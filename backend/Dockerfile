# 1. Usar imagem base do Python 3.11 (versão leve 'slim')
FROM python:3.10-slim

# 2. Definir diretório de trabalho no container
WORKDIR /code

# 3. Variáveis de ambiente para evitar arquivos .pyc e logs em buffer
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 4. Instalar dependências do sistema necessárias para pypdf e postgres
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. Copiar e instalar requirements
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 6. Copiar o código da aplicação
COPY ./app /code/app

# 7. Comando para iniciar o servidor
# O Render injeta a variável $PORT automaticamente. 
# Se rodar local, usa a porta 8000.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
CMD ["sh", "-c", "python app/prestart.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

