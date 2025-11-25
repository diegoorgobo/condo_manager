# backend/app/routers/users.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from .. import database, models, auth, schemas

router = APIRouter(prefix="/users", tags=["User Management"])
get_db = database.get_db

# --- Endpoint de Leitura Rápida ---
@router.get("/me", response_model=schemas.UserResponse, summary="Obter dados do usuário logado")
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    """Rota conveniente para o Frontend buscar seus próprios dados após o login."""
    return current_user

# --- PATCH Endpoint para VINCULAR CONDOMÍNIO (ID) ---
@router.patch("/{user_id}", response_model=schemas.UserResponse, summary="Atualizar dados parciais do usuário")
def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # 1. Autorização: Apenas o próprio usuário (ou um Admin) pode se atualizar
    if current_user.id != user_id and current_user.role not in ["Programador", "Administrativo"]:
         raise HTTPException(status_code=403, detail="Permissão negada para atualizar este usuário.")

    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    # 2. Desserializar e aplicar as alterações dinamicamente
    # O exclude_unset=True garante que apenas os campos enviados no JSON sejam alterados.
    update_data = user_update.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user
