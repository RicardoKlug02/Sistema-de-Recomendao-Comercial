import sys
from pathlib import Path

raiz = Path(__file__).resolve().parent.parent
if str(raiz) not in sys.path:
    sys.path.insert(0, str(raiz))

from sqlalchemy.orm import Session
from src.backend.app.core.database import engine
from src.backend.app.core.security import decodificar_token_acesso
from src.backend.app.services.auth_service import AuthService


def testar_fluxo_jwt():
    with Session(engine) as session:
        auth = AuthService(db_session=session)

        email_teste = "rick.nklug@gmail.com"
        senha_teste = "1234567"

        print(f"Tentando autenticar: {email_teste}")
        usuario = auth.autenticar(email=email_teste, senha_plana=senha_teste)

        if not usuario:
            print("❌ Falha na autenticação: Verifique se o usuário foi criado.")
            return

        print(f"✅ Usuário validado: {usuario.nome} (ID: {usuario.id})")

        # Gera o token
        sessao = auth.gerar_sessao(usuario)
        token = sessao["access_token"]
        print(f"\n🔑 Token JWT Gerado com Sucesso:\n{token[:40]}... (tamanho: {len(token)})")

        # Valida a decodificação
        dados = decodificar_token_acesso(token)
        print("\n🔓 Conteúdo decodificado do Token (Payload):", dados)

        assert dados["sub"] == email_teste, "O e-mail no token não bate!"
        print("\n🎉 Tudo funcionando perfeitamente!")


if __name__ == "__main__":
    testar_fluxo_jwt()