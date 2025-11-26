from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, Float, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Condominium(Base):
    __tablename__ = "condominiums"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    cnpj = Column(String, unique=True)
    address = Column(String)
    cleaning_company = Column(String, nullable=True)
    elevator_maintenance = Column(String, nullable=True)
    
    # Personalização do App (White Label)
    logo_url = Column(String, nullable=True)
    primary_color = Column(String, default="0xFF000000") # Hex Code ou ARGB
    secondary_color = Column(String, default="0xFFFFFFFF")
    
    users = relationship("User", back_populates="condominium")
    inspections = relationship("Inspection", back_populates="condominium")
    maintenance_alerts = relationship("MaintenanceAlert", back_populates="condominium")
    financials = relationship("FinancialRecord", back_populates="condominium")
    documents = relationship("Document", back_populates="condominium")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    phone = Column(String)
    photo_url = Column(String, nullable=True)
    role = Column(String) # Proprietário, Programador, Gerente, Administrativo, Síndico, Vistoriador
    
    condominium_id = Column(Integer, ForeignKey("condominiums.id"), nullable=True)
    condominium = relationship("Condominium", back_populates="users")
    
    inspections = relationship("Inspection", back_populates="surveyor")
    sent_messages = relationship("ChatMessage", back_populates="sender")

class ServiceProvider(Base):
    __tablename__ = "service_providers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    profession = Column(String)
    cnpj = Column(String)
    
    work_orders = relationship("WorkOrder", back_populates="provider")

class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="Pendente") # Pendente, Concluída
    ia_analysis = Column(Text, nullable=True)
    is_custom = Column(Boolean, default=False)
    
    surveyor_id = Column(Integer, ForeignKey("users.id"))
    condominium_id = Column(Integer, ForeignKey("condominiums.id"))
    
    surveyor = relationship("User", back_populates="inspections")
    condominium = relationship("Condominium", back_populates="inspections")
    items = relationship("InspectionItem", back_populates="inspection", cascade="all, delete-orphan")
    messages = relationship("ChatMessage", back_populates="inspection")

class InspectionItem(Base):
    __tablename__ = "inspection_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String) 
    status = Column(String) 
    photo_url = Column(String, nullable=True)
    observation = Column(Text, nullable=True)
    
    inspection_id = Column(Integer, ForeignKey("inspections.id"))
    inspection = relationship("Inspection", back_populates="items")
    
    # 🚨 CRÍTICO: Define o relacionamento com a OS (uselist=False pois um item só pode ter uma OS)
    work_order = relationship("WorkOrder", uselist=False, back_populates="item", cascade="all, delete-orphan")

class WorkOrder(Base):
    __tablename__ = "work_orders"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)
    status = Column(String, default="Pendente")
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    
    photo_before_url = Column(String, nullable=True)
    photo_after_url = Column(String, nullable=True)
    
    item_id = Column(Integer, ForeignKey("inspection_items.id"), nullable=True)
    provider_id = Column(Integer, ForeignKey("service_providers.id"), nullable=True)
    
    # 🚨 CRÍTICO: Define o relacionamento com o InspectionItem
    item = relationship("InspectionItem", back_populates="work_order") 
    provider = relationship("ServiceProvider", back_populates="work_orders")
    messages = relationship("Message", back_populates="work_order", cascade="all, delete-orphan") # ⬅️ NOVO: Relacionamento para carregar mensagens

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    inspection_id = Column(Integer, ForeignKey("inspections.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    
    inspection = relationship("Inspection", back_populates="messages")
    sender = relationship("User", back_populates="sent_messages")

class MaintenanceAlert(Base):
    __tablename__ = "maintenance_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String) # Limpeza Caixa d'água, PPCI, etc.
    due_date = Column(Date)
    alert_sent_1month = Column(Boolean, default=False)
    alert_sent_1week = Column(Boolean, default=False)
    alert_sent_1day = Column(Boolean, default=False)
    
    condominium_id = Column(Integer, ForeignKey("condominiums.id"))
    condominium = relationship("Condominium", back_populates="maintenance_alerts")

class FinancialRecord(Base):
    __tablename__ = "financial_records"
    
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    amount = Column(Float)
    type = Column(String) # Receita, Despesa
    date = Column(Date)
    
    condominium_id = Column(Integer, ForeignKey("condominiums.id"))
    condominium = relationship("Condominium", back_populates="financials")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    file_path = Column(String)
    content_text = Column(Text) # Texto extraído para IA buscar
    
    condominium_id = Column(Integer, ForeignKey("condominiums.id"))
    condominium = relationship("Condominium", back_populates="documents")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True) # <-- CORRIGIDO AQUI
    work_order_id = Column(Integer, ForeignKey("work_orders.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    work_order = relationship("WorkOrder", back_populates="messages")
    user = relationship("User") # Relacionamento com o usuário que enviou

class MaintenanceAlert(Base):
    __tablename__ = "maintenance_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String) 
    due_date = Column(Date)
    
    period_years = Column(Integer) # ⬅️ COLUNA FALTANTE ADICIONADA
    
    alert_sent_1month = Column(Boolean, default=False)
    alert_sent_1week = Column(Boolean, default=False)
    alert_sent_1day = Column(Boolean, default=False)
    
    condominium_id = Column(Integer, ForeignKey("condominiums.id"))
    condominium = relationship("Condominium", back_populates="maintenance_alerts")



