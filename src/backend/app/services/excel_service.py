"""Importação atômica: valida e concilia todo o lote antes de persistir."""

from collections import Counter
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re
import unicodedata
import zipfile
import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from src.backend.app.core.security import gerar_blind_index
from src.backend.app.models import Cliente, Fabrica, ItemVenda, Produto, Venda, Vendedor


class ErroImportacao(ValueError):
    pass


class ExcelService:
    MAX_LINHAS = 50000

    def __init__(self, db_session):
        self.db = db_session

    @staticmethod
    def normalizar_sku(valor):
        # SKU é identidade do ERP: não remover sufixos de embalagem.
        return str(valor).strip() if valor is not None else ""

    @staticmethod
    def _texto(valor):
        return "" if valor is None or pd.isna(valor) else str(valor).strip()

    @staticmethod
    def _chave(valor):
        texto = (
            unicodedata.normalize("NFKD", str(valor))
            .encode("ascii", "ignore")
            .decode()
            .lower()
        )
        return re.sub(r"[^a-z0-9]+", "_", texto).strip("_")

    @staticmethod
    def _numero(valor):
        if valor is None or pd.isna(valor) or str(valor).strip() == "":
            raise ErroImportacao("Valor numérico ausente.")
        s = str(valor).replace("R$", "").replace("\xa0", "").replace(" ", "").strip()
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        try:
            n = Decimal(s)
        except InvalidOperation:
            raise ErroImportacao(f"Valor numérico inválido: {s[:40]}.")
        if not n.is_finite():
            raise ErroImportacao("Valor numérico não finito.")
        return n

    def _converter_valor_br(self, valor):
        return self._numero(valor)

    @staticmethod
    def _pedido(valor):
        s = ExcelService._texto(valor)
        if re.fullmatch(r"\d+\.0", s):
            s = s[:-2]
        return s

    def _ler(self, caminho):
        # Não confiar na extensão: detectar assinatura e limitar expansão XLSX.
        with open(caminho, "rb") as arq:
            assinatura = arq.read(8)
        if assinatura.startswith(b"PK"):
            try:
                with zipfile.ZipFile(caminho) as pacote:
                    if sum(i.file_size for i in pacote.infolist()) > 80 * 1024 * 1024:
                        raise ErroImportacao(
                            "Planilha excede o limite de 80 MB descompactados."
                        )
            except zipfile.BadZipFile:
                raise ErroImportacao("Arquivo XLSX inválido.")
            engine = "openpyxl"
        elif assinatura == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
            engine = "xlrd"
        else:
<<<<<<< Updated upstream
            df["valor_total"] = 0.0

        df = df.map(self.sanitizar_valor_planilha)

=======
            raise ErroImportacao("O conteúdo não é uma planilha XLS/XLSX válida.")
        try:
            df = pd.read_excel(
                caminho,
                header=None,
                dtype=object,
                engine=engine,
                nrows=self.MAX_LINHAS + 50,
            )
        except ErroImportacao:
            raise
        except Exception:
            raise ErroImportacao(
                "Não foi possível ler a planilha. Verifique se está íntegra e sem senha."
            )
        if len(df) > self.MAX_LINHAS:
            raise ErroImportacao(f"Limite de {self.MAX_LINHAS} linhas excedido.")
        if df.empty:
            raise ErroImportacao("A planilha está vazia.")
