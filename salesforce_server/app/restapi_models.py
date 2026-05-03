# salesforce_server/app/models.py
from pydantic import BaseModel
from typing import Optional

class TokenRequest(BaseModel):
    grant_type: str
    client_id: str
    client_secret: str
    username: Optional[str] = None
    password: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    instance_url: str
    token_type: str = "Bearer"
    issued_at: str
    signature: str
    
class ContentVersionCreate(BaseModel):
    Title: str
    PathOnClient: str
    VersionData: str
    FirstPublishLocationId: str | None = None

