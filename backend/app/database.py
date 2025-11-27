# Em backend/app/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.engine import Engine
from sqlalchemy import event # ⬅️ NOVO: Importar event listener
import os

# ... (código para obter e corrigir SQLALCHEMY_DATABASE_URL mantido) ...
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Se não existir (estamos local), usa uma string padrão ou SQLite para teste
if not SQLALCHEMY_DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = "postgresql://postgres:suasenha@localhost/condomanager"

# CORREÇÃO CRÍTICA PARA RENDER/SUPABASE
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 🚨 FIX CRÍTICO: Listener para definir o search_path
@event.listens_for(Engine, "connect")
def set_postgres_search_path(dbapi_connection, connection_record):
    """Garante que o PostgreSQL use o schema 'public'."""
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("SET search_path TO public;")
        cursor.close()
    except Exception as e:
        print(f"Erro ao definir search_path: {e}") 

# Cria o motor do banco
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    poolclass=NullPool
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
