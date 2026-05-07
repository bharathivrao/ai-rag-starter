
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Literal, Optional
import sqlite3, os, time
from apps.api.auth import require_api_key

router = APIRouter(prefix="/feedback", tags=["feedback"], dependencies=[Depends(require_api_key)])

DB_PATH = os.path.join(os.getcwd(), "feedback.sqlite")

class FeedbackBody(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    answer: str = Field(min_length=1, max_length=20000)
    label: Literal["up", "down"]
    notes: Optional[str] = Field(default="", max_length=2000)

def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER, question TEXT, answer TEXT, label TEXT, notes TEXT)"
    )
    con.commit()
    con.close()

init_db()

@router.post("")
def save_feedback(body: FeedbackBody):
    try:
        con = sqlite3.connect(DB_PATH)
        con.execute(
            "INSERT INTO feedback (ts, question, answer, label, notes) VALUES (?, ?, ?, ?, ?)",
            (int(time.time()), body.question, body.answer, body.label, body.notes or ""),
        )
        con.commit()
        con.close()
    except sqlite3.Error as exc:
        raise HTTPException(500, f"Unable to save feedback: {exc}") from exc
    return {"ok": True}
