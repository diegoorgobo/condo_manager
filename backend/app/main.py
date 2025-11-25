from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from .routers import documents, financial, work_orders, condominiums, users
from .routers import documents, financial, work_orders, condominium

import json
# Importações internas
from . import models, schemas, crud, database, auth

# --- NOVAS IMPORTAÇÕES (ROUTERS) ---
# Importamos os arquivos que criamos nas pastas 'routers'
from .routers import documents, financial 
# -----------------------------------

# Cria tabelas no banco (apenas para dev)
#models.Base.metadata.create_all(bind=database.engine)
app.add_middleware(...) # CORS
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
app.include_router(work_orders.router)
app.include_router(condominiums.router)
app.include_router(users.router)
app.include_router(condominium.router)
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
    # 1. Parse do JSON dos itens
    try:
        items_data = json.loads(items_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Formato JSON inválido para itens da vistoria.")

    # 2. Criação da Vistoria base
    db_inspection = models.Inspection(
        surveyor_id=current_user.id,
        condominium_id=condominium_id,
        is_custom=is_custom,
        ia_analysis=ia_analysis
    )
    db.add(db_inspection)
    db.flush() # Força o DB a gerar o ID da vistoria

    # 3. Processamento dos Itens e Geração da OS
    for item in items_data:
        
        # Simulação de upload de foto (substituir por lógica real de storage)
        photo_url = "url_simulada_storage" 
        
        # Normaliza o status para evitar erros de Case Sensitivity
        status_item = item.get('status', '').lower()
        
        # Salva o Item da Vistoria
        db_item = models.InspectionItem(
            inspection_id=db_inspection.id,
            name=item.get('name'),
            status=status_item, # Salva o status normalizado
            observation=item.get('observation'),
            photo_url=photo_url
        )
        db.add(db_item)
        db.flush() # Garante que o ID do item é gerado para a OS
        
        # 4. GERAÇÃO DA ORDEM DE SERVIÇO (OS) SE NECESSÁRIO
        # Condição: status deve ser "ruim" (agora em minúsculo)
        if status_item == 'ruim':
            print("--- DEBUG (OS): Condição 'ruim' Atingida. Tentando criar OS. ---") 
            
            # 🚨 Chamada para a criação da OS no crud.py
            crud.create_work_order(
                db=db,
                title=f"Ação Imediata: {item.get('name')}",
                description=f"Item {item.get('name')} avaliado como Ruim na vistoria ID {db_inspection.id}.",
                item_id=db_item.id # Vincula a OS ao item de vistoria
            )

    db.commit() # Salva todas as alterações (vistoria, itens, OSs)
    
    return {"status": "success", "inspection_id": db_inspection.id, "message": "Vistoria e Ordens de Serviço (se necessário) criadas com sucesso."}



