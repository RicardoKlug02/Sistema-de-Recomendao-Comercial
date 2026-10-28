"""Importação transacional dos dois relatórios do ERP e de planilhas tabulares."""
import hashlib
import math
import re
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional
import pandas as pd
from sqlalchemy.orm import Session
from src.backend.app.core.security import gerar_blind_index
from src.backend.app.services.datas import hoje_comercial
from src.backend.app.models import Cliente, Fabrica, ItemVenda, Produto, Venda, Vendedor


def normalizar_coluna(valor):
    texto = unicodedata.normalize("NFKD", str(valor))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "_", texto.lower()).strip("_")


def texto(valor):
    return "" if pd.isna(valor) else str(valor).strip()


def identificador(valor):
    return re.sub(r"^([0-9]+)\.0+$", r"\1", texto(valor))


class ExcelService:
    def __init__(self, db_session: Session):
        self.db = db_session

    @staticmethod
    def normalizar_sku(sku_raw: Optional[str]) -> str:
        return re.sub(r"(?<=\d)[uU]$", "", identificador(sku_raw))

    def _anonimizar(self, valor: Any) -> str:
        # Compatibilidade com scripts antigos; a carga operacional conserva os nomes.
        return hashlib.sha256(texto(valor).encode()).hexdigest()[:14].upper()

    def _converter_valor_br(self, valor: Any) -> float:
        if pd.isna(valor) or valor is None or texto(valor) == "":
            raise ValueError("Valor numérico obrigatório não preenchido na planilha.")
        numero = texto(valor).replace("R$", "").replace("\u00a0", "").replace(" ", "")
        if "," in numero:
            numero = numero.replace(".", "").replace(",", ".")
        try:
            resultado = float(numero)
        except ValueError:
            raise ValueError("Valor numérico inválido na planilha.")
        if not math.isfinite(resultado):
            raise ValueError("Valor não finito na planilha.")
        return resultado

    @staticmethod
    def _mapear_colunas(df):
        aliases = {
            "pedido": ("pedido", "numero_do_pedido", "numero_pedido", "n_pedido"),
            "data": ("data", "data_emissao", "data_de_emissao", "data_do_pedido", "data_pedido"),
            "fabrica": ("fabrica", "representada", "industria", "fabricante"),
            "cliente": ("razao_social", "cliente", "nome_do_cliente"),
            "nome_fantasia": ("nome_fantasia", "fantasia"),
            "cnpj_cpf": ("cnpj_cpf", "cnpj", "cpf", "cpf_cnpj"),
            "vendedor": ("vendedor", "vendedor_a", "representante", "nome_vendedor"),
            "rede": ("rede", "rede_de_clientes", "grupo", "grupo_economico"),
            "tipo_pedido": ("tipo_pedido", "tipo_do_pedido", "tipo"),
            "cidade": ("cidade", "municipio"), "estado": ("estado", "uf"),
            "cep": ("cep",), "valor_total": ("valor_total", "total", "valor", "valor_do_pedido", "total_pedido", "total_em_produtos"),
            "sku": ("sku", "codigo", "codigo_produto", "codigo_do_produto", "cod_produto"),
            "nome_produto": ("produto", "nome_produto", "descricao", "descricao_produto"),
            "quantidade": ("quantidade", "qtd", "qtde"), "preco_unitario": ("preco_unitario", "preco", "valor_unitario"),
        }
        df.columns = [normalizar_coluna(c) for c in df.columns]
        rename = {}
        for destino, nomes in aliases.items():
            origem = next((c for c in nomes if c in df.columns), None)
            if origem:
                rename[origem] = destino
        return df.rename(columns=rename).loc[:, lambda x: ~x.columns.duplicated()]

    def _ler_tabela(self, arquivo):
        bruto = pd.read_excel(arquivo, header=None, dtype=str)
        for i, row in bruto.head(40).iterrows():
            cols = {normalizar_coluna(v) for v in row.dropna()}
            if cols.intersection({"pedido", "numero_pedido", "numero_do_pedido"}) and len(cols) >= 3:
                df = bruto.iloc[i + 1:].copy()
                df.columns = bruto.iloc[i].tolist()
                return self._mapear_colunas(df.dropna(how="all"))
        raise ValueError("Cabeçalho não encontrado. Use colunas Pedido, Data, Cliente, CNPJ/CPF, Fábrica e Valor Total.")

    def _limpar_excel_cabecalho(self, caminho_arquivo, permitir_vazio=False):
        df = self._ler_tabela(caminho_arquivo)
        obrigatorias = {"pedido", "data", "fabrica", "cnpj_cpf", "valor_total"}
        faltantes = obrigatorias - set(df.columns)
        if faltantes:
            raise ValueError("Colunas obrigatórias ausentes: " + ", ".join(sorted(faltantes)))
        if "cliente" not in df:
            if "nome_fantasia" not in df:
                raise ValueError("Informe a coluna Cliente ou Razão Social.")
            df["cliente"] = df["nome_fantasia"]
        df = df.dropna(subset=["pedido"]).copy()
        df["pedido"] = df["pedido"].map(identificador)
        df = df[df["pedido"] != ""]
        if df.empty and not permitir_vazio:
            raise ValueError("A planilha de pedidos está vazia.")
        df["valor_total"] = df["valor_total"].map(self._converter_valor_br)
        return df.reset_index(drop=True)

    def _limpar_excel_produtos(self, caminho_arquivo):
        bruto = pd.read_excel(caminho_arquivo, header=None, dtype=str)
        colunas = ["sku", "nome_produto", "pedido", "preco_unitario", "quantidade"]
        if bruto.empty:
            return pd.DataFrame(columns=colunas)
        if not bruto[0].fillna("").str.strip().str.startswith("Produto:").any():
            df = self._ler_tabela(caminho_arquivo)
            faltantes = set(colunas) - set(df.columns)
            if faltantes:
                raise ValueError("Colunas de itens ausentes: " + ", ".join(sorted(faltantes)))
            df = df.dropna(subset=["pedido", "sku"]).copy()
            df["pedido"] = df["pedido"].map(identificador)
            df["sku"] = df["sku"].map(self.normalizar_sku)
            for c in ("preco_unitario", "quantidade"):
                df[c] = df[c].map(self._converter_valor_br)
            return df
        itens, sku, nome = [], None, None
        for _, row in bruto.iterrows():
            inicio = texto(row.iloc[0])
            if inicio.startswith("Produto:"):
                descricao = inicio.removeprefix("Produto:").strip()
                partes = re.split(r"\s+-\s+", descricao, maxsplit=1)
                if len(partes) != 2:
                    partes = re.split(r"\s*-\s*", descricao, maxsplit=1)
                sku = self.normalizar_sku(partes[0])
                nome = partes[1] if len(partes) == 2 else descricao
                continue
            if len(row) < 6 or inicio.startswith(("Data", "Filtros", "Relatório", "Total")):
                continue
            # O ERP inclui totalizadores com contagem na coluna Pedido.
            # Não são itens: não têm data, cliente, criador nem preço unitário.
            if not inicio and all(pd.isna(row.iloc[i]) for i in (2, 3, 4)):
                continue
            pedido = identificador(row.iloc[1])
            if not sku or not re.fullmatch(r"[0-9]+", pedido):
                continue
            itens.append({"sku": sku, "nome_produto": nome, "pedido": pedido,
                          "preco_unitario": self._converter_valor_br(row.iloc[4]),
                          "quantidade": self._converter_valor_br(row.iloc[5])})
        return pd.DataFrame(itens, columns=colunas)

    def importar_processo_completo(self, path_cab: str, path_itens: str) -> Dict[str, Any]:
        try:
            resultado = self._validar_e_salvar(
                self._limpar_excel_cabecalho(path_cab), self._limpar_excel_produtos(path_itens), commit=False)
            self.db.commit()
            return {"status": "sucesso", **resultado}
        except ValueError as exc:
            self.db.rollback()
            return {"status": "erro", "mensagem": str(exc), "tipo": "validacao"}
        except Exception:
            self.db.rollback()
            raise

    @staticmethod
    def _periodo_sincronizacao(modo, mes):
        if modo == "atualizar":
            if mes:
                raise ValueError("Informe um mês somente no modo Sincronizar mês completo.")
            return None
        if modo != "sincronizar_mes" or not re.fullmatch(r"\d{4}-\d{2}", mes or ""):
            raise ValueError("Selecione o modo de importação e um mês válido (AAAA-MM).")
        try:
            inicio = date.fromisoformat(f"{mes}-01")
            fim = date(inicio.year + (inicio.month == 12), inicio.month % 12 + 1, 1)
        except ValueError:
            raise ValueError("Informe um mês válido para sincronizar.")
        if inicio > hoje_comercial():
            raise ValueError("Não é possível sincronizar um mês futuro.")
        return inicio, fim

    def _preparar_carga(self, df_cab, df_prod, modo="atualizar", mes=None):
        periodo = self._periodo_sincronizacao(modo, mes)
        if df_cab.empty and not periodo:
            raise ValueError("A planilha de pedidos está vazia.")
        # Valida toda a carga antes de qualquer substituição dos itens.
        chaves = set()
        pedidos_fabricas = {}
        cabecalhos = []
        hoje = hoje_comercial()
        for linha, row in df_cab.iterrows():
            pedido = identificador(row["pedido"])
            if "tipo_pedido" in row and normalizar_coluna(row["tipo_pedido"]) not in {"venda", "pedido_de_venda"}:
                raise ValueError(f"Pedido {pedido}: somente pedidos do tipo Venda são permitidos. Confira o filtro do relatório.")
            fabrica = texto(row.get("fabrica"))
            doc = re.sub(r"\D", "", texto(row.get("cnpj_cpf")))
            if not pedido or not fabrica or len(doc) not in (11, 14):
                raise ValueError(f"Pedido na linha {linha + 1}: informe número, fábrica e CNPJ/CPF com 11 ou 14 dígitos.")
            chave = (fabrica.casefold(), pedido)
            if chave in chaves:
                raise ValueError(f"Pedido {pedido} duplicado na mesma fábrica.")
            chaves.add(chave)
            pedidos_fabricas.setdefault(pedido, set()).add(fabrica.casefold())
            try:
                valor_data = row.get("data")
                if re.match(r"^\d{4}-\d{2}-\d{2}", str(valor_data)):
                    data = pd.to_datetime(valor_data, format="ISO8601", errors="raise")
                else:
                    data = pd.to_datetime(valor_data, dayfirst=True, errors="raise")
                if pd.isna(data):
                    raise ValueError()
                data = data.date()
            except (ValueError, TypeError):
                raise ValueError(f"Pedido {pedido}: data inválida.")
            if data > hoje:
                raise ValueError(f"Pedido {pedido}, fábrica {fabrica}, linha {linha + 1}: data de emissão "
                                 f"{data:%d/%m/%Y} posterior a hoje ({hoje:%d/%m/%Y}). "
                                 "Corrija a planilha e confira novamente. Nenhum pedido desta carga foi importado.")
            if periodo and not periodo[0] <= data < periodo[1]:
                raise ValueError(f"Pedido {pedido}: a data está fora do mês {mes}. Nenhuma alteração foi salva.")
            valor = self._converter_valor_br(row.get("valor_total"))
            if valor < 0:
                raise ValueError(f"Pedido {pedido}: valor total negativo.")
            cabecalhos.append((row, pedido, fabrica, doc, data, valor))
        grupos, ignorados = {}, 0
        for _, item in df_prod.iterrows():
            pedido = identificador(item["pedido"])
            fabricas = pedidos_fabricas.get(pedido)
            if not fabricas:
                ignorados += 1
                continue
            fabrica_item = texto(item.get("fabrica")).casefold()
            if len(fabricas) > 1 and not fabrica_item:
                raise ValueError(f"Pedido {pedido}: número repetido entre fábricas. Informe a fábrica na planilha de itens.")
            fabrica_item = fabrica_item or next(iter(fabricas))
            if fabrica_item not in fabricas:
                raise ValueError(f"Pedido {pedido}: fábrica do item difere do cabeçalho.")
            qtd = self._converter_valor_br(item["quantidade"])
            preco = self._converter_valor_br(item["preco_unitario"])
            sku = self.normalizar_sku(item["sku"])
            if not sku or qtd <= 0 or qtd != int(qtd) or preco < 0:
                raise ValueError(f"Pedido {pedido}: SKU, quantidade inteira positiva ou preço inválido.")
            grupos.setdefault((fabrica_item, pedido), []).append((sku, texto(item["nome_produto"]) or sku, int(qtd), preco))
        if periodo and ignorados:
            raise ValueError("A sincronização mensal exige itens com cabeçalhos correspondentes. "
                             "Confira se as duas planilhas são completas e do mesmo mês.")
        return cabecalhos, grupos, ignorados

    def _pedidos_ausentes(self, cabecalhos, modo, mes):
        periodo = self._periodo_sincronizacao(modo, mes)
        if not periodo:
            return []
        chaves = {(c[2].casefold(), c[1]) for c in cabecalhos}
        return [v for v, fabrica in self.db.query(Venda, Fabrica.nome_fantasia)
                .join(Fabrica, Fabrica.id == Venda.fabrica_id)
                .filter(Venda.data_venda >= periodo[0], Venda.data_venda < periodo[1]).all()
                if (fabrica.casefold(), v.numero_pedido) not in chaves]

    def conferir(self, df_cab, df_prod, modo="atualizar", mes=None):
        cabecalhos, grupos, ignorados = self._preparar_carga(df_cab, df_prod, modo, mes)
        fabricas = {f.id: f.nome_fantasia.casefold() for f in self.db.query(Fabrica).all()}
        numeros = {c[1] for c in cabecalhos}
        existentes = {(fabricas[v.fabrica_id], v.numero_pedido): v for v in
                      self.db.query(Venda).filter(Venda.numero_pedido.in_(numeros)).all()}
        itens_anteriores = {}
        ausentes = self._pedidos_ausentes(cabecalhos, modo, mes)
        ids = [v.id for v in existentes.values()] + [v.id for v in ausentes]
        for item in self.db.query(ItemVenda).filter(ItemVenda.venda_id.in_(ids)).order_by(ItemVenda.id):
            itens_anteriores.setdefault(item.venda_id, []).append(item)
        registros, estado = [], []
        atualizados = sem_itens = total_itens = removidos = reduzidos = 0
        produtos = {p.id: p.sku for p in self.db.query(Produto).all()}
        def registrar_estado(venda):
            anteriores = itens_anteriores.get(venda.id, [])
            estado.append([venda.id, venda.cliente_id, venda.vendedor_id, str(venda.data_venda), venda.valor_total,
                           [[i.id, i.produto_id, i.quantidade, i.preco_unitario] for i in anteriores]])
        por_fabrica = {}
        for row, pedido, fabrica, _, data, valor in cabecalhos:
            chave = (fabrica.casefold(), pedido)
            venda = existentes.get(chave)
            itens = grupos.get(chave, [])
            atualizados += venda is not None
            sem_itens += not itens
            total_itens += len(itens)
            por_fabrica[fabrica] = por_fabrica.get(fabrica, 0) + valor
            if venda:
                anteriores = itens_anteriores.get(venda.id, [])
                registrar_estado(venda)
                if itens or modo == "sincronizar_mes":
                    novos = {}
                    antigos = {}
                    for sku, _, qtd, _ in itens:
                        novos[sku] = novos.get(sku, 0) + qtd
                    for i in anteriores:
                        sku = produtos[i.produto_id]
                        antigos[sku] = antigos.get(sku, 0) + i.quantidade
                        removidos += sku not in novos
                    reduzidos += sum(sku in novos and novos[sku] < qtd for sku, qtd in antigos.items())
            registros.append({"pedido": pedido, "fabrica": fabrica, "cliente": texto(row.get("cliente")),
                              "data": data.isoformat(), "valor": valor, "itens": len(itens),
                              "acao": "Atualizar" if venda else "Adicionar"})
        excluidos = []
        for venda in ausentes:
            registrar_estado(venda)
            anteriores = itens_anteriores.get(venda.id, [])
            removidos += len(anteriores)
            excluidos.append({"pedido": venda.numero_pedido, "fabrica": fabricas[venda.fabrica_id],
                              "data": venda.data_venda.isoformat(), "valor": venda.valor_total,
                              "itens": len(anteriores), "acao": "Excluir"})
        from src.backend.app.models import Importacao
        ultima = self.db.query(Importacao.id).order_by(Importacao.id.desc()).first()
        import json
        assinatura = hashlib.sha256(json.dumps([sorted(estado), ultima[0] if ultima else 0], sort_keys=True).encode()).hexdigest()
        avisos = []
        if ignorados:
            avisos.append(f"{ignorados} linhas de itens sem pedido correspondente serão ignoradas. Confira o período dos arquivos.")
        if sem_itens and modo == "atualizar":
            avisos.append(f"{sem_itens} pedidos sem itens nesta carga: entram no faturamento. Itens anteriormente importados serão conservados.")
        if atualizados:
            avisos.append("Pedidos existentes serão atualizados, sem duplicação. Quando houver itens na carga, eles substituirão os itens anteriores do pedido.")
        if modo == "sincronizar_mes":
            avisos.append(f"Sincronização de {mes}: os arquivos devem conter todas as vendas do mês, "
                          "de todos os vendedores e fábricas. Pedidos ausentes serão excluídos e os itens dos pedidos "
                          "informados serão substituídos, inclusive quando a nova lista estiver vazia. Outros meses serão preservados.")
        if "tipo_pedido" not in df_cab:
            avisos.append("O arquivo não informa o tipo do pedido. Confirme que contém somente vendas efetivadas que geram comissão.")
        datas = [c[4] for c in cabecalhos]
        periodo = self._periodo_sincronizacao(modo, mes)
        return {"modo": modo, "mes": mes, "excluidos": len(ausentes), "itens_removidos": removidos,
                "quantidades_reduzidas": reduzidos, "pedidos_excluidos": excluidos[:100],
                "valor_excluido": round(sum(v.valor_total for v in ausentes), 2),
                "processados": len(cabecalhos), "adicionados": len(cabecalhos) - atualizados,
                "atualizados": atualizados, "itens": total_itens, "pedidos_sem_itens": sem_itens,
                "itens_ignorados": ignorados, "valor_total": round(sum(c[5] for c in cabecalhos), 2),
                "inicio": (min(datas) if datas else periodo[0]).isoformat(),
                "fim": (max(datas) if datas else date.fromordinal(periodo[1].toordinal() - 1)).isoformat(), "avisos": avisos,
                "fabricas": [{"nome": f, "valor": round(v, 2)} for f, v in por_fabrica.items()],
                "pedidos": registros[:100], "estado": assinatura}

    def _validar_e_salvar(self, df_cab, df_prod, commit=True, modo="atualizar", mes=None):
        cabecalhos, grupos, ignorados = self._preparar_carga(df_cab, df_prod, modo, mes)
        if self.db.bind.dialect.name == "postgresql":
            from sqlalchemy import text
            if not self.db.execute(text("SELECT pg_try_advisory_xact_lock(20260929)")).scalar():
                raise ValueError("Outra importação está em andamento. Aguarde a conclusão antes de enviar novamente.")
        ausentes = self._pedidos_ausentes(cabecalhos, modo, mes)
        fabricas_cache = {f.nome_fantasia.casefold(): f for f in self.db.query(Fabrica).all()}
        vendedores = {v.nome.casefold(): v for v in self.db.query(Vendedor).all()}
        clientes = {c.cnpj_hash: c for c in self.db.query(Cliente).all() if c.cnpj_hash}
        # Prepara cadastros em lote; não faz uma viagem ao banco por pedido.
        for row, _, nome_fabrica, doc, _, _ in cabecalhos:
            if nome_fabrica.casefold() not in fabricas_cache:
                fabrica = Fabrica(nome_fantasia=nome_fabrica)
                self.db.add(fabrica)
                fabricas_cache[nome_fabrica.casefold()] = fabrica
            vend_nome = texto(row.get("vendedor"))
            if vend_nome and vend_nome.casefold() not in vendedores:
                vendedor = Vendedor(nome=vend_nome)
                self.db.add(vendedor)
                vendedores[vend_nome.casefold()] = vendedor
            doc_hash = gerar_blind_index(doc)
            if doc_hash not in clientes:
                cliente = Cliente(cnpj_cpf=doc, cnpj_hash=doc_hash, razao_social=texto(row.get("cliente")) or doc)
                self.db.add(cliente)
                clientes[doc_hash] = cliente
            cliente = clientes[doc_hash]
            cliente.razao_social = texto(row.get("cliente")) or cliente.razao_social
            local_anterior = (cliente.cidade, cliente.estado)
            for campo, origem in (("nome_fantasia", "nome_fantasia"), ("cidade", "cidade"),
                                  ("estado", "estado"), ("cep", "cep"), ("grupo_economico", "rede")):
                if texto(row.get(origem)):
                    setattr(cliente, campo, texto(row.get(origem)))
            if cliente.estado:
                cliente.estado = cliente.estado.upper()
            if cliente.cidade and cliente.estado and (not cliente.micro_regiao or local_anterior != (cliente.cidade, cliente.estado)):
                from src.backend.app.services.ibge_service import IBGEService
                cliente.micro_regiao = IBGEService.obter_regiao_imediata(cliente.cidade, cliente.estado)
        self.db.flush()
        produtos = {(p.fabrica_id, p.sku): p for p in self.db.query(Produto).all()}
        for (nome_fabrica, _), lista in grupos.items():
            fid = fabricas_cache[nome_fabrica].id
            for sku, nome, _, _ in lista:
                if (fid, sku) not in produtos:
                    produto = Produto(sku=sku, nome=nome, fabrica_id=fid)
                    self.db.add(produto)
                    produtos[(fid, sku)] = produto
        self.db.flush()
        numeros = {c[1] for c in cabecalhos}
        vendas = {(v.fabrica_id, v.numero_pedido): v for v in self.db.query(Venda).filter(Venda.numero_pedido.in_(numeros)).all()}
        adicionados = atualizados = sem_itens = 0
        cargas = []
        for row, pedido, nome_fabrica, doc, data, valor in cabecalhos:
            fabrica = fabricas_cache[nome_fabrica.casefold()]
            cliente = clientes[gerar_blind_index(doc)]
            vendedor = vendedores.get(texto(row.get("vendedor")).casefold())
            venda = vendas.get((fabrica.id, pedido))
            if venda is None:
                venda = Venda(numero_pedido=pedido, fabrica_id=fabrica.id)
                self.db.add(venda)
                vendas[(fabrica.id, pedido)] = venda
                adicionados += 1
            else:
                atualizados += 1
            venda.cliente_id, venda.data_venda, venda.valor_total = cliente.id, data, valor
            venda.vendedor_id = vendedor.id if vendedor else None
            lista = grupos.get((nome_fabrica.casefold(), pedido), [])
            if lista or modo == "sincronizar_mes":
                cargas.append((venda, lista))
            if not lista:
                sem_itens += 1
        self.db.flush()
        # No modo mensal, também remove pedidos ausentes e listas que ficaram vazias.
        ids = [v.id for v, _ in cargas] + [v.id for v in ausentes]
        if ids:
            self.db.query(ItemVenda).filter(ItemVenda.venda_id.in_(ids)).delete(synchronize_session=False)
        if ausentes:
            self.db.query(Venda).filter(Venda.id.in_([v.id for v in ausentes])).delete(synchronize_session=False)
        itens_salvos = 0
        for venda, lista in cargas:
            for sku, _, quantidade, preco in lista:
                self.db.add(ItemVenda(venda_id=venda.id, produto_id=produtos[(venda.fabrica_id, sku)].id,
                                      quantidade=quantidade, preco_unitario=preco))
                itens_salvos += 1
        avisos = []
        if ignorados:
            avisos.append(f"{ignorados} linhas de itens sem cabeçalho correspondente não foram importadas. Confira os filtros dos relatórios.")
        if sem_itens:
            avisos.append(f"{sem_itens} pedidos sem itens na carga: mantidos no faturamento. As análises de mix utilizam somente itens conhecidos.")
        if modo == "sincronizar_mes":
            avisos.append(f"Mês {mes} sincronizado: {len(ausentes)} pedidos ausentes excluídos. Outros meses preservados.")
        if commit:
            self.db.commit()
        else:
            self.db.flush()
        return {"mensagem": "Importação concluída.", "processados": len(cabecalhos),
                "modo": modo, "mes": mes, "excluidos": len(ausentes),
                "adicionados": adicionados, "atualizados": atualizados, "itens": itens_salvos,
                "pedidos_sem_itens": sem_itens, "itens_ignorados": ignorados, "avisos": avisos}
    @staticmethod
    def sanitizar_valor_planilha(valor):
        return texto(valor) if isinstance(valor, str) else valor
