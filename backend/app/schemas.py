from pydantic import BaseModel, ConfigDict, EmailStr
from typing import List, Optional
from datetime import datetime, date
from typing import Optional
from datetime import date


class CondominiumResponse(BaseModel):
    id: int
    name: str
    cnpj: str
    address: Optional[str] = None
    
    # Campos para White Labeling
    logo_url: Optional[str] = None
    primary_color: Optional[str] = "#1A1A1A" # Cor primária padrão (Dark Grey)
    secondary_color: Optional[str] = "#007BFF" # Cor secundária padrão (Blue)
    tertiary_color: Optional[str] = "#FFFFFF" # Cor terciária (Branco)

    model_config = ConfigDict(from_attributes=True)
# --- Configuração Base ---
class BaseConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)

# --- User ---
class UserBase(BaseConfig):
    email: EmailStr
    name: str
    phone: Optional[str] = None
    role: str
    condominium_id: Optional[int] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    photo_url: Optional[str] = None

class UserUpdate(BaseConfig):
    name: Optional[str] = None
    phone: Optional[str] = None
    photo_url: Optional[str] = None
    role: Optional[str] = None
    condominium_id: Optional[int] = None

# --- Token ---
class Token(BaseModel):
    access_token: str
    token_type: str

# --- Condominium ---
class CondominiumBase(BaseConfig):
    name: str
    cnpj: str
    primary_color: Optional[str] = "0xFF000000"
    logo_url: Optional[str] = None

class CondominiumCreate(CondominiumBase):
    pass

class CondominiumResponse(CondominiumBase):
    id: int
    # Incluir outros campos conforme necessidade

# --- Inspection Item ---
class InspectionItemCreate(BaseConfig):
    name: str
    status: str # Bom, Regular, Ruim
    observation: Optional[str] = None
    # photo_url será tratado no upload

class InspectionItemResponse(InspectionItemCreate):
    id: int
    photo_url: Optional[str] = None

# --- Inspection ---
class InspectionCreate(BaseConfig):
    condominium_id: int
    is_custom: bool = False
    ia_analysis: Optional[str] = None
    items: List[InspectionItemCreate]

class InspectionResponse(BaseConfig):
    id: int
    date: datetime
    status: str
    surveyor_id: int
    items: List[InspectionItemResponse]
    
# --- Work Order ---
class WorkOrderCreate(BaseConfig):
    title: str
    description: str
    item_id: Optional[int] = None
    provider_id: Optional[int] = None

class SimpleCondo(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

# A CLASSE DE RESPOSTA (CORREÇÃO DA INDENTAÇÃO E NOME)
class WorkOrderResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    created_at: datetime
    closed_at: Optional[datetime] = None
    condominium: Optional[SimpleCondo] = None
    item_id: Optional[int] = None
    provider_id: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)

class UserMessage(BaseModel):
    # Schema simplificado para exibir o autor da mensagem
    id: int
    name: str

    class Config:
        orm_mode = True

class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase):
    pass # Apenas o conteúdo é necessário na criação

class MessageResponse(MessageBase):
    id: int
    work_order_id: int
    user_id: int
    created_at: datetime
    # Adicionamos o autor para que o frontend saiba quem enviou
    user: UserMessage # ⬅️ NOVO: Incluir o nome do autor

    class Config:
        orm_mode = True

class MaintenanceAlertBase(BaseModel):
    type: str # Ex: "Seguro Predial", "Limpeza Caixa D'água"
    due_date: date # ⬅️ Campo de data do vencimento (YYYY-MM-DD)
    period_years: int # 1 a 10 anos (para referência)
    condominium_id: int

class MaintenanceAlertCreate(MaintenanceAlertBase):
    pass

class MaintenanceAlertResponse(MaintenanceAlertBase):
    id: int
    alert_sent_1month: bool
    alert_sent_1week: bool
    alert_sent_1day: bool

    model_config = ConfigDict(from_attributes=True)

class CondominiumBase(BaseModel):
    name: str
    cnpj: str
    address: Optional[str] = None
    cleaning_company: Optional[str] = None
    elevator_maintenance: Optional[str] = None
    
    # Cores/Logo (Para o White Labeling)
    logo_url: Optional[str] = None
    primary_color: Optional[str] = "#1A3D6B" # Padrão
    secondary_color: Optional[str] = "#4CAF50"

# Usamos este schema para a entrada de dados (POST/PUT)
class CondominiumCreate(CondominiumBase):
    pass







