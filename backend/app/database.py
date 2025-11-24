from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool # <--- 1. IMPORTAR NullPool
import os

# 1. Tenta pegar a URL do Render (Variável de Ambiente)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# 2. Se não existir (estamos local), usa uma string padrão ou SQLite para teste
if not SQLALCHEMY_DATABASE_URL:
    # Ajuste aqui para o seu banco local se preferir
    SQLALCHEMY_DATABASE_URL = "postgresql://postgres:suasenha@localhost/condomanager"

# 3. CORREÇÃO CRÍTICA PARA RENDER/SUPABASE
# O SQLAlchemy não aceita 'postgres://', precisa ser 'postgresql://'
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Cria o motor do banco
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    poolclass=NullPool # <--- 2. APLICAR NULLPOOL AQUI
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


