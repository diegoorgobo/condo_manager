from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List
from .. import database, models, schemas, auth
from ..utils.pdf_extractor import extract_text_from_pdf

router = APIRouter(prefix="/documents", tags=["Documents & AI"])

@router.post("/upload", response_model=dict)
async def upload_document(
    title: str = Form(...),
    condominium_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db)
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Apenas PDFs são permitidos.")

    # 1. Extrair Texto para a IA
    extracted_text = await extract_text_from_pdf(file)

    # 2. Salvar metadados no Banco
    # (Em produção, salve o arquivo no S3/Supabase Storage e guarde a URL em file_path)
    fake_path = f"storage/{file.filename}" 
    
    db_doc = models.Document(
        title=title,
        file_path=fake_path,
        content_text=extracted_text, # O texto puro fica salvo aqui para busca
        condominium_id=condominium_id
    )
    db.add(db_doc)
    db.commit()
    
    return {"status": "Documento indexado com sucesso", "id": db_doc.id}

@router.get("/ask")
def ask_ai(question: str, condominium_id: int, db: Session = Depends(database.get_db)):
    """
    Simula uma IA buscando respostas nos documentos do condomínio.
    """
    # 1. Busca simples por palavras-chave (Para MVP)
    # Divide a pergunta em palavras chaves (ignorando 'de', 'para', etc se quiser melhorar)
    keywords = [w for w in question.split() if len(w) > 3]
    
    if not keywords:
        return {"answer": "Por favor, faça uma pergunta mais específica."}

    # 2. Procura documentos que contenham as palavras
    filters = []
    for word in keywords:
        filters.append(models.Document.content_text.ilike(f"%{word}%"))
    
    # Busca docs que tenham pelo menos uma das palavras chaves no texto
    results = db.query(models.Document).filter(
        models.Document.condominium_id == condominium_id,
        or_(*filters)
    ).all()

    if not results:
        return {"answer": "Não encontrei informações sobre isso nos documentos cadastrados."}

    # 3. Extrai o contexto (Snippet)
    # Pega o trecho do texto onde a palavra aparece
    found_snippets = []
    for doc in results:
        text_lower = doc.content_text.lower()
        for word in keywords:
            idx = text_lower.find(word.lower())
            if idx != -1:
                # Pega 100 caracteres antes e 300 depois
                start = max(0, idx - 100)
                end = min(len(doc.content_text), idx + 300)
                snippet = doc.content_text[start:end].replace("\n", " ")
                found_snippets.append(f"No documento '{doc.title}': ...{snippet}...")
                break # Um snippet por documento é suficiente por enquanto

    if not found_snippets:
        return {"answer": "O termo consta nos documentos, mas não consegui extrair um contexto claro."}

    # Retorna uma resposta formatada
    final_response = "Encontrei as seguintes informações:\n\n" + "\n\n".join(found_snippets)
    return {"answer": final_response}
