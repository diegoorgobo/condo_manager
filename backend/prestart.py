# backend/prestart.py

import os
from app.database import engine, Base
from app import models # Garante que todos os modelos sejam importados

# 1. Correção Crítica do Prefixo (necessário se o Render não fizer isso)
db_url = os.getenv("DATABASE_URL")
if db_url and db_url.startswith("postgres://"):
    os.environ["DATABASE_URL"] = db_url.replace("postgres://", "postgresql://", 1)

print("Verificando e criando tabelas ausentes no banco de dados...")
# Este comando cria apenas as tabelas que ainda não existem
Base.metadata.create_all(bind=engine)
print("Criação de tabelas concluída.")
