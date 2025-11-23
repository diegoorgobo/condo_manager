import os
import uvicorn
import json
import uuid
from datetime import datetime, date, timedelta
from typing import Optional, List, Literal

from fastapi import FastAPI, Depends, HTTPException, status, Body, Query, UploadFile
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, case

from jose import JWTError, jwt
from passlib.context import CryptContext
import google.generativeai as genai
from supabase import create_client, Client

import models
import database

# --- Configuração de Ambiente ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY", "CHAVE_DEBUG_LOCAL")

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    gemini_model = None

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

models.Base.metadata.create_all(bind=database.engine)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Schemas ---
class Token(BaseModel): access_token: str; token_type: str
class UserResponse(BaseModel):
    usuario_id: int; nome: str; email: str; permissao: str
    class Config: orm_mode = True
class GoogleToken(BaseModel): token: str
class FotoCreate(BaseModel): url_foto: str; descricao_foto: Optional[str] = None
class ItemVistoriadoCreate(BaseModel):
    categoria_item: str; nome_especifico_item: str; status_item: str; descricao_detalhada: Optional[str] = None; fotos: List[FotoCreate] = []
class VistoriaCreate(BaseModel): condominio_id: int; observacoes_gerais: Optional[str] = None; itens: List[ItemVistoriadoCreate]
class VistoriaResponse(BaseModel):
    vistoria_id: int; status_vistoria: str; data_inicio: datetime
    class Config: orm_mode = True
class ChatMessageCreate(BaseModel): conteudo_texto: str
class ChatMessageResponse(BaseModel):
    mensagem_id: int; remetente: UserResponse; conteudo_texto: str; data_envio: datetime
    class Config: orm_mode = True
class IAPergunta(BaseModel): condominio_id: int; pergunta_texto: str
class CondominioCreate(BaseModel): nome_fantasia: str; cnpj: str; endereco_completo: Optional[str] = None
class CondominioResponse(BaseModel): condominio_id: int; nome_fantasia: str; class Config: orm_mode = True
class UserApprove(BaseModel): permissao: Literal["SINDICO", "VISTORIADOR", "ADMINISTRATIVO"]; condominio_id: int
class ManutencaoResponse(BaseModel):
    tarefa_id: int; tipo_tarefa: str; status_tarefa: str; data_proximo_vencimento: Optional[date]; detalhes_agendamento_semanal: Optional[str]; data_ultima_execucao: Optional[date]
    class Config: orm_mode = True
class FinanceiroDashboardResponse(BaseModel): total_receitas: float; total_despesas: float; lucratividade: float; total_pendente: float

# --- Helpers ---
def verify_password(plain, hashed): return pwd_context.verify(plain, hashed)
def get_password_hash(password): return pwd_context.hash(password)
def create_access_token(data: dict):
    to_encode = data.copy(); expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire}); return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try: payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]); email: str = payload.get("sub")
    except JWTError: raise HTTPException(status_code=401, detail="Credenciais inválidas")
    user = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if user is None: raise HTTPException(status_code=401, detail="Usuário não encontrado")
    return user

def get_user_with_permission(required_permission: str | List[str]):
    async def permission_checker(current_user: UserResponse = Depends(get_current_user)):
        if isinstance(required_permission, str): required_permissions = [required_permission]
        else: required_permissions = required_permission
        if "ADMINISTRADOR" in required_permissions or "PROPRIETARIO" in required_permissions:
            if current_user.permissao in ["ADMINISTRADOR", "PROPRIETARIO"]: return current_user
        if current_user.permissao not in required_permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Acesso restrito.")
        return current_user
    return permission_checker

# --- APP ---
app = FastAPI()

@app.get("/")
def read_root(): return {"status": "online"}

@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.Usuario).filter(models.Usuario.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hash_senha):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    return {"access_token": create_access_token(data={"sub": user.email, "permissao": user.permissao}), "token_type": "bearer"}

@app.post("/auth/google", response_model=Token)
async def auth_google(google_token: GoogleToken, db: Session = Depends(get_db)):
    if google_token.token != "token_valido_simulado_pelo_flutter":
        raise HTTPException(status_code=401, detail="Token inválido")
    email = "novo.usuario@gmail.com" # Simulado
    user = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if not user:
        user = models.Usuario(email=email, nome="Usuário Google", hash_senha=get_password_hash(""), permissao="PENDENTE")
        db.add(user); db.commit(); db.refresh(user)
    return {"access_token": create_access_token(data={"sub": user.email, "permissao": user.permissao}), "token_type": "bearer"}

@app.get("/me", response_model=UserResponse)
async def read_users_me(current_user: UserResponse = Depends(get_current_user)): return current_user

@app.post("/upload")
async def upload_file(file: UploadFile):
    if not supabase: raise HTTPException(status_code=500, detail="Storage não configurado")
    content = await file.read(); filename = f"{uuid.uuid4()}_{file.filename}"
    supabase.storage.from_("arquivos").upload(path=filename, file=content, file_options={"content-type": file.content_type})
    return {"url": supabase.storage.from_("arquivos").get_public_url(filename)}

# --- ADMIN ---
@app.get("/admin/usuarios", response_model=List[UserResponse])
async def admin_list_users(user: UserResponse = Depends(get_user_with_permission(["ADMINISTRADOR", "PROPRIETARIO"])), db: Session = Depends(get_db)):
    return db.query(models.Usuario).all()

