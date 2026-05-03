# salesforce_server/app/api/auth_router.py

from __future__ import annotations
from datetime import datetime
import secrets
from fastapi import APIRouter, Request, HTTPException

from salesforce_server.app.app import config, resolve_path


router = APIRouter(prefix="/services/oauth2")


# ------------------------------------------------------------
# 設定値（config.toml）
# ------------------------------------------------------------
SF_INSTANCE_URL = config["storage"]["base_url"]   # ← ここがポイント
SF_PUBLIC_KEY_PATH = resolve_path(config["security"]["sf_public_key"])


with open(SF_PUBLIC_KEY_PATH, "r") as f:
    SF_PUBLIC_KEY = f.read()


@router.post("/token")
async def issue_token(request: Request):
    """
    Salesforce OAuth2 Token Endpoint (Mock)
    Supports JWT Bearer Flow only
    """

    form = await request.form()

    grant_type = form.get("grant_type")
    if grant_type != "urn:ietf:params:oauth:grant-type:jwt-bearer":
        raise HTTPException(status_code=400, detail="unsupported_grant_type")

    # assertion = form.get("assertion")
    # 本番ではここで JWT を decode & verify する
    # Mock なので省略

    return {
        "access_token": "mock_access_token",
        "instance_url": SF_INSTANCE_URL,   # ← ここが storage.base_url
        "token_type": "Bearer",
        "issued_at": str(int(datetime.utcnow().timestamp() * 1000)),
        "signature": secrets.token_hex(16),
    }
