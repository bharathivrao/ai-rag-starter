
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI RAG Starter", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .routes import ingest, ask, feedback, documents  # noqa: E402

app.include_router(ask.router)
app.include_router(ingest.router)
app.include_router(feedback.router)
app.include_router(documents.router)

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

@app.get("/")
def root():
    return {
        "name": "AI RAG Starter",
        "docs": "/docs",
        "health": "/health",
        "endpoints": [
            "/ingest",
            "/ingest/upload",
            "/ask",
            "/feedback",
            "/documents",
            "/documents/collections",
        ],
    }

@app.get("/health")
def health():
    return {"status": "ok"}
