
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict
import os
from fastapi import Depends
from core.embeddings import embed_texts
from core.retriever import QdrantStore
from core.generator import generate_answer
from apps.api.auth import require_api_key

router = APIRouter(prefix="/ask", tags=["ask"], dependencies=[Depends(require_api_key)])

class AskBody(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    collection: str = Field(default=os.getenv("COLLECTION", "default"), pattern=r"^[A-Za-z0-9_.-]{1,128}$")
    k: int = Field(default=5, ge=1, le=20)

@router.post("")
def ask(body: AskBody):
    if not body.question.strip():
        raise HTTPException(400, "Question is empty")
    try:
        store = QdrantStore()
        if not store.collection_exists(body.collection):
            raise HTTPException(404, f"Collection does not exist: {body.collection}")
        q_vec = embed_texts([body.question])[0]
        results = store.search(body.collection, q_vec, top_k=body.k)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, f"Unable to search or generate embeddings: {exc}") from exc
    context_chunks = [r["payload"]["text"] for r in results]
    citations: List[Dict] = [
        {"title": r["payload"].get("title"), "source": r["payload"].get("source")}
        for r in results
    ]
    try:
        answer = generate_answer(body.question, context_chunks, citations)
    except Exception as exc:
        raise HTTPException(502, f"Unable to generate answer: {exc}") from exc
    return {"answer": answer, "citations": citations, "used": len(context_chunks)}
