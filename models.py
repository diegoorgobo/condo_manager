from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Text, DateTime, Date, Float, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# Tabela de Associação (Usuários <-> Condomínios)
usuarios_condominios_association = Table(
    'usuarios_condominios', Base.metadata,
    Column('usuario_id', Integer, ForeignKey('usuarios.usuario_id'), primary_key=True),
    Column('condominio_id', Integer, ForeignKey('condominios.condominio_id'), primary_key=True)
)

class Usuario(Base):
    __tablename__ = "usuarios"
    usuario_id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hash_senha = Column(String, nullable=False)
    permissao = Column(String, nullable=False) 
    condominios = relationship("Condominio", secondary=usuarios_condominios_association, back_populates="usuarios")

class Condominio(Base):
    __tablename__ = "condominios"
    condominio_id = Column(Integer, primary_key=True, index=True)
    nome_fantasia = Column(String, nullable=False)
    cnpj = Column(String, unique=True, nullable=False)
    endereco_completo = Column(String, nullable=True)
    usuarios = relationship("Usuario", secondary=usuarios_condominios_association, back_populates="condominios")

class Vistoria(Base):
    __tablename__ = "vistorias"
    vistoria_id = Column(Integer, primary_key=True, index=True)
    condominio_id = Column(Integer, ForeignKey("condominios.condominio_id"), nullable=False)
    vistoriador_id = Column(Integer, ForeignKey("usuarios.usuario_id"), nullable=False)
    data_inicio = Column(DateTime(timezone=True), server_default=func.now())
    status_vistoria = Column(String, default='CONCLUIDA')
    observacoes_gerais = Column(Text, nullable=True)
    itens_vistoriados = relationship("ItemVistoriado", back_populates="vistoria", cascade="all, delete-orphan")
    vistoriador = relationship("Usuario")

class ItemVistoriado(Base):
    __tablename__ = "itens_vistoriados"
    item_vistoriado_id = Column(Integer, primary_key=True, index=True)
    vistoria_id = Column(Integer, ForeignKey("vistorias.vistoria_id"), nullable=False)
    categoria_item = Column(String, nullable=False)
    nome_especifico_item = Column(String, nullable=False)
    status_item = Column(String, nullable=False)
    descricao_detalhada = Column(Text, nullable=True)
    link_os_id = Column(Integer, ForeignKey("ordens_servico.os_id"), nullable=True)
    link_os = relationship("OrdemServico", back_populates="item_vistoriado", foreign_keys=[link_os_id])
    fotos = relationship("FotoVistoria", back_populates="item_vistoriado", cascade="all, delete-orphan")
    vistoria = relationship("Vistoria", back_populates="itens_vistoriados")

class FotoVistoria(Base):
    __tablename__ = "fotos_vistoria"
    foto_id = Column(Integer, primary_key=True, index=True)
    item_vistoriado_id = Column(Integer, ForeignKey("itens_vistoriados.item_vistoriado_id"), nullable=False)
    url_foto = Column(String, nullable=False)
    descricao_foto = Column(String, nullable=True)
    item_vistoriado = relationship("ItemVistoriado", back_populates="fotos")

class OrdemServico(Base):
    __tablename__ = "ordens_servico"
    os_id = Column(Integer, primary_key=True, index=True)
    item_vistoriado_id = Column(Integer, ForeignKey("itens_vistoriados.item_vistoriado_id"), nullable=True)
    condominio_id = Column(Integer, ForeignKey("condominios.condominio_id"), nullable=False)
    criado_por_id = Column(Integer, ForeignKey("usuarios.usuario_id"), nullable=False)
    responsavel_id = Column(Integer, ForeignKey("usuarios.usuario_id"), nullable=False)
    titulo_os = Column(String, nullable=False)
    descricao_problema = Column(Text, nullable=True)
    status_os = Column(String, default='ABERTA')
    data_abertura = Column(DateTime(timezone=True), server_default=func.now())
    condominio = relationship("Condominio")
    criado_por = relationship("Usuario", foreign_keys=[criado_por_id])
    responsavel = relationship("Usuario", foreign_keys=[responsavel_id])
    item_vistoriado = relationship("ItemVistoriado", back_populates="link_os", foreign_keys=[item_vistoriado_id])

class ChatMensagem(Base):
    __tablename__ = "chat_mensagens"
    mensagem_id = Column(Integer, primary_key=True, index=True)
    vistoria_id = Column(Integer, ForeignKey("vistorias.vistoria_id"), nullable=False)
    remetente_id = Column(Integer, ForeignKey("usuarios.usuario_id"), nullable=False)
    conteudo_texto = Column(Text, nullable=False)
    data_envio = Column(DateTime(timezone=True), server_default=func.now())
    remetente = relationship("Usuario")

class TarefaManutencao(Base):
    __tablename__ = "tarefas_manutencao"
    tarefa_id = Column(Integer, primary_key=True, index=True)
    condominio_id = Column(Integer, ForeignKey("condominios.condominio_id"), nullable=False)
    tipo_tarefa = Column(String, nullable=False)
    status_tarefa = Column(String, default='ATIVA')
    data_proximo_vencimento = Column(Date, nullable=True)
    periodicidade_meses = Column(Integer, nullable=True)
    detalhes_agendamento_semanal = Column(String, nullable=True)
    data_ultima_execucao = Column(Date, nullable=True)
    condominio = relationship("Condominio")

class FaturaCondominio(Base):
    __tablename__ = "faturas_condominios"
    fatura_id = Column(Integer, primary_key=True, index=True)
    condominio_id = Column(Integer, ForeignKey("condominios.condominio_id"), nullable=False)
    valor = Column(Float, nullable=False)
    status_pagamento = Column(String, default='PENDENTE')
    condominio = relationship("Condominio")

class DespesaInterna(Base):
    __tablename__ = "despesas_internas"
    despesa_id = Column(Integer, primary_key=True, index=True)
    valor = Column(Float, nullable=False)
    status_pagamento = Column(String, default='PENDENTE')

class DocumentoCondominio(Base):
    __tablename__ = "documentos_condominio"
    documento_id = Column(Integer, primary_key=True, index=True)
    condominio_id = Column(Integer, ForeignKey("condominios.condominio_id"), nullable=False)
    nome_exibicao = Column(String, nullable=False)
    url_arquivo = Column(String, nullable=False)
    tipo_documento = Column(String, nullable=False)
    status_processamento = Column(String, default='PENDENTE')
    chunks = relationship("ChunkDocumento", back_populates="documento")

class ChunkDocumento(Base):
    __tablename__ = "chunks_documentos"
    chunk_id = Column(Integer, primary_key=True, index=True)
    documento_id = Column(Integer, ForeignKey("documentos_condominio.documento_id"), nullable=False)
    conteudo_texto = Column(Text, nullable=False)
    vetor_id = Column(String, nullable=False)
    documento = relationship("DocumentoCondominio", back_populates="chunks")