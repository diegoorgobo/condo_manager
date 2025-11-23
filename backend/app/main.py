from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
import json

# Importações internas
from . import models, schemas, crud, database, auth

# --- NOVAS IMPORTAÇÕES (ROUTERS) ---
# Importamos os arquivos que criamos nas pastas 'routers'
from .routers import documents, financial 
# -----------------------------------

# Cria tabelas no banco (apenas para dev)
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="CondoManager API")

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REGISTRO DOS ROUTERS ---
# É aqui que "ligamos" os novos módulos ao app principal
app.include_router(documents.router)
app.include_router(financial.router)
# ----------------------------


# --- ROTAS DE AUTENTICAÇÃO (Mantidas no main por simplicidade, ou movidas para auth.py) ---

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = crud.get_user_by_email(db, form_data.username)
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

# --- OUTRAS ROTAS ANTIGAS ---
# Se você tiver rotas soltas de Vistoria (upload) aqui, recomendo mover 
# para um arquivo routers/inspections.py futuramente para organizar, 
# mas se estiverem aqui, deixe-as abaixo.

@app.post("/inspections/upload")
async def create_inspection_with_files(
    condominium_id: int = Form(...),
    is_custom: bool = Form(...),
    ia_analysis: str = Form(""),
    items_json: str = Form(...),
    files: List[UploadFile] = File(None), 
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    # ... (Seu código existente de upload de vistoria) ...
    # Recomendo manter o código que já fizemos aqui ou mover para um router próprio.
    # Por segurança, vou omitir a repetição da lógica interna para não ficar longo,
    # mas mantenha a função que você já tinha!
    pass