>>>>>>> Stashed changes
        return df

    ALIASES = {
        "pedido": {
            "pedido",
            "numero_pedido",
            "n_pedido",
            "no_pedido",
            "numero_do_pedido",
        },
        "cnpj_cpf": {"cnpj", "cpf", "cnpj_cpf", "cpf_cnpj"},
        "cliente": {"cliente", "razao_social", "nome_cliente", "nome_do_cliente"},
        "fabrica": {"fabrica", "industria", "fornecedor", "representada"},
        "valor_total": {
            "valor_total",
            "total",
            "total_pedido",
            "valor_do_pedido",
            "valor",
            "total_em_produtos",
        },
        "data": {
            "data",
            "data_venda",
            "data_pedido",
            "emissao",
            "data_emissao",
            "data_de_emissao",
        },
        "vendedor": {"vendedor", "vendedor_a", "representante"},
        "rede": {"rede", "grupo", "grupo_economico", "rede_de_clientes"},
        "cidade": {"cidade", "municipio"},
        "estado": {"estado", "uf"},
        "micro_regiao": {"micro_regiao", "microrregiao", "regiao"},
        "sku": {"sku", "codigo", "codigo_produto", "cod_produto"},
        "nome_produto": {"produto", "nome_produto", "descricao", "descricao_produto"},
        "quantidade": {"quantidade", "qtd", "qtde"},
        "preco_unitario": {"preco_unitario", "valor_unitario", "preco", "unitario"},
        "subtotal": {"subtotal", "total_item", "valor_item"},
        "categoria": {"categoria", "linha"},
    }

    def _tabular(self, bruto, obrigatorias):
        for indice, linha in bruto.head(30).iterrows():
            mapeamento = {}
            for col, valor in linha.items():
                chave = self._chave(valor)
                for destino, aliases in self.ALIASES.items():
                    if chave in aliases and destino not in mapeamento.values():
                        mapeamento[col] = destino
                        break
            if obrigatorias <= set(mapeamento.values()):
                dados = (
                    bruto.loc[indice + 1 :, list(mapeamento)]
                    .rename(columns=mapeamento)
                    .copy()
                )
                dados["_linha"] = dados.index + 1
                return dados.dropna(how="all", subset=list(mapeamento.values()))
        return None

    def _limpar_excel_cabecalho(self, caminho):
        df = self._tabular(
            self._ler(caminho),
            {"pedido", "cnpj_cpf", "cliente", "fabrica", "data", "valor_total"},
        )
        if df is None:
            raise ErroImportacao(
                "Pedidos: cabeçalho obrigatório não encontrado (pedido, CNPJ/CPF, cliente, fábrica, data, valor total)."
            )
        # Apenas rodapés explicitamente identificados são ignorados.
        return df[~df["pedido"].map(self._texto).str.lower().str.startswith("total")]

    def _limpar_excel_produtos(self, caminho):
        bruto = self._ler(caminho)
        df = self._tabular(
            bruto, {"pedido", "sku", "nome_produto", "quantidade", "preco_unitario"}
        )
        if df is not None:
            return df[
                ~df["pedido"].map(self._texto).str.lower().str.startswith("total")
            ]
        # Relatório legado: blocos "Produto: SKU - Nome" seguidos dos pedidos.
        itens, sku, nome = [], "", ""
        for indice, row in bruto.iterrows():
            c0 = self._texto(row.iloc[0])
            if c0.startswith("Produto:"):
                partes = c0.removeprefix("Produto:").strip().split(" - ", 1)
                if len(partes) != 2:
                    raise ErroImportacao(
                        f"Itens, linha {indice + 1}: seção de produto inválida."
                    )
                sku, nome = partes
                continue
            if not sku or c0.startswith(("Data", "Filtros", "Relatório", "Total")):
                continue
            # Rodapé do ERP: contagem de pedidos e totais, sem data, cliente ou preço.
            if (
                not c0
                and len(row) >= 7
                and all(pd.isna(row.iloc[i]) for i in [2, 3, 4])
            ):
                continue
            pedido = self._pedido(row.iloc[1]) if len(row) > 1 else ""
            if not pedido:
                continue
            if not pedido.isdigit():
                raise ErroImportacao(f"Itens, linha {indice + 1}: pedido inválido.")
            if len(row) < 7:
                raise ErroImportacao(f"Itens, linha {indice + 1}: colunas incompletas.")
            itens.append(
                dict(
                    pedido=pedido,
                    sku=sku,
                    nome_produto=nome,
                    preco_unitario=row.iloc[4],
                    quantidade=row.iloc[5],
                    subtotal=row.iloc[6],
                    _linha=indice + 1,
                )
            )
        if not itens:
            raise ErroImportacao("Nenhum item reconhecido na planilha de produtos.")
        return pd.DataFrame(itens)

    def _validar(self, cab, prod):
        pedidos, itens = {}, {}
        for _, row in cab.iterrows():
            linha = row.get("_linha", "?")
            try:
                pedido = self._pedido(row.get("pedido"))
                if not pedido or len(pedido) > 50:
                    raise ErroImportacao("Número de pedido ausente ou muito longo.")
                if pedido in pedidos:
                    raise ErroImportacao(f"Pedido {pedido} duplicado no cabeçalho.")
                documento = re.sub(r"\D", "", self._texto(row.get("cnpj_cpf")))
                if len(documento) not in (11, 14):
                    raise ErroImportacao(
                        "CNPJ/CPF deve ter 11 ou 14 dígitos, preservando zeros à esquerda."
                    )
                nome, fabrica = (
                    self._texto(row.get("cliente")),
                    self._texto(row.get("fabrica")),
                )
                if not nome or not fabrica:
                    raise ErroImportacao("Cliente e fábrica são obrigatórios.")
                if len(nome.encode()) > 300 or len(fabrica) > 100:
                    raise ErroImportacao("Nome de cliente ou fábrica excede o limite.")
                raw = row.get("data")
                if isinstance(raw, (int, float)) or not self._texto(raw):
                    raise ErroImportacao("Data ausente ou numérica sem formatação.")
                try:
                    if isinstance(raw, (date, datetime)):
                        data_venda = raw.date() if isinstance(raw, datetime) else raw
                    else:
                        s = str(raw).strip()
                        data_venda = datetime.strptime(
                            s,
                            "%Y-%m-%d"
                            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s)
                            else "%d/%m/%Y",
                        ).date()
                except (ValueError, TypeError):
                    raise ErroImportacao(
                        "Data inválida; utilize DD/MM/AAAA ou AAAA-MM-DD."
                    )
                if data_venda > date.today():
                    raise ErroImportacao("Data de venda futura não permitida.")
                total = self._numero(row.get("valor_total"))
                if total <= 0 or total >= Decimal("100000000000000"):
                    raise ErroImportacao("Total do pedido fora do intervalo permitido.")
                if total != total.quantize(Decimal(".01")):
                    raise ErroImportacao(
                        "Total do pedido deve ter até duas casas decimais."
                    )
                dados = {
                    c: self._texto(row.get(c))
                    for c in ["vendedor", "rede", "cidade", "estado", "micro_regiao"]
                }
                for c, limite in [
                    ("vendedor", 100),
                    ("rede", 100),
                    ("cidade", 100),
                    ("estado", 2),
                    ("micro_regiao", 50),
                ]:
                    if len(dados[c]) > limite:
                        raise ErroImportacao(f"{c} excede {limite} caracteres.")
                pedidos[pedido] = dict(
                    pedido=pedido,
                    documento=documento,
                    hash=gerar_blind_index(documento),
                    nome=nome,
                    fabrica=fabrica,
                    data=data_venda,
                    total=total,
                    **dados,
                )
            except ErroImportacao as e:
                raise ErroImportacao(f"Pedidos, linha {linha}: {e}")
        if not pedidos:
            raise ErroImportacao("Nenhum pedido encontrado.")
        duplicados = set()
        for _, row in prod.iterrows():
            linha = row.get("_linha", "?")
            try:
                pedido = self._pedido(row.get("pedido"))
                if pedido not in pedidos:
                    raise ErroImportacao(
                        f"Item sem cabeçalho correspondente: pedido {pedido}."
                    )
                sku, nome = (
                    self.normalizar_sku(self._texto(row.get("sku"))),
                    self._texto(row.get("nome_produto")),
                )
                if not sku or not nome:
                    raise ErroImportacao("SKU e nome são obrigatórios.")
                categoria = self._texto(row.get("categoria"))
                if len(sku) > 150 or len(nome) > 255 or len(categoria) > 100:
                    raise ErroImportacao("SKU, nome ou categoria excede o limite.")
                qtd, preco = (
                    self._numero(row.get("quantidade")),
                    self._numero(row.get("preco_unitario")),
                )
                if qtd <= 0 or qtd != qtd.to_integral_value() or qtd > 2147483647:
                    raise ErroImportacao(
                        "Quantidade deve ser inteira e positiva; frações não são suportadas."
                    )
                if (
                    preco <= 0
                    or preco >= Decimal("100000000000000")
                    or preco != preco.quantize(Decimal(".01"))
                ):
                    raise ErroImportacao(
                        "Preço deve ser positivo e ter até duas casas decimais."
                    )
                subtotal = (qtd * preco).quantize(
                    Decimal(".01"), rounding=ROUND_HALF_UP
                )
                if self._texto(row.get("subtotal")):
                    declarado = self._numero(row["subtotal"])
                    # ERP exibe preço arredondado a centavos. Preservar subtotal oficial,
                    # aceitando somente a diferença matematicamente possível desse arredondamento.
                    tolerancia = qtd * Decimal(".005") + Decimal(".005")
                    if (
                        declarado <= 0
                        or declarado != declarado.quantize(Decimal(".01"))
                        or abs(declarado - subtotal) > tolerancia
                    ):
                        raise ErroImportacao(
                            "Subtotal diverge de quantidade × preço além da tolerância de arredondamento."
                        )
                    subtotal = declarado
                chave = (pedido, sku, qtd, preco)
                if chave in duplicados:
                    raise ErroImportacao(
                        f"Item duplicado no pedido {pedido}, SKU {sku}."
                    )
                duplicados.add(chave)
                itens.setdefault(pedido, []).append(
                    dict(
                        sku=sku,
                        nome=nome,
                        quantidade=int(qtd),
                        preco=preco,
                        subtotal=subtotal,
                        categoria=categoria,
                    )
                )
            except ErroImportacao as e:
                raise ErroImportacao(f"Itens, linha {linha}: {e}")
        for pedido, p in pedidos.items():
            if pedido not in itens:
                raise ErroImportacao(
                    f"Pedido {pedido} sem itens. Nenhum dado foi alterado."
                )
            soma = sum((i["subtotal"] for i in itens[pedido]), Decimal(0))
            if abs(soma - p["total"]) > Decimal(".01"):
                raise ErroImportacao(
                    f"Pedido {pedido}: soma dos itens ({soma}) diverge do total ({p['total']}). Verifique descontos, frete ou itens faltantes."
                )
        return pedidos, itens

    def importar_processo_completo(
        self, path_cab, path_itens, permitir_atualizacao=False, commit=True
    ):
        try:
            pedidos, itens = self._validar(
                self._limpar_excel_cabecalho(path_cab),
                self._limpar_excel_produtos(path_itens),
            )
            resultado = self._salvar(pedidos, itens, permitir_atualizacao)
            if commit:
                self.db.commit()
            return resultado
        except ErroImportacao as e:
            self.db.rollback()
            return {"status": "erro", "mensagem": str(e)}
        except SQLAlchemyError:
            self.db.rollback()
            return {
                "status": "erro",
                "mensagem": "Conflito ou falha no banco. Nenhum dado da carga foi alterado. Verifique a configuração e tente novamente.",
            }

    def _salvar(self, pedidos, itens, permitir_atualizacao):
        if self.db.bind.dialect.name == "postgresql":
            # Serializa cargas, inclusive inserts ainda sem linhas bloqueáveis.
            self.db.execute(text("SELECT pg_advisory_xact_lock(735291)"))
        fabricas = {}
        for f in self.db.query(Fabrica).all():
            chave = f.nome_fantasia.casefold()
            if chave in fabricas:
                raise ErroImportacao(
                    "Há fábricas com nomes duplicados na base; revise o cadastro."
                )
            fabricas[chave] = f
        if self.db.query(Cliente).filter(Cliente.cnpj_hash.is_(None)).first():
            raise ErroImportacao(
                "Existem clientes legados sem índice de documento. Reconcilie a base antes de importar para evitar duplicidades."
            )
        clientes = {c.cnpj_hash: c for c in self.db.query(Cliente).all() if c.cnpj_hash}
        vendedores = {v.nome.casefold(): v for v in self.db.query(Vendedor).all()}
        produtos = {p.sku: p for p in self.db.query(Produto).all()}
        vendas = {
            v.numero_pedido: v
            for v in self.db.query(Venda).filter(Venda.numero_pedido.in_(pedidos)).all()
        }
        contagem = dict(
            adicionados=0,
            atualizados=0,
            inalterados=0,
            itens=sum(len(v) for v in itens.values()),
        )
        for num, p in pedidos.items():
            fabrica = fabricas.get(p["fabrica"].casefold())
            if not fabrica:
                fabrica = Fabrica(nome_fantasia=p["fabrica"])
                self.db.add(fabrica)
                self.db.flush()
                fabricas[p["fabrica"].casefold()] = fabrica
            cliente = clientes.get(p["hash"])
            if not cliente:
                cliente = Cliente(
                    cnpj_cpf=p["documento"],
                    cnpj_hash=p["hash"],
                    razao_social=p["nome"],
                    nome_fantasia=p["nome"],
                )
                self.db.add(cliente)
                self.db.flush()
                clientes[p["hash"]] = cliente
            # Nunca apagar metadados quando a planilha omite campos opcionais.
            for fonte, destino in [
                ("rede", "grupo_economico"),
                ("cidade", "cidade"),
                ("estado", "estado"),
                ("micro_regiao", "micro_regiao"),
            ]:
                if p[fonte]:
                    setattr(cliente, destino, p[fonte])
            vendedor = None
            if p["vendedor"]:
                chave = p["vendedor"].casefold()
                vendedor = vendedores.get(chave)
                if not vendedor:
                    vendedor = Vendedor(nome=p["vendedor"])
                    self.db.add(vendedor)
                    self.db.flush()
                    vendedores[chave] = vendedor
            novos_itens = []
            for i in itens[num]:
                produto = produtos.get(i["sku"])
                if produto and produto.fabrica_id != fabrica.id:
                    raise ErroImportacao(
                        f"SKU {i['sku']} já pertence a outra fábrica. Revise a identidade do produto."
                    )
                if not produto:
                    produto = Produto(
                        sku=i["sku"],
                        nome=i["nome"],
                        fabrica_id=fabrica.id,
                        categoria=i["categoria"] or None,
                    )
                    self.db.add(produto)
                    self.db.flush()
                    produtos[i["sku"]] = produto
                elif i["categoria"]:
                    produto.categoria = i["categoria"]
                novos_itens.append(
                    (produto.id, i["quantidade"], i["preco"], i["subtotal"])
                )
            venda = vendas.get(num)
            if venda:
                if venda.cliente_id != cliente.id or venda.fabrica_id != fabrica.id:
                    raise ErroImportacao(
                        f"Pedido {num} já existe para outro cliente ou fábrica. A carga não substituirá sua identidade."
                    )
                existentes = Counter(
                    (
                        i.produto_id,
                        i.quantidade,
                        Decimal(i.preco_unitario),
                        Decimal(i.subtotal),
                    )
                    for i in venda.itens
                )
                iguais = (
                    existentes == Counter(novos_itens)
                    and venda.data_venda == p["data"]
                    and venda.valor_total == p["total"]
                    and venda.vendedor_id == (vendedor.id if vendedor else None)
                )
                if iguais:
                    contagem["inalterados"] += 1
                    continue
                if not permitir_atualizacao:
                    raise ErroImportacao(
                        f"Pedido {num} já existe com dados diferentes. Marque a atualização de pedidos existentes após conferir a carga."
                    )
                if not {i[0] for i in existentes} <= {i[0] for i in novos_itens}:
                    raise ErroImportacao(
                        f"Pedido {num}: a nova carga removeria produtos existentes. Envie o pedido completo."
                    )
                venda.itens.clear()
                self.db.flush()
                contagem["atualizados"] += 1
            else:
                venda = Venda(
                    numero_pedido=num, cliente_id=cliente.id, fabrica_id=fabrica.id
                )
                self.db.add(venda)