@app.post("/admin/usuarios/{usuario_id}/aprovar")
async def admin_approve(usuario_id: int, data: UserApprove, user: UserResponse = Depends(get_user_with_permission(["ADMINISTRADOR", "PROPRIETARIO"])), db: Session = Depends(get_db)):
    user_to_approve = db.query(models.Usuario).filter(models.Usuario.usuario_id == usuario_id).first()
    if not user_to_approve: raise HTTPException(404, "Usuário não encontrado")
    condominio = db.query(models.Condominio).filter(models.Condominio.condominio_id == data.condominio_id).first()
    user_to_approve.permissao = data.permissao
    user_to_approve.condominios.append(condominio)
    db.commit()
    return {"message": "Aprovado"}

@app.post("/admin/condominios", response_model=CondominioResponse)
async def create_condo(data: CondominioCreate, user: UserResponse = Depends(get_user_with_permission(["ADMINISTRADOR", "PROPRIETARIO"])), db: Session = Depends(get_db)):
    condo = models.Condominio(**data.dict())
    db.add(condo); db.commit(); db.refresh(condo)
    return condo

# --- VISTORIA & OS ---
@app.get("/vistorias", response_model=List[VistoriaResponse])
async def list_vistorias(user: UserResponse = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(models.Vistoria)
    if user.permissao == "VISTORIADOR": return query.filter(models.Vistoria.vistoriador_id == user.usuario_id).all()
    return query.all()

@app.post("/vistorias", response_model=VistoriaResponse)
async def create_vistoria(data: VistoriaCreate, user: models.Usuario = Depends(get_user_with_permission("VISTORIADOR")), db: Session = Depends(get_db)):
    vistoria = models.Vistoria(condominio_id=data.condominio_id, vistoriador_id=user.usuario_id, observacoes_gerais=data.observacoes_gerais)
    db.add(vistoria)
    for item in data.itens:
        db_item = models.ItemVistoriado(categoria_item=item.categoria_item, nome_especifico_item=item.nome_especifico_item, status_item=item.status_item, descricao_detalhada=item.descricao_detalhada)
        for f in item.fotos: db_item.fotos.append(models.FotoVistoria(url_foto=f.url_foto, descricao_foto=f.descricao_foto))
        vistoria.itens_vistoriados.append(db_item)
        if item.status_item == "PROBLEMA":
            # Gera OS
            condo = db.query(models.Condominio).filter(models.Condominio.condominio_id == data.condominio_id).first()
            sindico = next((u for u in condo.usuarios if u.permissao == 'SINDICO'), None) if condo else None
            if sindico: db.add(models.OrdemServico(item_vistoriado_id=None, condominio_id=data.condominio_id, criado_por_id=user.usuario_id, responsavel_id=sindico.usuario_id, titulo_os=f"Prob: {item.nome_especifico_item}", descricao_problema=item.descricao_detalhada))
    db.commit(); db.refresh(vistoria)
    return vistoria

# --- CHAT ---
@app.get("/chat/{vistoria_id}", response_model=List[ChatMessageResponse])
async def get_chat(vistoria_id: int, db: Session = Depends(get_db)):
    return db.query(models.ChatMensagem).options(joinedload(models.ChatMensagem.remetente)).filter(models.ChatMensagem.vistoria_id == vistoria_id).all()

@app.post("/chat/{vistoria_id}")
async def post_chat(vistoria_id: int, msg: ChatMessageCreate, user: models.Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    novo_msg = models.ChatMensagem(vistoria_id=vistoria_id, remetente_id=user.usuario_id, conteudo_texto=msg.conteudo_texto)
    db.add(novo_msg); db.commit(); db.refresh(novo_msg); db.refresh(novo_msg.remetente)
    return novo_msg

# --- IA ---
@app.post("/ia/pergunta")
async def ask_ia(pergunta: IAPergunta, db: Session = Depends(get_db)):
    if not gemini_model: return {"resposta": "IA indisponível."}
    chunks = db.query(models.ChunkDocumento).join(models.DocumentoCondominio).filter(models.DocumentoCondominio.condominio_id == pergunta.condominio_id).all()
    contexto = "\n".join([c.conteudo_texto for c in chunks])
    resp = gemini_model.generate_content(f"Contexto:\n{contexto}\n\nPergunta: {pergunta.pergunta_texto}\nResposta:")
    return {"resposta": resp.text}

# --- MANUTENÇÃO ---
@app.get("/manutencoes/{condominio_id}", response_model=List[ManutencaoResponse])
async def get_manutencoes(condominio_id: int, db: Session = Depends(get_db)):
    return db.query(models.TarefaManutencao).filter(models.TarefaManutencao.condominio_id == condominio_id).all()

@app.get("/admin/financeiro/dashboard", response_model=FinanceiroDashboardResponse)
async def get_financeiro(db: Session = Depends(get_db)):
    receitas = db.query(func.coalesce(func.sum(models.FaturaCondominio.valor), 0.0)).filter(models.FaturaCondominio.status_pagamento == 'PAGA').scalar()
    despesas = db.query(func.coalesce(func.sum(models.DespesaInterna.valor), 0.0)).filter(models.DespesaInterna.status_pagamento == 'PAGO').scalar()
    return {"total_receitas": receitas, "total_despesas": despesas, "lucratividade": receitas - despesas, "total_pendente": 0.0}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)