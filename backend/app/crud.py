from sqlalchemy.orm import Session
from . import models, schemas, auth
from datetime import datetime
from typing import Optional, List

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        name=user.name,
        password_hash=hashed_password,
        role=user.role,
        phone=user.phone,
        condominium_id=user.condominium_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_inspection(db: Session, inspection: schemas.InspectionCreate, user_id: int):
    # 1. Cria a Inspection (db_inspection)
    # ... (código existente) ...

    # 2. Loop de Processamento dos Itens
    for item in inspection.items:
        db_item = models.InspectionItem(
            inspection_id=db_inspection.id,
            
            # 🚨 CORREÇÃO CRÍTICA: Pegar o ID do Condomínio da Inspection principal
            condominium_id=db_inspection.condominium_id, 
            
            name=item.name,
            status=item.status,
            observation=item.observation
        )
        db.add(db_item)
    
    db.commit()
    return db_inspection
    
    # Adiciona os itens da vistoria
    for item in inspection.items:
        db_item = models.InspectionItem(
            inspection_id=db_inspection.id,
            name=item.name,
            status=item.status,
            observation=item.observation
            # photo_url deve ser atualizado separadamente ou logica complexa de upload aqui
        )
        db.add(db_item)
    
    db.commit()
    return db_inspection

def create_work_order(db: Session, title: str, description: str, item_id: int, provider_id: Optional[int] = None):
    
    # 1. Checagem Defensiva (Embora item_id seja int, é bom garantir)
    if not item_id:
        # Se a OS não tiver item_id, não pode ser criada (Regra de Negócio)
        print("ALERTA: Tentativa de criar OS sem item_id. Abortando.")
        return None 
        
    # 2. Criação do Objeto
    db_wo = models.WorkOrder(
        title=title,
        description=description,
        item_id=item_id,
        # O provider_id é opcional, mas se for passado como None, deve ser aceito pelo DB.
        provider_id=provider_id, 
        status="Pendente",
        created_at=datetime.utcnow()
    )
    
    # 3. Inserção
    try:
        db.add(db_wo)
        db.flush() # Tenta inserir. Se falhar, a exceção ocorre aqui.
        print(f"SUCESSO: Criada OS ID {db_wo.id} para item {item_id}.")
        return db_wo
    except Exception as e:
        # Este bloco captura o erro de Foreign Key Violation (o real problema)
        db.rollback() 
        print(f"ERRO CRÍTICO NA CRIAÇÃO DA OS: {e}")
        # Lança uma exceção para o FastAPI retornar um erro 500 (temporariamente)
        raise e



