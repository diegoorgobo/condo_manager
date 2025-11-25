# Em backend/app/routers/condominium.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
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
