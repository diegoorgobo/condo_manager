# backend/app/routers/alerts.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date, timedelta # ⬅️ Importar timedelta
from .. import database, models, auth, schemas
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/alerts", tags=["Maintenance Alerts & Scheduler"])

get_db = database.get_db

# --- ROTA 1: CRIAÇÃO (Chamada pelo App Flutter) ---
@router.post("/", response_model=schemas.MaintenanceAlertResponse, status_code=201, summary="Cadastrar novo Aviso de Manutenção")
def create_maintenance_alert(
    alert: schemas.MaintenanceAlertCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Permite cadastrar um novo prazo de manutenção (seguro, PPCI, etc.)."""
    
    # 1. Autorização: Garante que o usuário logado só crie alertas para seu condomínio
    if current_user.condominium_id != alert.condominium_id:
        raise HTTPException(status_code=403, detail="Acesso negado: ID de condomínio inválido para este usuário.")

    # 2. Cria o registro no banco
    db_alert = models.MaintenanceAlert(**alert.model_dump())
    
    # 3. TRATAMENTO DE ERRO CRÍTICO
    try:
        db.add(db_alert)
        db.commit() # 🚨 O CRASH DE FK OCORRE AQUI
        db.refresh(db_alert)
    except IntegrityError as e:
        db.rollback() 
        # A mensagem de erro que o Render esconde é capturada e retornada de forma limpa.
        raise HTTPException(
            status_code=400, 
            detail="Falha de integridade: Verifique se o Condomínio ID existe."
        )
        
    return db_alert


# --- ROTA 2: SCHEDULER (Chamada pelo CRON JOB do Render) ---
@router.get("/run-scheduler", summary="Executar Verificação Diária de Vencimentos", include_in_schema=False)
def run_daily_scheduler(db: Session = Depends(get_db)):
    """
    Esta rota é chamada diariamente por um Cron Job externo.
    Verifica se os prazos de manutenção atingiram 30, 7 ou 1 dia de antecedência.
    """
    
    today = date.today()
    
    # 1. Buscar todos os alertas que AINDA NÃO VENCERAM e que NÃO FORAM FINALIZADOS.
    # Assumimos que o due_date é sempre no futuro.
    alerts = db.query(models.MaintenanceAlert).filter(
        models.MaintenanceAlert.due_date >= today
    ).all()
    
    updated_alerts = []

    for alert in alerts:
        # Calcular a diferença em dias entre o vencimento e hoje
        days_to_due = (alert.due_date - today).days
        
        updated = False
        
        # 🚨 AVALIAÇÃO DE PRAZOS (Usamos <= para garantir que o alerta dispare se for hoje ou menos)

        # 1. Alerta de 1 Mês (30 dias)
        if days_to_due <= 30 and not alert.alert_sent_1month:
            alert.alert_sent_1month = True
            updated = True
        
        # 2. Alerta de 1 Semana (7 dias)
        if days_to_due <= 7 and not alert.alert_sent_1week:
            alert.alert_sent_1week = True
            updated = True
            
        # 3. Alerta de 1 Dia
        if days_to_due <= 1 and not alert.alert_sent_1day:
            alert.alert_sent_1day = True
            updated = True

        if updated:
            db.add(alert)
            updated_alerts.append(alert.id)
            
    db.commit()
    
    return {"status": "Scheduler finished", "alerts_dispatched": len(updated_alerts), "updated_ids": updated_alerts}

@router.get(
    "/list/{condominium_id}",
    response_model=list[schemas.MaintenanceAlertResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar Alertas de Manutenção por Condomínio"
)
def list_maintenance_alerts(
    condominium_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Busca todos os alertas de manutenção ativos para um condomínio específico.
    """
    
    # 🚨 Adicionar Lógica de Segurança
    # Garante que o usuário logado só possa ver alertas do seu próprio condomínio.
    if current_user.condominium_id != condominium_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Não autorizado a acessar alertas deste condomínio."
        )
        
    # Busca os alertas no banco de dados.
    alerts = db.query(models.MaintenanceAlert).filter(
        models.MaintenanceAlert.condominium_id == condominium_id
    ).order_by(models.MaintenanceAlert.due_date).all()
    
    # Retorna a lista, que será serializada pelo Pydantic (response_model)
    return alerts
