from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, case, text, or_
from sqlalchemy.orm import joinedload, outerjoin
# Importa componentes internos
from .. import database, models, auth, schemas 

router = APIRouter(prefix="/work-orders", tags=["Work Orders"])

# Schema simples para atualizar status (recebe a nova situação)
class StatusUpdateSchema(BaseModel):
    status: str 
    
class WorkOrderPhotoUpdateSchema(BaseModel):
    photo_after_url: Optional[str] = None
    status: str = "Concluído"
    model_config = ConfigDict(from_attributes=True)

# Dependência para o banco de dados
get_db = database.get_db

### ROTAS DE BUSCA E GESTÃO ###

@router.get("/", response_model=List[schemas.WorkOrderResponse], summary="Listar Ordens de Serviço com Filtros")
def list_work_orders(
    condominium_id: Optional[int] = None,
    sort_by: str = "status",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Filtra as OSs pelo condomínio e ordena por status ou data."""
    
    # 1. CRIAÇÃO DA QUERY BASE E EAGER LOADING (Carrega o nome do condomínio)
    query = db.query(models.WorkOrder)

    # FIX CRÍTICO: Usa OUTERJOIN para incluir OSs manuais e JOINEDLOAD para carregar o nome
    query = query.outerjoin(models.InspectionItem).options(
        joinedload(models.WorkOrder.item).joinedload(models.InspectionItem.condominium)
    )

    # 2. AUTORIZAÇÃO E FILTRAGEM (Restaurando a lógica de segurança)
    if current_user.role != 'Programador':
        user_condo_id = current_user.condominium_id
        
        if user_condo_id is not None:
            query = query.filter(
                or_(
                    # 1. OSs vinculadas ao condomínio do usuário logado
                    models.InspectionItem.condominium_id == user_condo_id,
                    
                    # 2. OSs sem vínculo (manuais)
                    models.WorkOrder.item_id.is_(None)
                )
            )
        else:
            return [] 

    # 3. FILTRAGEM POR QUERY PARAMETER
    if condominium_id:
        query = query.filter(models.InspectionItem.condominium_id == condominium_id)

    # 4. ORDENAÇÃO
    if sort_by == 'status':
        status_order = case(
            (models.WorkOrder.status == 'Pendente', 1),
            (models.WorkOrder.status == 'Em Andamento', 2),
            (models.WorkOrder.status == 'Concluído', 3),
            else_=4
        )
        query = query.order_by(status_order, models.WorkOrder.created_at.desc())
    else:
        query = query.order_by(models.WorkOrder.created_at.desc())

    orders = query.all()
    return orders

@router.post("/{order_id}/close", response_model=schemas.WorkOrderResponse, summary="Concluir OS com Foto")
async def close_wo_with_photo(
    order_id: int,
    data: WorkOrderPhotoUpdateSchema,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Finaliza a OS, registrando a foto do serviço pronto."""
    db_wo = db.query(models.WorkOrder).filter(models.WorkOrder.id == order_id).first()
    if not db_wo:
        raise HTTPException(status_code=404, detail="Ordem de Serviço não encontrada")

    db_wo.status = "Concluído"
    db_wo.photo_after_url = data.photo_after_url
    
    if not db_wo.closed_at:
        db_wo.closed_at = datetime.utcnow()
        
    db.commit()
    db.refresh(db_wo)
    return db_wo

@router.post("/", response_model=schemas.WorkOrderResponse, status_code=201, summary="Criar Ordem de Serviço Manualmente")
async def create_work_order(
    work_order: schemas.WorkOrderCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Cria uma nova OS a partir de uma demanda administrativa."""
    
    db_wo = models.WorkOrder(**work_order.model_dump())
    
    try:
        db.add(db_wo)
        db.commit()
        db.refresh(db_wo)
    except IntegrityError as e:
        db.rollback()
        print(f"ERRO SQL INTEGRITY FAILED (ROLLBACK): {e.orig}") 
        raise HTTPException(
            status_code=400, 
            detail="Falha ao criar a OS: Verifique se todos os IDs (Condomínio/Item/Provider) existem."
        )

    return db_wo
