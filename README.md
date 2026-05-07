# AI RAG Starter (FastAPI + Qdrant)

A minimal Retrieval-Augmented Generation (RAG) starter you can run locally or in Docker.

## Features

- `/ingest` — parse (files/URLs) → chunk → embed → upsert to Qdrant
- `/ask` — search → (optional) rerank stub → prompt → LLM answer with citations
- `/feedback` — store basic feedback to a local SQLite file
- Qdrant vector DB via Docker Compose
- Simple char-based chunker (swap with token-based later)
- Extensible parsing for PDF, DOCX, TXT, HTML/URLs

## Quickstart (dev, no Docker)

1. **Python 3.10+** recommended.
2. Create `.env` from example:

    ```bash
    cp .env.example .env
    # Fill in OPENAI_API_KEY (or set env var at runtime)
    ```

3. Install deps:

    ```bash
    pip install -r requirements.txt
    ```

4. Start Qdrant (Docker required for this step):

    ```bash
    docker compose up -d qdrant
    ```

5. Run API:

    ```bash
    uvicorn apps.api.main:app --reload --port 8000
    ```

6. Try endpoints:
    - Ingest a URL:

        ```bash
        curl -X POST http://localhost:8000/ingest        -H "Content-Type: application/json"        -d '{"sources":[{"type":"url","url":"https://qdrant.tech"}],"collection":"default"}'
        ```

    - Ask a question:

        ```bash
        curl -X POST http://localhost:8000/ask        -H "Content-Type: application/json"        -d '{"question":"What is Qdrant?", "collection":"default", "k": 5}'
        ```


## Quickstart (Docker Compose: app + Qdrant)

```bash
docker compose up --build
# API served at http://localhost:8000
```

## Project Layout

```
apps/api/                 # FastAPI app
  main.py
  routes/
    ingest.py             # /ingest
    ask.py                # /ask
    feedback.py           # /feedback
core/
  parsing/                # PDF/DOCX/TXT; URL HTML
  crawling/               # URL fetch
  chunking.py             # simple chunker
  embeddings.py           # OpenAI embeddings
  retriever.py            # Qdrant client wrapper
  generator.py            # LLM call + prompt compose
infra/
  docker-compose.yml
  Dockerfile
tests/
  test_chunking.py
.env.example
requirements.txt
```

## Environment

- `OPENAI_API_KEY` — required for embeddings and LLM
- `OPENAI_EMBED_MODEL` — default: `text-embedding-3-small`
- `OPENAI_CHAT_MODEL` — default: `gpt-4o-mini`
- `QDRANT_URL` — default: `http://localhost:6333`
- `COLLECTION` — default collection name (`default`)

## Notes

- This starter uses **character-based** chunking to keep dependencies light; swap in token-based (tiktoken) if you prefer.
- Reranking is left as a stub to integrate with your preferred reranker (e.g., Cohere, BGE).

## Challenges Faced

- **Coordinating multiple services locally:** the API depends on Qdrant and OpenAI credentials, so keeping Docker, environment variables, and local development startup steps aligned was an important part of the setup.
- **Handling different ingestion sources:** supporting both URLs and local files required validation, parsing, temporary file handling for uploads, and clear failure responses when content could not be parsed.
- **Chunking tradeoffs:** the project currently uses character-based chunking to stay lightweight, but chunk size and overlap still affect retrieval quality, citation usefulness, and embedding cost.
- **Managing vector collection behavior:** Qdrant collections need to be created with the correct vector size before upsert, and document listing/deletion depends on consistent source metadata across chunks.
- **Keeping API access controlled:** adding optional API-key authentication had to preserve easy local development while still protecting ingest, ask, feedback, and document-management routes when a token is configured.
- **Persisting feedback simply:** SQLite keeps feedback storage easy to run locally, but it requires careful error handling and a clear database path so the API can reliably save user feedback.
- **Balancing starter simplicity with extensibility:** reranking, stronger parsers, token-aware chunking, and production persistence are intentionally left replaceable without making the starter too complex.
