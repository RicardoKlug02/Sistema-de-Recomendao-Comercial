import pandas as pd
import hashlib
import re
from datetime import datetime
from sqlalchemy.orm import Session

class ExcelService:
    def __init__(self, db_session: Session):
        self.db = db_session

    # --- MÉTODO PRINCIPAL ---
    def importar_processo_completo(self, path_cab, path_itens):
        try:
            df_produtos = self._limpar_excel_produtos(path_itens)
            df_cabecalho = self._limpar_excel_cabecalho(path_cab)
            
            self._validar_e_salvar(df_cabecalho, df_produtos)
            
            return {"status": "sucesso", "mensagem": "Dados importados e anonimizados."}
        except Exception as e:
            self.db.rollback()
            return {"status": "erro", "mensagem": str(e)}

    # --- MÉTODOS PRIVADOS ---
    def _anonimizar(self, valor):
        salt = "TCC_SECRET_2026"
        return hashlib.sha256((str(valor) + salt).encode()).hexdigest()
    
    def _limpar_excel_cabecalho(self, caminho_arquivo: str):
        
        df = pd.read_excel(caminho_arquivo, skiprows=10)
    
        # 1. Limpeza de nomes de colunas: remove espaços extras e normaliza para minúsculo
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    
        # 2. Tratamento de colunas importantes
        if 'total_em_produtos' in df.columns:
            df['total_em_produtos'] = pd.to_numeric(df['total_em_produtos'], errors='coerce')
            df = df.dropna(subset=['total_em_produtos'])
        
        # 3. Filtro básico: remove linhas onde o número do pedido esteja vazio
        df = df.dropna(subset=['pedido'])
    
        return df

    def _limpar_excel_produtos(self, caminho_arquivo):
        df = pd.read_excel(caminho_arquivo, header=None, skiprows=9)
        df['codigo_produto'] = None
        codigo_atual = None
        padrao_data = r'\d{2}/\d{2}/\d{4}'
        
        for index, row in df.iterrows():
            linha = str(row[0])
            if "Produto:" in linha:
                codigo_atual = linha.split("Produto: ")[1].split(" -")[0]
            elif re.search(padrao_data, linha):
                df.at[index, 'codigo_produto'] = codigo_atual
        
        df_limpo = df.dropna(subset=['codigo_produto'])
        df_limpo.columns = ['data', 'pedido', 'nome_fantasia', 'vendedor', 'preco', 'qtd', 'subtotal', 'id_produto']
        return df_limpo

    def _validar_e_salvar(self, df_cab, df_prod, nome_arquivo):
        # 1. Validação de Soma
        for _, row_cab in df_cab.iterrows():
            total_nota = row_cab['total_em_produtos']
            total_calc = df_prod[df_prod['pedido'] == row_cab['id_pedido']]['subtotal'].sum()
            
            if abs(total_calc - total_nota) > 0.01:
                raise ValueError(f"Divergência no pedido {row_cab['id_pedido']}")

            # 2. Persistência com Anonimização
            venda = Venda(
                id=row_cab['id_pedido'],
                cliente_id=self._anonimizar(row_cab['id_cliente']),
                data=row_cab['data']
            )
            self.db.add(venda)
            
        self.db.commit()