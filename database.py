import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Tenta pegar a URL do ambiente (Render). Se não tiver, usa a local.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:SUA_SENHA_LOCAL@localhost:5432/app_sindico_db")

# Correção para o Render que usa postgres:// mas o SQLAlchemy exige postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()