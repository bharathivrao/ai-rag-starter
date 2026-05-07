
import os
from typing import List, Dict
from openai import OpenAI

CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
OPENAI_TIMEOUT_SECONDS = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "10"))
OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "0"))

SYS_PROMPT = (
    "You are a grounded Q&A assistant. Use ONLY the provided context. "
    "If the answer is not in context, say you don't know. Always cite sources."
)

def _format_context(chunks: List[str], citations: List[Dict]) -> str:
    parts = []
    for i, (c, cite) in enumerate(zip(chunks, citations)):
        title = cite.get("title") or "Untitled"
        src = cite.get("source") or "unknown"
        parts.append(f"[{i+1}] {title} — {src}\n{c.strip()}\n")
    return "\n".join(parts)

def generate_answer(question: str, context_chunks: List[str], citations: List[Dict]) -> str:
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        timeout=OPENAI_TIMEOUT_SECONDS,
        max_retries=OPENAI_MAX_RETRIES,
    )
    context = _format_context(context_chunks, citations)
    user_prompt = f"""
Question: {question}

Context:
{context}

Instructions:
- Answer concisely.
- Include citation markers like [1], [2] aligned with the numbered context above.
- If unsure, say you don't know.
"""
    msgs = [
        {"role": "system", "content": SYS_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    resp = client.chat.completions.create(model=CHAT_MODEL, messages=msgs, temperature=0.2)
    return resp.choices[0].message.content.strip()
