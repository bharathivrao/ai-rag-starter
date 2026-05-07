import os

from fastapi import Header, HTTPException


API_AUTH_TOKEN = os.getenv("API_AUTH_TOKEN")


def require_api_key(
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
) -> None:
    if not API_AUTH_TOKEN:
        return

    bearer_token = None
    if authorization and authorization.lower().startswith("bearer "):
        bearer_token = authorization[7:].strip()

    if x_api_key == API_AUTH_TOKEN or bearer_token == API_AUTH_TOKEN:
        return

    raise HTTPException(status_code=401, detail="Missing or invalid API key")
