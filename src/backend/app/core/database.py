# src/backend/app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Carrega as variáveis do seu arquivo .env
load_dotenv()

# Pega a URL do banco do seu .env
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Cria a engine do SQLAlchemy
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Cria a fábrica de sessões (usada para fazer consultas no banco)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# A famosa Base que todos os seus modelos irão herdar
Base = declarative_base()