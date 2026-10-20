"""Inicializa o banco pela mesma cadeia de migrações usada no Render."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from start import run_migrations, bootstrap_admin

def init_db():
    run_migrations()
    bootstrap_admin()
    print("Migrações aplicadas.")

if __name__ == "__main__":
    init_db()
