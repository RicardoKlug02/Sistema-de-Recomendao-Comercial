"""Servidor de teste isolado, com dados sintéticos e sem envio de e-mails."""

import os
import sys
import tempfile
from pathlib import Path
from cryptography.fernet import Fernet

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
with tempfile.TemporaryDirectory(prefix="rioverde-e2e-") as pasta:
    os.environ.update(
        DATABASE_URL="sqlite:///" + str(Path(pasta) / "e2e.db"),
        JWT_SECRET_KEY="e2e-" + "x" * 48,
        CHAVE_SERIALIZER="e2e-" + "y" * 48,
        BLIND_INDEX_SALT="e2e-" + "z" * 48,
        SECRET_ENCRYPTION_KEY=Fernet.generate_key().decode(),
        MAIL_ENABLED="False",
        CORS_ORIGINS='["http://127.0.0.1:5178"]',
    )
    from src.backend.app.core.database import Base, engine, SessionLocal
    from src.backend.app.models import (
        Usuario,
        Cliente,
        Fabrica,
        Produto,
        Venda,
        ItemVenda,
    )
    from src.backend.app.core.security import gerar_hash_senha, gerar_blind_index
    from datetime import date

    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        db.add_all(
            [
                Usuario(
                    nome="Admin de Teste",
                    email="admin@example.com",
                    senha_hash=gerar_hash_senha("TesteSeguro123"),
                    perfil="admin",
                    aprovado=True,
                ),
                Usuario(
                    nome="Vendedor de Teste",
                    email="vendedor@example.com",
                    senha_hash=gerar_hash_senha("TesteSeguro123"),
                    perfil="vendedor",
                    aprovado=True,
                ),
            ]
        )
        c = Cliente(
            razao_social="Comercial Exemplo",
            cnpj_cpf="11222333000144",
            cnpj_hash=gerar_blind_index("11222333000144"),
            cidade="Blumenau",
            estado="SC",
        )
        f = Fabrica(nome_fantasia="Fábrica Exemplo")
        db.add_all([c, f])
        db.flush()
        p = Produto(
            nome="Cabo elétrico de teste",
            sku="TESTE-1",
            categoria="Elétrica",
            fabrica_id=f.id,
        )
        db.add(p)
        db.flush()
        for n, mes in enumerate([1, 2, 3], 1):
            v = Venda(
                numero_pedido=f"TESTE-{n}",
                cliente_id=c.id,
                fabrica_id=f.id,
                data_venda=date(2026, mes, 1),
                valor_total=100,
            )
            db.add(v)
            db.flush()
            db.add(
                ItemVenda(
                    venda_id=v.id, produto_id=p.id, quantidade=10, preco_unitario=10
                )
            )
        db.commit()
    import uvicorn

    uvicorn.run("src.backend.main:app", host="127.0.0.1", port=8765)
