from pydantic import BaseModel, Field
from datetime import datetime, timezone


class APIKey(BaseModel):
    project: str
    description: str
    hashed_key: str
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    internal: bool
