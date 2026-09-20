from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# Configuração de CORS liberada para consumo do Frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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