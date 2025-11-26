from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, Float, Date
from sqlalchemy.orm import relationship, declarative_base # Garantir que o Base está sendo usado corretamente
from datetime import datetime
from .database import Base # Assumindo que Base é importado de .database

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
    primary_color = Column(String, default="#1A3D6B") # ⬅️ USANDO FORMATO HEX PARA CONSISTÊNCIA
    secondary_color = Column(String, default="#4CAF50")
    
    # Relações
    users = relationship("User", back_populates="condominium")
    inspections = relationship("Inspection", back_populates="condominium")
    inspection_items = relationship("InspectionItem", back_populates="condominium")
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
    role = Column(String) 
    
    condominium_id = Column(Integer, ForeignKey("condominiums.id"), nullable=True)
    condominium = relationship("Condominium", back_populates="users")
    
    inspections = relationship("Inspection", back_populates="surveyor")
    sent_messages = relationship("Message", back_populates="user") # ⬅️ CORRIGIDO: Referencia a classe Message

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
    status = Column(String, default="Pendente")
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

    # 🚨 ORDEM CORRIGIDA: id deve vir antes de outros campos, mas o order_by não é estrito
    id = Column(Integer, primary_key=True, index=True)
    condominium_id = Column(Integer, ForeignKey("condominiums.id"), nullable=True)
    name = Column(String)
    status = Column(String)
    photo_url = Column(String, nullable=True)
    observation = Column(Text, nullable=True)
    
    inspection_id = Column(Integer, ForeignKey("inspections.id"))
    inspection = relationship("Inspection", back_populates="items")
    condominium = relationship("Condominium", back_populates="inspection_items") # ⬅️ CORRIGIDO: back_populates
    
    # Define o relacionamento com a OS
    work_order = relationship("WorkOrder", uselist=False, back_populates="item", cascade="all, delete-orphan")

class WorkOrder(Base):
    __tablename__ = "work_orders"
    # 🚨 CORRIGIDO: Removido o argumento schema, que deve ser definido no create_db.py ou Alembic
    # __table_args__ = {'schema': 'public'} 
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    # ❌ ERRO DE SINTAXE: 'title' duplicado
    # title = Column(String)
    description = Column(Text)
    status = Column(String, default="Pendente")
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    
    photo_before_url = Column(String, nullable=True)
    photo_after_url = Column(String, nullable=True)
    
    item_id = Column(Integer, ForeignKey("inspection_items.id"), nullable=True)
    provider_id = Column(Integer, ForeignKey("service_providers.id"), nullable=True)
    
    # Define o relacionamento com o InspectionItem
    item = relationship("InspectionItem", back_populates="work_order") 
    provider = relationship("ServiceProvider", back_populates="work_orders")
    
    # 🚨 CORRIGIDO: Referencia a classe Message (definida abaixo)
    messages = relationship("Message", back_populates="work_order", cascade="all, delete-orphan") 

# 🚨 CLASSE CHAT MESSAGE (Mudar o nome para Message para evitar conflito com a nova Message)
class ChatMessage(Base): # Renomeado de ChatMessage para evitar conflito
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    inspection_id = Column(Integer, ForeignKey("inspections.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    
    inspection = relationship("Inspection", back_populates="messages")
    sender = relationship("User", back_populates="sent_messages")

class FinancialRecord(Base):
    __tablename__ = "financial_records"
    
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    amount = Column(Float)
    type = Column(String) 
    date = Column(Date)
    
    condominium_id = Column(Integer, ForeignKey("condominiums.id"))
    condominium = relationship("Condominium", back_populates="financials")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    file_path = Column(String)
    content_text = Column(Text)
    
    condominium_id = Column(Integer, ForeignKey("condominiums.id"))
    condominium = relationship("Condominium", back_populates="documents")

# 🚨 CLASSE MESSAGE (Mensagens vinculadas à OS)
class Message(Base):
    __tablename__ = "messages"
    
    # 🚨 CORREÇÃO: Removido autoincrement=True, que deve ser resolvido no CREATE TABLE (SERIAL)
    id = Column(Integer, primary_key=True) 
    work_order_id = Column(Integer, ForeignKey("work_orders.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos (Back_populates)
    work_order = relationship("WorkOrder", back_populates="messages")
    user = relationship("User", back_populates="sent_messages") # ⬅️ CORRIGIDO: back_populates

class MaintenanceAlert(Base):
    __tablename__ = "maintenance_alerts"
    
    # 🚨 FIX: Incluído extend_existing=True para evitar o erro de startup
    __table_args__ = {'extend_existing': True} 
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String)
    due_date = Column(Date)
    
    period_years = Column(Integer) # COLUNA ADICIONADA
    
    alert_sent_1month = Column(Boolean, default=False)
    alert_sent_1week = Column(Boolean, default=False)
    alert_sent_1day = Column(Boolean, default=False)
    
    condominium_id = Column(Integer, ForeignKey("condominiums.id"))
    condominium = relationship("Condominium", back_populates="maintenance_alerts")
