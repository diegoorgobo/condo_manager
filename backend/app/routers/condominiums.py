# backend/app/routers/condominiums.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import database, models, auth, schemas

router = APIRouter(prefix="/condominiums", tags=["Condominium Management"])

get_db = database.get_db

@router.get("/", response_model=list[schemas.ThemeConfigModel], summary="Listar Condomínios disponíveis")
def list_available_condos(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Retorna o condomínio ao qual o usuário logado pertence."""
    
    # Filtra pelo ID do condomínio do usuário logado
    condos = db.query(models.Condominium).filter(
        models.Condominium.id == current_user.condominium_id
    ).all()

    # O código espera uma lista (mesmo que com um item), então retornamos 'condos'
    return condos

@router.post("/", response_model=schemas.CondominiumResponse, status_code=status.HTTP_201_CREATED)
def create_condominium(
    condo: schemas.CondominiumCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user) # Protegido por autenticação
):
    """Cria um novo registro de condomínio (necessário antes de criar usuários/vistorias)."""
    
    # 1. Checa se o CNPJ já existe
    db_condo = db.query(models.Condominium).filter(models.Condominium.cnpj == condo.cnpj).first()
    if db_condo:
        raise HTTPException(status_code=400, detail="CNPJ já registrado.")
    
    # 2. Cria a instância do modelo
    db_condo = models.Condominium(**condo.model_dump())
    
    db.add(db_condo)
    db.commit()
    db.refresh(db_condo)
    return db_condo

@router.get("/{condominium_id}", response_model=schemas.CondominiumResponse)
def get_condominium(
    condominium_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Busca detalhes de um condomínio específico."""
    db_condo = db.query(models.Condominium).filter(models.Condominium.id == condominium_id).first()
    if db_condo is None:
        raise HTTPException(status_code=404, detail="Condomínio não encontrado")
    
    return db_condo
