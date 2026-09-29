"""Lista todos os 'from src.backend... import X' em que X não existe no módulo.

Uso (na raiz do projeto, com o .venv ativo):
    python verificar_imports.py
"""
import ast
from pathlib import Path

RAIZ = Path.cwd()  # rode sempre a partir da raiz do projeto
PASTAS = ["src", "tests", "scripts", "alembic"]


def arquivo_do_modulo(modulo: str):
    base = RAIZ.joinpath(*modulo.split("."))
    if base.with_suffix(".py").exists():
        return base.with_suffix(".py")
    if (base / "__init__.py").exists():
        return base / "__init__.py"
    return None


def nomes_definidos(arquivo: Path) -> set:
    arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
    nomes = set()
    for no in ast.walk(arvore):
        if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            nomes.add(no.name)
        elif isinstance(no, ast.Assign):
            for alvo in no.targets:
                if isinstance(alvo, ast.Name):
                    nomes.add(alvo.id)
        elif isinstance(no, ast.AnnAssign) and isinstance(no.target, ast.Name):
            nomes.add(no.target.id)
        elif isinstance(no, (ast.Import, ast.ImportFrom)):
            for a in no.names:
                nomes.add((a.asname or a.name).split(".")[0])
    return nomes


def main():
    problemas = []
    for pasta in PASTAS:
        for arq in (RAIZ / pasta).rglob("*.py"):
            if ".venv" in arq.parts:
                continue
            try:
                arvore = ast.parse(arq.read_text(encoding="utf-8"))
            except SyntaxError as e:
                problemas.append(f"{arq.relative_to(RAIZ)}: erro de sintaxe ({e})")
                continue
            for no in ast.walk(arvore):
                if not (isinstance(no, ast.ImportFrom) and no.module):
                    continue
                if not no.module.startswith("src."):
                    continue
                alvo = arquivo_do_modulo(no.module)
                if alvo is None:
                    problemas.append(
                        f"{arq.relative_to(RAIZ)}:{no.lineno} módulo inexistente: {no.module}"
                    )
                    continue
                definidos = nomes_definidos(alvo)
                for a in no.names:
                    if a.name == "*" or a.name in definidos:
                        continue
                    if arquivo_do_modulo(f"{no.module}.{a.name}"):
                        continue  # é um submódulo
                    problemas.append(
                        f"{arq.relative_to(RAIZ)}:{no.lineno} importa '{a.name}' "
                        f"de {no.module}, mas não existe lá"
                    )
    if problemas:
        print("Imports quebrados:\n")
        print("\n".join(sorted(set(problemas))))
    else:
        print("Nenhum import quebrado encontrado.")


if __name__ == "__main__":
    main()