from datetime import datetime
import os
from pathlib import Path
import re
import sys
import pandas as pd
from sqlalchemy.orm import Session

#Ajustamos sys.path para a raiz
raiz = Path(__file__).resolve().parent.parent
if str(raiz) not in sys.path:
    sys.path.insert(0, str(raiz))

from src.backend.app.core.database import engine
from src.backend.app.models.cliente import Cliente
from src.backend.app.models.fabrica import Fabrica
from src.backend.app.models.item_venda import ItemVenda
from src.backend.app.models.produto import Produto
from src.backend.app.models.venda import Venda
from src.backend.app.models.vendedor import Vendedor


def converter_valor_br(valor) -> float:
    """Converte valores no padrão pt-BR ('7.685,10') para float."""
    if pd.isna(valor):
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    val_str = (
        str(valor).replace("R$", "").replace(".", "").replace(",", ".").strip()
    )
    try:
        return float(val_str)
    except ValueError:
        return 0.0


def carregar_planilha_cabecalho(caminho_arquivo: str) -> pd.DataFrame:
    print(f"Lendo cabeçalhos de {caminho_arquivo}...")
    df = pd.read_excel(caminho_arquivo, skiprows=10, dtype=str)
    df.columns = df.columns.str.strip()

    # Mapeamento de colunas
    col_map = {}
    for col in df.columns:
        c_lower = col.lower()
        if "data" in c_lower:
            col_map["data"] = col
        elif "pedido" in c_lower:
            col_map["pedido"] = col
        elif "razão" in c_lower or "razao" in c_lower:
            col_map["razao_social"] = col
        elif "fantasia" in c_lower or "nome fan" in c_lower:
            col_map["nome_fantasia"] = col
        elif "cnpj" in c_lower or "cpf" in c_lower:
            col_map["cnpj_cpf"] = col
        elif "cep" in c_lower:
            col_map["cep"] = col
        elif "rede" in c_lower:
            col_map["grupo_economico"] = col
        elif "vendedor" in c_lower:
            col_map["vendedor"] = col
        elif "total" in c_lower:
            col_map["valor_total"] = col
        elif "represent" in c_lower:
            col_map["representante_fabrica"] = col

    df_renomeado = df.rename(columns={v: k for k, v in col_map.items()})
    return df_renomeado


def carregar_planilha_itens(caminho_arquivo: str) -> pd.DataFrame:
    print(f"Lendo e desestruturando itens de {caminho_arquivo}...")
    df_raw = pd.read_excel(caminho_arquivo, header=None, dtype=str)

    itens = []
    sku_atual = None
    nome_produto_atual = None

    for _, row in df_raw.iterrows():
        col_0 = str(row[0]).strip() if pd.notna(row[0]) else ""

        #Identifica o cabeçalho do produto
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

        #Ignora linhas de topo, filtros e vazias
        if any(
            col_0.startswith(prefix)
            for prefix in ["Data", "Filtros", "Relatório"]
        ):
            continue

        #Pedido fica na coluna B (índice 1)
        pedido_val = row[1]
        if pd.isna(pedido_val) or str(pedido_val).strip() == "":
            continue

        #Trata linhas de totais que repetem a contagem
        try:
            int(str(pedido_val).strip())
        except ValueError:
            continue

        pedido = str(pedido_val).strip()
        preco_unit = converter_valor_br(row[4])
        qtd = converter_valor_br(row[5])

        itens.append(
            {
                "sku": sku_atual,
                "nome_produto": nome_produto_atual,
                "numero_pedido": pedido,
                "preco_unitario": preco_unit,
                "quantidade": int(qtd),
            }
        )

    return pd.DataFrame(itens)


