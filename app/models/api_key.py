from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional


class APIKey(BaseModel):
    project: str
    description: str
    hashed_key: str
    active: bool = True
    internal: bool
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    revoked_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
