
import os
from typing import Tuple
import pdfplumber
from docx import Document

def parse_local_file(path: str) -> Tuple[str, str]:
    ext = os.path.splitext(path)[1].lower()
    if ext in [".txt", ".md"]:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read(), os.path.basename(path)
    if ext in [".pdf"]:
        try:
            txts = []
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    txts.append(page.extract_text() or "")
            return "\n".join(txts), os.path.basename(path)
        except Exception:
            return "", os.path.basename(path)
    if ext in [".docx"]:
        try:
            doc = Document(path)
            text = "\n".join([p.text for p in doc.paragraphs])
            return text, os.path.basename(path)
        except Exception:
            return "", os.path.basename(path)
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read(), os.path.basename(path)
    except Exception:
        return "", os.path.basename(path)
