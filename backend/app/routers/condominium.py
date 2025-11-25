# Em backend/app/routers/condominium.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import database, models, auth, schemas # Importa componentes internos

router = APIRouter(prefix="/condominiums", tags=["Condominiums"])

get_db = database.get_db

@router.get("/{condominium_id}", response_model=schemas.CondominiumResponse, summary="Obter Configuração de Tema do Condomínio")
def get_condo_config(
    condominium_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Retorna os detalhes do condomínio, incluindo cores e URL do logo.
    Requer autenticação e verifica se o usuário pertence a este condomínio.
    """
    
    # 1. Busca o condomínio
    condo = db.query(models.Condominium).filter(
        models.Condominium.id == condominium_id
    ).first()

    if not condo:
        raise HTTPException(status_code=404, detail="Condomínio não encontrado.")
    
    # 2. Verifica a autorização (Obrigatório para segurança)
    if current_user.condominium_id != condominium_id:
        # Se for o Programador (que precisa ver todos), ignore a restrição
        if current_user.role != 'Programador':
             raise HTTPException(status_code=403, detail="Acesso negado.")

    return condo

@router.post("/", response_model=schemas.CondominiumResponse, status_code=201, summary="Criar um novo Condomínio")
def create_condominium(
    condominium: schemas.CondominiumCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Permite criar um novo condomínio (Funcionalidade restrita a perfis Admin/Programador)."""
    
    if current_user.role not in ['Programador', 'gerente']: # Restrição por Perfil
        raise HTTPException(status_code=403, detail="Apenas Programadores/Gerentes podem criar novos condomínios.")

    # Verifica se já existe pelo CNPJ
    if db.query(models.Condominium).filter(models.Condominium.cnpj == condominium.cnpj).first():
        raise HTTPException(status_code=400, detail="CNPJ já cadastrado.")

    db_condo = models.Condominium(**condominium.model_dump())
    
    db.add(db_condo)
    db.commit()
    db.refresh(db_condo)
    return db_condo

# --- ROTA 2: LISTAR TODOS OS CONDOMÍNIOS DO USUÁRIO ---
@router.get("/", response_model=List[schemas.CondominiumResponse], summary="Listar Condomínios Acessíveis")
def list_condominiums(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Lista todos os condomínios acessíveis.
    Programadores veem todos. Síndicos veem apenas o(s) dele(s).
    """
    
    if current_user.role == 'Programador':
        # Programador vê todos os condomínios
        condos = db.query(models.Condominium).all()
    else:
        # Usuários comuns veem apenas o condomínio ao qual estão vinculados
        condos = db.query(models.Condominium).filter(
            models.Condominium.id == current_user.condominium_id # Filtra pelo ID vinculado ao usuário
        ).all()

    return condos