<<<<<<< Updated upstream
                self.db.flush()
                vendas_existentes[num_pedido] = venda

            if num_pedido in prod_agrupados.groups:
                for _, item_row in prod_agrupados.get_group(num_pedido).iterrows():
                    sku_item = self.normalizar_sku(item_row["sku"])
                    prod_id = produtos_cache.get(sku_item)
                    if prod_id:
                        self.db.add(
                            ItemVenda(
                                venda_id=venda.id,
                                produto_id=prod_id,
                                quantidade=item_row["quantidade"],
                                preco_unitario=item_row["preco_unitario"],
                            )
                        )

        self.db.commit()
        
    @staticmethod
    def sanitizar_valor_planilha(valor: object) -> object:
        """Neutraliza tentativa de injeção de fórmulas de planilhas."""
        if isinstance(valor, str):
            val_limpo = valor.strip()
            # Prefixos perigosos que iniciam comandos DDE ou fórmulas no Excel
            if val_limpo.startswith(("=", "+", "-", "@", "\t", "\r")):
                return f"'{val_limpo}"  # Aspas simples forçam o texto como literal puro
            return val_limpo
        return valor
=======
                contagem["adicionados"] += 1
            venda.data_venda = p["data"]
            venda.valor_total = p["total"]
            venda.vendedor_id = vendedor.id if vendedor else None
            self.db.flush()
            for produto_id, qtd, preco, subtotal in novos_itens:
                venda.itens.append(
                    ItemVenda(
                        produto_id=produto_id,
                        quantidade=qtd,
                        preco_unitario=preco,
                        subtotal=subtotal,
                    )
                )
        self.db.flush()
        return dict(
            status="sucesso",
            mensagem=f"Carga validada: {len(pedidos)} pedidos, {contagem['itens']} itens.",
            **contagem,
        )
>>>>>>> Stashed changes
