
import os
import tempfile
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel, Field, HttpUrl, model_validator
from apps.api.auth import require_api_key
from core.parsing.parsers import parse_local_file
from core.crawling.web import fetch_url_text
from core.chunking import chunk_texts
from core.embeddings import embed_texts
from core.retriever import QdrantStore

router = APIRouter(prefix="/ingest", tags=["ingest"], dependencies=[Depends(require_api_key)])

class Source(BaseModel):
    type: Literal["file", "url"]
    path: Optional[str] = None
    url: Optional[HttpUrl] = None
    title: Optional[str] = Field(default=None, max_length=300)

    @model_validator(mode="after")
    def validate_location(self):
        if self.type == "url" and not self.url:
            raise ValueError("URL sources require url")
        if self.type == "file" and not self.path:
            raise ValueError("File sources require path")
        return self

class IngestBody(BaseModel):
    sources: List[Source] = Field(min_length=1, max_length=50)
    collection: str = Field(default=os.getenv("COLLECTION", "default"), pattern=r"^[A-Za-z0-9_.-]{1,128}$")

@router.post("")
def ingest(body: IngestBody):
    texts = []
    metas = []
    for s in body.sources:
        if s.type == "url" and s.url:
            text, title = fetch_url_text(str(s.url))
            if not text.strip():
                continue
            texts.append(text)
            metas.append({"source": str(s.url), "title": title or s.title or str(s.url)})
        elif s.type == "file" and s.path:
            content, title = parse_local_file(s.path)
            if not content.strip():
                continue
            texts.append(content)
            metas.append({"source": s.path, "title": title or s.title or s.path})
        else:
            raise HTTPException(400, f"Bad source: {s}")
    if not texts:
        raise HTTPException(400, "No valid content to ingest")

    try:
        chunks, chunk_metas = chunk_texts(texts, metas)
        vectors = embed_texts(chunks)
        store = QdrantStore()
        store.upsert(body.collection, chunks, vectors, chunk_metas)
    except Exception as exc:
        raise HTTPException(502, f"Unable to ingest content: {exc}") from exc
    return {"ok": True, "chunks": len(chunks)}

def _ingest_uploaded_contents(uploaded: List[tuple[str, bytes]], collection: str):
    texts, metas = [], []
    for filename, content in uploaded:
        suffix = os.path.splitext(filename or "")[1]
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp_path = tmp.name
        with tmp as fp:
            fp.write(content)
        try:
            text, title = parse_local_file(tmp_path)
        finally:
            os.remove(tmp_path)
        if text.strip():
            texts.append(text)
            metas.append({"source": filename, "title": title or filename})
    if not texts:
        raise HTTPException(400, "No parsable files")
    try:
        chunks, chunk_metas = chunk_texts(texts, metas)
        vectors = embed_texts(chunks)
        store = QdrantStore()
        store.upsert(collection, chunks, vectors, chunk_metas)
    except Exception as exc:
        raise HTTPException(502, f"Unable to ingest uploaded files: {exc}") from exc
    return {"ok": True, "chunks": len(chunks)}


@router.post("/upload")
async def ingest_upload(
    files: List[UploadFile] = File(...),
    collection: str = Query(default=os.getenv("COLLECTION", "default"), pattern=r"^[A-Za-z0-9_.-]{1,128}$"),
):
    if not files:
        raise HTTPException(400, "At least one file is required")
    if len(files) > 20:
        raise HTTPException(400, "Upload at most 20 files at a time")

    uploaded = [(f.filename or "upload", await f.read()) for f in files]
    return await run_in_threadpool(_ingest_uploaded_contents, uploaded, collection)
