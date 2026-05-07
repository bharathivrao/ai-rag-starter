
from core.chunking import chunk_texts

def test_chunking_basic():
    txts = ["A" * 3000]
    metas = [{"source":"x","title":"t"}]
    chunks, metas_out = chunk_texts(txts, metas, max_chars=1000, overlap=200)
    assert len(chunks) >= 3
    assert len(chunks) == len(metas_out)
