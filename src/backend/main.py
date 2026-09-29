from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session
from src.backend.app.core.config import settings
from src.backend.app.core.database import get_db
from src.backend.app.api.auth import router as auth_router
from src.backend.app.api.cliente import router as cliente_router
from src.backend.app.api.upload import router as upload_router
from src.backend.app.api.comercial import router as comercial_router

app = FastAPI(title="Sales Intelligence API", version="1.1.0",
              description="Indicadores, Cliente 360º e alertas de inteligência comercial")
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS,
                   allow_credentials=False, allow_methods=["GET", "POST", "OPTIONS"],
                   allow_headers=["Authorization", "Content-Type"])
for router in (auth_router, cliente_router, upload_router, comercial_router):
    app.include_router(router, prefix="/api/v1")

DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if settings.SERVE_FRONTEND and (DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")


@app.get("/health", tags=["Healthcheck"])
def health():
    return {"status": "online", "sistema": "Sales Intelligence Backend"}


@app.get("/health/ready", tags=["Healthcheck"])
def ready(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(503, "Banco de dados temporariamente indisponível.")
    return {"status": "online", "banco": "conectado"}


@app.get("/", include_in_schema=False)
def inicio():
    if settings.SERVE_FRONTEND and (DIST / "index.html").is_file():
        return FileResponse(DIST / "index.html")
    return {"status": "online", "sistema": "Sales Intelligence Backend", "docs": "/docs"}


@app.get("/{arquivo}", include_in_schema=False)
def publico(arquivo: str):
    if settings.SERVE_FRONTEND and arquivo in ("favicon.svg", "icons.svg"):
        caminho = DIST / arquivo
        if caminho.is_file():
            return FileResponse(caminho)
    raise HTTPException(404, "Recurso não encontrado.")
