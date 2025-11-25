from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError
# Importa componentes internos (Corrigido para evitar repetição e conflito)
from .. import database, models, auth, schemas 

router = APIRouter(prefix="/work-orders", tags=["Work Orders"])

# Schema simples para atualizar status (recebe a nova situação)
class StatusUpdateSchema(BaseModel):
    status: str # Ex: "Em Andamento", "Concluído"
    
class WorkOrderPhotoUpdateSchema(BaseModel):
    photo_after_url: Optional[str] = None
    status: str = "Concluído"
    model_config = ConfigDict(from_attributes=True) # Pydantic v2

# Dependência para o banco de dados
get_db = database.get_db

### ROTAS DE BUSCA E GESTÃO ###

@router.get("/", response_model=List[schemas.WorkOrderResponse], summary="Listar Ordens de Serviço por Condomínio")
async def list_work_orders(
    condominium_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # 🚨 CÓDIGO FINAL DE DEBUG: RETORNA TUDO E IGNORA O FILTRO E O JOIN
    orders = db.query(models.WorkOrder).all() 
    # Isso deve retornar os 18 registros que você viu no Supabase.
    
    try:
        # A serialização Pydantic acontece automaticamente no retorno. 
        # Envolvemos em um bloco try para capturar o erro que a está impedindo.
        return orders 
    except Exception as e:
        # Este print mostrará o campo exato que está inválido
        print(f"ERRO FATAL DE SERIALIZAÇÃO: {e}") 
        raise HTTPException(
            status_code=500, 
            detail=f"Falha de Serialização: Campo inválido encontrado no banco. Trace: {e}"
        )

@router.post("/{order_id}/status", response_model=schemas.WorkOrderResponse, summary="Atualizar Status da OS")
async def update_wo_status(
    order_id: int,
    data: StatusUpdateSchema,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user) # Rota Protegida!
):
    """Atualiza o status para Pendente, Em Andamento ou Concluído (sem foto)."""
    db_wo = db.query(models.WorkOrder).filter(models.WorkOrder.id == order_id).first()
    if not db_wo:
        raise HTTPException(status_code=404, detail="Ordem de Serviço não encontrada")

    db_wo.status = data.status.capitalize() # <-- Otimização: Padroniza o status para (Pendente/Em Andamento/Concluído)
    
    # Se for concluído, marca a data de fechamento
    if data.status.lower() == "concluído" and not db_wo.closed_at:
        db_wo.closed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_wo)
    return db_wo

@router.post("/{order_id}/close", response_model=schemas.WorkOrderResponse, summary="Concluir OS com Foto")
async def close_wo_with_photo(
    order_id: int,
    data: WorkOrderPhotoUpdateSchema,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user) # Rota Protegida!
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
    
    # 🚨 O BLOCO CRÍTICO: db.add() e db.commit() devem estar no try.
    try:
        db.add(db_wo)
        db.commit() # <--- A FALHA DE SQL OCORRE EXATAMENTE AQUI
        db.refresh(db_wo)
    except IntegrityError as e:
        # Se falhar (por exemplo, Foreign Key inválida)
        db.rollback() 
        
        # 🔔 Este log VAI aparecer no Uvicorn e nos dirá o nome da restrição quebrada.
        print(f"ERRO SQL INTEGRITY FAILED (ROLLBACK): {e.orig}") 
        
        raise HTTPException(
            status_code=400, 
            detail="Falha ao criar a OS: Verifique se todos os IDs (Condomínio/Item/Provider) existem."
        )

    return db_wo

@router.get("/{work_order_id}/messages", response_model=List[schemas.MessageResponse], summary="Listar Mensagens de uma OS")
def list_messages(
    work_order_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # 1. Verificar se a OS existe e se o usuário tem acesso (Simplificado: Apenas verifica se a OS existe)
    work_order = db.query(models.WorkOrder).filter(models.WorkOrder.id == work_order_id).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="Ordem de Serviço não encontrada")

    # 2. Carregar todas as mensagens ordenadas por data
    # Usa options(joinedload(models.Message.user)) para carregar o autor (User) em uma única query (otimização)
    messages = db.query(models.Message).options(
        joinedload(models.Message.user)
    ).filter(
        models.Message.work_order_id == work_order_id
    ).order_by(
        models.Message.created_at
    ).all()
    
    return messages


# --- NOVO: Endpoint para Enviar Mensagem ---
@router.post("/{work_order_id}/messages", response_model=schemas.MessageResponse, status_code=201, summary="Enviar uma nova Mensagem para a OS")
def create_message(
    work_order_id: int,
    message: schemas.MessageCreate, # O Pydantic valida o corpo da requisição (apenas 'content')
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # 1. Verificar se a OS existe
    work_order = db.query(models.WorkOrder).filter(models.WorkOrder.id == work_order_id).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="Ordem de Serviço não encontrada")

    # 2. Criar e salvar a mensagem
    db_message = models.Message(
        work_order_id=work_order_id,
        user_id=current_user.id,
        content=message.content,
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    # 3. Recarregar o autor para inclusão no response_model (otimização)
    db_message.user # Simplesmente acessa a propriedade para garantir que a relação foi carregada antes de serializar
    
    return db_message
