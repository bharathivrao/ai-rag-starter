
import os
import uuid
from typing import Dict, List
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_TIMEOUT_SECONDS = float(os.getenv("QDRANT_TIMEOUT_SECONDS", "10"))

class QdrantStore:
    def __init__(self):
        self.client = QdrantClient(url=QDRANT_URL, timeout=QDRANT_TIMEOUT_SECONDS)
        self.dim_cache = {}

    def _ensure_collection(self, name: str, vector_dim: int):
        if name in self.dim_cache:
            return
        try:
            self.client.get_collection(name)
            self.dim_cache[name] = vector_dim
            return
        except Exception:
            pass
        self.client.recreate_collection(
            collection_name=name,
            vectors_config=VectorParams(size=vector_dim, distance=Distance.COSINE),
        )
        self.dim_cache[name] = vector_dim

    def upsert(self, collection: str, texts: List[str], vectors: List[List[float]], metas: List[Dict]):
        if not vectors:
            return
        dim = len(vectors[0])
        self._ensure_collection(collection, dim)
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=v,
                payload=meta,
            )
            for v, meta in zip(vectors, metas)
        ]
        self.client.upsert(collection_name=collection, points=points)

    def search(self, collection: str, query_vec: List[float], top_k: int = 5) -> List[Dict]:
        hits = self.client.search(collection_name=collection, query_vector=query_vec, limit=top_k)
        results = []
        for h in hits:
            results.append({
                "id": h.id,
                "score": h.score,
                "payload": h.payload,
            })
        return results

    def list_collections(self) -> List[str]:
        collections = self.client.get_collections().collections
        return [c.name for c in collections]

    def collection_exists(self, collection: str) -> bool:
        return self.client.collection_exists(collection)

    def list_documents(self, collection: str, limit: int = 100) -> List[Dict]:
        if not self.collection_exists(collection):
            raise ValueError(f"Collection does not exist: {collection}")

        docs: Dict[str, Dict] = {}
        offset = None
        while True:
            records, offset = self.client.scroll(
                collection_name=collection,
                limit=min(max(limit, 1), 256),
                offset=offset,
                with_payload=["source", "title"],
                with_vectors=False,
            )
            for record in records:
                payload = record.payload or {}
                source = payload.get("source") or "unknown"
                title = payload.get("title") or source
                entry = docs.setdefault(source, {"source": source, "title": title, "chunks": 0})
                entry["chunks"] += 1
            if offset is None or len(docs) >= limit:
                break
        return list(docs.values())[:limit]

    def delete_document(self, collection: str, source: str) -> int:
        if not self.collection_exists(collection):
            raise ValueError(f"Collection does not exist: {collection}")

        selector = Filter(
            must=[
                FieldCondition(
                    key="source",
                    match=MatchValue(value=source),
                )
            ]
        )
        count = self.client.count(collection_name=collection, count_filter=selector, exact=True).count
        if count:
            self.client.delete(collection_name=collection, points_selector=selector)
        return count

    def delete_collection(self, collection: str) -> bool:
        if not self.collection_exists(collection):
            return False
        return self.client.delete_collection(collection_name=collection)
