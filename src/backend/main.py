from fastapi import FastAPI
from src.backend.app.core.config import settings
from src.backend.app.api.comercial import router as comercial_router
from src.backend.app.api.usuarios import router as usuarios_router
from fastapi.middleware.cors import CORSMiddleware
from src.backend.app.core.limites import LimiteUpload, LimiteAutenticacao

from src.backend.app.api.auth import router as auth_router
from src.backend.app.api.cliente import router as cliente_router
from src.backend.app.api.upload import router as upload_router

app = FastAPI(
    title="Sales Intelligence API",
    version="1.0.0",
    description="Motor de Inteligência Comercial B2B, Previsão de Recompra e Cross-Selling",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(LimiteUpload)
app.add_middleware(LimiteAutenticacao)

# Configuração de CORS liberada para consumo do Frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(comercial_router, prefix="/api/v1")
app.include_router(usuarios_router, prefix="/api/v1")

# Inclusão dos Roteadores da API v1
app.include_router(auth_router, prefix="/api/v1")
app.include_router(cliente_router, prefix="/api/v1")
app.include_router(upload_router, prefix="/api/v1")


@app.get("/", tags=["Healthcheck"])
def read_root():
    return {
        "status": "online",
        "sistema": "Sales Intelligence Backend",
        "docs": "/docs",
    }


@app.get("/health/ready", tags=["Healthcheck"])
def pronto():
    from sqlalchemy import text
    from src.backend.app.core.database import engine
    from fastapi import HTTPException

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM usuarios LIMIT 1"))
        return {"status": "pronto"}
    except Exception:
        raise HTTPException(503, "Banco indisponível ou migrações pendentes.")
