import pandas as pd
from sqlalchemy.orm import Session
from src.backend.app.models.cliente import Cliente

class ExcelService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def importar_clientes_de_excel(self, caminho_arquivo: str):
        """
        Lê um arquivo Excel e salva no banco de dados.
        O Excel deve ter colunas compatíveis com os atributos da sua classe Cliente.
        """
        try:
            # Lê o Excel
            df = pd.read_excel(caminho_arquivo)
            
            # Limpeza básica (ex: remover linhas com nomes nulos)
            df = df.dropna(subset=['nome']) 

            # Transforma as linhas do DF em instâncias do modelo Cliente
            for _, row in df.iterrows():
                novo_cliente = Cliente(
                    nome=row['nome'],
                    segmento=row.get('segmento'), # .get evita erro se a coluna não existir
                    email=row.get('email')
                )
                self.db.add(novo_cliente)

            # Comita as alterações no banco
            self.db.commit()
            return {"status": "sucesso", "registros": len(df)}

        except Exception as e:
            self.db.rollback()
            return {"status": "erro", "mensagem": str(e)}