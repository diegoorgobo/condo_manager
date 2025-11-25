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
    
    # 1. Autorização: Garante que o usuário logado pode criar alertas para este condomínio
    if current_user.condominium_id != alert.condominium_id:
        raise HTTPException(status_code=403, detail="Você não pode cadastrar alertas para este condomínio.")

    # 2. Cria o registro no banco
    db_alert = models.MaintenanceAlert(**alert.model_dump())
    
    try:
        db.add(db_alert)
        db.commit() # 🚨 O CRASH OCORRE AQUI (IntegrityError ou FK Violation)
        db.refresh(db_alert)
    except IntegrityError as e:
        db.rollback()
        # Força o log do erro de integridade (Foreign Key)
        print(f"INTEGRITY ERROR: {e.orig}") 
        raise HTTPException(
            status_code=400, 
            detail="Falha de integridade: Certifique-se de que o Condomínio ID existe e de que os dados estão válidos."
        )
        
    return db_alert


# --- ROTA 2: SCHEDULER (Chamada pelo CRON JOB do Render) ---
@router.get("/run-scheduler", summary="Executar Verificação Diária de Vencimentos", include_in_schema=False)
def run_daily_scheduler(db: Session = Depends(get_db)):
    """
    Esta rota é chamada diariamente por um Cron Job externo.
    Não é exposta na documentação (include_in_schema=False).
    """
    
    today = date.today()
    
    # 1. Definir datas de alerta: 30 dias, 7 dias, 1 dia
    date_one_month = today + timedelta(days=30)
    date_one_week = today + timedelta(days=7)
    date_one_day = today + timedelta(days=1)
    
    updated_alerts = []

    # 2. Buscar alertas que estão próximos do vencimento
    alerts = db.query(models.MaintenanceAlert).filter(
        models.MaintenanceAlert.due_date.in_([date_one_month, date_one_week, date_one_day])
    ).all()
    
    for alert in alerts:
        # Lógica de atualização da flag 'alert_sent'
        
        updated = False
        
        # Alerta de 1 Mês (30 dias)
        if alert.due_date == date_one_month and not alert.alert_sent_1month:
            alert.alert_sent_1month = True
            updated = True
        
        # Alerta de 1 Semana (7 dias)
        if alert.due_date == date_one_week and not alert.alert_sent_1week:
            alert.alert_sent_1week = True
            updated = True
            
        # Alerta de 1 Dia (1 dia)
        if alert.due_date == date_one_day and not alert.alert_sent_1day:
            alert.alert_sent_1day = True
            updated = True

        if updated:
            db.add(alert)
            updated_alerts.append(alert.id)
            
    db.commit()
    
    return {"status": "Scheduler finished", "alerts_dispatched": len(updated_alerts), "updated_ids": updated_alerts}
