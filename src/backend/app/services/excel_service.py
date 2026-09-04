from datetime import datetime
import hashlib
import re
import pandas as pd
from sqlalchemy.orm import Session

from src.backend.app.models.cliente import Cliente
from src.backend.app.models.fabrica import Fabrica
from src.backend.app.models.item_venda import ItemVenda
from src.backend.app.models.produto import Produto
from src.backend.app.models.venda import Venda
from src.backend.app.models.vendedor import Vendedor


class ExcelService:

    def __init__(self, db_session: Session):
        self.db = db_session
        self.salt = "TCC_SECRET_2026"

    # --- MÉTODO PRINCIPAL ---
    def importar_processo_completo(self, path_cab: str, path_itens: str):
        try:
            df_produtos = self._limpar_excel_produtos(path_itens)
            df_cabecalho = self._limpar_excel_cabecalho(path_cab)

            self._validar_e_salvar(df_cabecalho, df_produtos)

            return {
                "status": "sucesso",
                "mensagem": "Dados importados e anonimizados com sucesso.",
            }
        except Exception as e:
            self.db.rollback()
            return {"status": "erro", "mensagem": str(e)}

    # --- MÉTODOS PRIVADOS ---
    def _anonimizar(self, valor: str) -> str:
        if not valor or pd.isna(valor) or str(valor).strip() == "nan":
            return "ANON_DESCONHECIDO"
        texto = f"{str(valor).strip()}_{self.salt}"
        # Pega os primeiros 14 caracteres do hash (14 + 4 de 'CLI_' = 18 caracteres no total)
        return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:14].upper()

    def _converter_valor_br(self, valor) -> float:
        if pd.isna(valor):
            return 0.0
        if isinstance(valor, (int, float)):
            return float(valor)
        val_str = str(valor).replace("R$", "").strip()
        if "," in val_str:
            val_str = val_str.replace(".", "").replace(",", ".")
        try:
            return float(val_str)
        except ValueError:
            return 0.0

    def _limpar_excel_cabecalho(self, caminho_arquivo: str) -> pd.DataFrame:
        df = pd.read_excel(caminho_arquivo, skiprows=10, dtype=str)
        df.columns = [
            str(c).strip().lower().replace(" ", "_") for c in df.columns
        ]

        col_map = {}
        for col in df.columns:
            if "data" in col:
                col_map["data"] = col
            elif "pedido" in col:
                col_map["pedido"] = col
            elif "cnpj" in col or "cpf" in col:
                col_map["cnpj_cpf"] = col
            elif "vendedor" in col:
                col_map["vendedor"] = col
            elif "total" in col:
                col_map["valor_total"] = col

        df = df.rename(columns={v: k for k, v in col_map.items()})
        df = df.dropna(subset=["pedido"])
        df["pedido"] = df["pedido"].astype(str).str.strip()
        df["valor_total"] = df["valor_total"].apply(self._converter_valor_br)
        return df

    def _limpar_excel_produtos(self, caminho_arquivo: str) -> pd.DataFrame:
        df = pd.read_excel(caminho_arquivo, header=None, dtype=str)
        itens = []
        sku_atual = None
        nome_produto_atual = None

        for _, row in df.iterrows():
            col_0 = str(row[0]).strip() if pd.notna(row[0]) else ""

            if col_0.startswith("Produto:"):
                texto = col_0.replace("Produto:", "").strip()
                match = re.match(r"^([^-]+)\s*-\s*(.+)$", texto)
                if match:
                    sku_atual = match.group(1).strip()
                    nome_produto_atual = match.group(2).strip()
                else:
                    sku_atual = texto
                    nome_produto_atual = texto
                continue

            if any(
                col_0.startswith(p)
                for p in ["Data", "Filtros", "Relatório", "Total"]
            ):
                continue

            pedido_val = row[1]
            if pd.isna(pedido_val) or str(pedido_val).strip() == "":
                continue

            try:
                int(str(pedido_val).strip())
            except ValueError:
                continue

            preco = self._converter_valor_br(row[4])
            qtd = int(self._converter_valor_br(row[5]))
            subtotal = (
                self._converter_valor_br(row[6])
                if len(row) > 6
                else round(preco * qtd, 2)
            )

            itens.append(
                {
                    "sku": sku_atual,
                    "nome_produto": nome_produto_atual,
                    "pedido": str(pedido_val).strip(),
                    "preco_unitario": preco,
                    "quantidade": qtd,
                    "subtotal": subtotal,
                }
            )

        return pd.DataFrame(itens)

    def _validar_e_salvar(self, df_cab: pd.DataFrame, df_prod: pd.DataFrame):
        # 1. Fábrica Matriz
        fabrica = self.db.query(Fabrica).first()
        if not fabrica:
            fabrica = Fabrica(nome_fantasia="Fábrica Matriz")
            self.db.add(fabrica)
            self.db.flush()

        # 2. Cache e Sincronização de Clientes (com Anonimização LGPD)
        clientes_cache = {
            c.cnpj_cpf: c.id
            for c in self.db.query(Cliente.cnpj_cpf, Cliente.id).all()
        }
        for _, row in df_cab.iterrows():
            doc_real = str(row.get("cnpj_cpf", "")).strip()
            if not doc_real or doc_real == "nan":
                continue

            doc_anon = f"CLI_{self._anonimizar(doc_real)}"
            if doc_anon not in clientes_cache:
                cliente = Cliente(
                    razao_social=f"Cliente {doc_anon[:10]}",
                    nome_fantasia=f"Fantasia {doc_anon[:10]}",
                    cnpj_cpf=doc_anon,
                )
                self.db.add(cliente)
                self.db.flush()
                clientes_cache[doc_anon] = cliente.id

        # 3. Cache e Sincronização de Vendedores (Anonimizados)
        vendedores_cache = {
            v.nome: v.id for v in self.db.query(Vendedor.nome, Vendedor.id).all()
        }
        for _, row in df_cab.iterrows():
            vend_real = str(row.get("vendedor", "")).strip()
            if not vend_real or vend_real == "nan":
                continue

            vend_anon = f"Vendedor_{self._anonimizar(vend_real)[:8]}"
            if vend_anon not in vendedores_cache:
                vendedor = Vendedor(nome=vend_anon)
                self.db.add(vendedor)
                self.db.flush()
                vendedores_cache[vend_anon] = vendedor.id

        # 4. Cache e Sincronização de Produtos
        produtos_cache = {
            p.sku: p.id for p in self.db.query(Produto.sku, Produto.id).all()
        }
        for _, row in (
            df_prod[["sku", "nome_produto"]].drop_duplicates().iterrows()
        ):
            sku = str(row["sku"]).strip()
            if sku and sku not in produtos_cache:
                produto = Produto(
                    sku=sku,
                    nome=str(row["nome_produto"]),
                    fabrica_id=fabrica.id,
                )
                self.db.add(produto)
                self.db.flush()
                produtos_cache[sku] = produto.id

        # 5. Persistência de Vendas e Itens (Upsert)
        prod_agrupados = df_prod.groupby("pedido")

        for _, row_cab in df_cab.iterrows():
            num_pedido = row_cab["pedido"]
            doc_anon = f"CLI_{self._anonimizar(str(row_cab.get('cnpj_cpf', '')))}"
            vend_anon = f"Vendedor_{self._anonimizar(str(row_cab.get('vendedor', '')))[:8]}"

            cliente_id = clientes_cache.get(doc_anon)
            vendedor_id = vendedores_cache.get(vend_anon)
            valor_total = row_cab["valor_total"]

            # Tratamento da data
            data_raw = str(row_cab.get("data", ""))[:10]
            try:
                data_venda = datetime.strptime(data_raw, "%d/%m/%Y").date()
            except Exception:
                data_venda = datetime(2026, 1, 1).date()

            venda = (
                self.db.query(Venda)
                .filter(Venda.numero_pedido == num_pedido)
                .first()
            )
            if venda:
                venda.cliente_id = cliente_id
                venda.vendedor_id = vendedor_id
                venda.data_venda = data_venda
                venda.valor_total = valor_total
                self.db.query(ItemVenda).filter(
                    ItemVenda.venda_id == venda.id
                ).delete()
            else:
                venda = Venda(
                    numero_pedido=num_pedido,
                    cliente_id=cliente_id,
                    vendedor_id=vendedor_id,
                    fabrica_id=fabrica.id,
                    data_venda=data_venda,
                    valor_total=valor_total,
                )
                self.db.add(venda)
                self.db.flush()

            # Insere os itens da venda
            if num_pedido in prod_agrupados.groups:
                for _, item_row in prod_agrupados.get_group(
                    num_pedido
                ).iterrows():
                    prod_id = produtos_cache.get(item_row["sku"])
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