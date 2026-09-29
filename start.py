import os
import subprocess
import uvicorn

def run_migrations():
    print("Iniciando verificação de migrações do Alembic...")
    try:
        # Tenta dar upgrade normal para o head
        result = subprocess.run(["alembic", "upgrade", "head"], check=True, capture_output=True, text=True)
        print(result.stdout)
        print("Migrações aplicadas com sucesso!")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao rodar migrações: {e.stderr}")
        print("Tentando sincronizar o Alembic (stamp head)...")
        try:
            # Se falhar por revisão perdida, força o stamp para o head atual
            subprocess.run(["alembic", "stamp", "head"], check=True)
            print("Alembic sincronizado com sucesso!")
        except Exception as stamp_error:
            print(f"Erro crítico ao sincronizar Alembic: {stamp_error}")

if __name__ == "__main__":
    # Roda as migrações/sincronização antes de subir a API
    run_migrations()
    
    # Inicia o servidor Uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Iniciando Uvicorn na porta {port}...")
    uvicorn.run("src.backend.app.main:app", host="0.0.0.0", port=port)