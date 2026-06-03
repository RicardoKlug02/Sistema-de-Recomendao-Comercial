import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../../../../.env'))

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

class DatabaseConfig:
    def __init__(self):
        self.engine = create_engine(DB_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

db_config = DatabaseConfig()

engine = db_config.engine
SessionLocal = db_config.SessionLocal
Base = declarative_base()