def importar_dados(caminho_cabecalho: str, caminho_itens: str):
    df_cabecalho = carregar_planilha_cabecalho(caminho_cabecalho)
    df_itens = carregar_planilha_itens(caminho_itens)

    with Session(engine) as session:
        try:
            # 1- Obter ou criar Fábrica Padrão
            fabrica = session.query(Fabrica).first()
            if not fabrica:
                fabrica = Fabrica(nome_fantasia="Fábrica Padrão")
                session.add(fabrica)
                session.flush()

            #Caches em memória para acelerar a inserção
            clientes_cache = {
                c.cnpj_cpf: c.id
                for c in session.query(Cliente).all()
                if c.cnpj_cpf
            }
            vendedores_cache = {
                v.nome: v.id for v in session.query(Vendedor).all()
            }
            produtos_cache = {
                p.sku: p.id for p in session.query(Produto).all() if p.sku
            }

            print("\n- Sincronizando Clientes e Vendedores...")
            for _, row in df_cabecalho.iterrows():
                cnpj = str(row.get("cnpj_cpf", "")).strip()
                if cnpj and cnpj not in clientes_cache and cnpj != "nan":
                    cliente = Cliente(
                        razao_social=str(
                            row.get("razao_social", "Não informado")
                        ),
                        nome_fantasia=str(
                            row.get("nome_fantasia", row.get("razao_social"))
                        ),
                        cnpj_cpf=cnpj,
                        cep=str(row.get("cep", ""))[:10],
                        grupo_economico=str(row.get("grupo_economico", "")),
                    )
                    session.add(cliente)
                    session.flush()
                    clientes_cache[cnpj] = cliente.id

                vendedor_nome = str(row.get("vendedor", "")).strip()
                if (
                    vendedor_nome
                    and vendedor_nome not in vendedores_cache
                    and vendedor_nome != "nan"
                ):
                    vendedor = Vendedor(nome=vendedor_nome)
                    session.add(vendedor)
                    session.flush()
                    vendedores_cache[vendedor_nome] = vendedor.id

            print("- Sincronizando Produtos...")
            for _, row in (
                df_itens[["sku", "nome_produto"]]
                .drop_duplicates()
                .iterrows()
            ):
                sku = str(row["sku"]).strip()
                if sku and sku not in produtos_cache and sku != "nan":
                    produto = Produto(
                        sku=sku,
                        nome=str(row["nome_produto"]),
                        fabrica_id=fabrica.id,
                    )
                    session.add(produto)
                    session.flush()
                    produtos_cache[sku] = produto.id

            print("- Inserindo Vendas e Itens no Banco...")
            pedidos_itens_agrupados = df_itens.groupby("numero_pedido")
            total_pedidos = len(df_cabecalho)

            for idx, (_, row) in enumerate(df_cabecalho.iterrows(), start=1):
                pedido_num = str(row.get("pedido", "")).strip()
                if not pedido_num or pedido_num == "nan":
                    continue

                #Data da venda
                data_str = str(row.get("data", "")).strip()
                try:
                    data_obj = datetime.strptime(
                        data_str[:10], "%d/%m/%Y"
                    ).date()
                except Exception:
                    data_obj = datetime(2026, 1, 1).date()

                cnpj = str(row.get("cnpj_cpf", "")).strip()
                vendedor_nome = str(row.get("vendedor", "")).strip()
                valor_total = converter_valor_br(row.get("valor_total", 0.0))

                venda = Venda(
                    cliente_id=clientes_cache.get(cnpj),
                    vendedor_id=vendedores_cache.get(vendedor_nome),
                    fabrica_id=fabrica.id,
                    data_venda=data_obj,
                    valor_total=valor_total,
                )
                session.add(venda)
                session.flush()  #Gera o venda.id

                #Se houver itens na segunda planilha para este pedido
                if pedido_num in pedidos_itens_agrupados.groups:
                    grupo_itens = pedidos_itens_agrupados.get_group(pedido_num)
                    for _, item_row in grupo_itens.iterrows():
                        sku = str(item_row["sku"]).strip()
                        prod_id = produtos_cache.get(sku)
                        if prod_id:
                            item = ItemVenda(
                                venda_id=venda.id,
                                produto_id=prod_id,
                                quantidade=int(item_row["quantidade"]),
                                preco_unitario=float(
                                    item_row["preco_unitario"]
                                ),
                            )
                            session.add(item)

                if idx % 100 == 0:
                    print(f"  Processados {idx}/{total_pedidos} pedidos...")

            session.commit()
            print(
                f"\n✓ Importação finalizada com sucesso! {total_pedidos} vendas inseridas."
            )

        except Exception as e:
            session.rollback()
            print(f"\n❌ Erro durante a importação: {e}")
            raise


if __name__ == "__main__":
    #Indique os caminhos reais dos seus arquivos
    ARQUIVO_CABECALHO = "data/pedidos_janeiro_2026.xlsx"
    ARQUIVO_ITENS = "data/itens_janeiro_2026.xlsx"

    importar_dados(ARQUIVO_CABECALHO, ARQUIVO_ITENS)