import os
from typing import Annotated
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field

from apps.api.auth import require_api_key
from core.retriever import QdrantStore


router = APIRouter(prefix="/documents", tags=["documents"], dependencies=[Depends(require_api_key)])

CollectionName = Annotated[
    str,
    Field(pattern=r"^[A-Za-z0-9_.-]{1,128}$"),
]


@router.get("/collections")
def list_collections():
    try:
        return {"collections": QdrantStore().list_collections()}
    except Exception as exc:
        raise HTTPException(502, f"Unable to list collections: {exc}") from exc


@router.get("")
def list_documents(
    collection: CollectionName = os.getenv("COLLECTION", "default"),
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
):
    try:
        documents = QdrantStore().list_documents(collection, limit=limit)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Unable to list documents: {exc}") from exc
    return {"collection": collection, "documents": documents}


@router.delete("")
def delete_document(
    source: str = Query(min_length=1, max_length=2000),
    collection: CollectionName = os.getenv("COLLECTION", "default"),
):
    try:
        deleted = QdrantStore().delete_document(collection, unquote(source))
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Unable to delete document: {exc}") from exc

    if deleted == 0:
        raise HTTPException(404, "No document chunks matched that source")
    return {"ok": True, "deleted_chunks": deleted}


@router.delete("/collections/{collection}")
def delete_collection(collection: CollectionName):
    try:
        deleted = QdrantStore().delete_collection(collection)
    except Exception as exc:
        raise HTTPException(502, f"Unable to delete collection: {exc}") from exc
    if not deleted:
        raise HTTPException(404, f"Collection does not exist: {collection}")
    return {"ok": True}
