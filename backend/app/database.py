# backend/app/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool # Importação do fix para o pooler do Supabase
import os

# 1. Leitura da variável de ambiente (Render)
SQLALCHEMY_DATABASE_URL = os.getenv("postgresql://postgres.jqlygddtjkvtuckwpucp:tYEb8LxvOSmT6Z49@aws-1-sa-east-1.pooler.supabase.com:6543/postgres") #os.getenv("DATABASE_URL"

# Fallback para teste local se ENV não estiver setada
if not SQLALCHEMY_DATABASE_URL:
    # USAMOS A STRING LIMPA DIRETAMENTE AQUI, JÁ QUE ELA NÃO TEM CARACTERES RUINS
    SQLALCHEMY_DATABASE_URL = "postgresql://postgres.jqlygddtjkvtuckwpucp:tYEb8LxvOSmT6Z49@aws-1-sa-east-1.pooler.supabase.com:6543/postgres" 

# 2. Correção Crítica do Prefixo (Supabase)
# Substitui 'postgres://' por 'postgresql://' se necessário
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 3. CRIAÇÃO DO MOTOR COM NULLPOOL
# Desabilita o pooling interno do SQLAlchemy para evitar o conflito SASL com a porta 6543.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    poolclass=NullPool # <--- AQUI ESTÁ A SOLUÇÃO
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
