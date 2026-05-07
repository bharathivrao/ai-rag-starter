
from typing import List, Tuple, Dict

def _split_text(text: str, max_chars: int = 1200, overlap: int = 200) -> List[str]:
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + max_chars, n)
        chunk = text[start:end]
        chunks.append(chunk)
        if end >= n:
            break
        start = end - overlap
        if start < 0:
            start = 0
        if start >= n:
            break
    return [c for c in chunks if c.strip()]

def chunk_texts(texts: List[str], metas: List[Dict], max_chars: int = 1200, overlap: int = 200) -> Tuple[List[str], List[Dict]]:
    out_texts, out_metas = [], []
    for text, meta in zip(texts, metas):
        parts = _split_text(text, max_chars=max_chars, overlap=overlap)
        for idx, p in enumerate(parts):
            cm = dict(meta)
            cm["chunk_index"] = idx
            out_texts.append(p)
            cm["text"] = p  # stored in payload for convenience
            out_metas.append(cm)
    return out_texts, out_metas
