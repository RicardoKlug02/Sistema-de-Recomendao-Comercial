from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# Aqui você importará suas rotas futuramente
# from app.api.cliente import router as cliente_router

app = FastAPI(title="TCC API - Sistema de Recomendação")

# CORS para o seu irmão conseguir consumir a API do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Bem-vindo ao Backend do TCC. Documentação em /docs"}

# Exemplo de como você vai registrar suas rotas:
# app.include_router(cliente_router, prefix="/api")