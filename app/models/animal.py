from datetime import datetime, timezone
from pydantic import BaseModel, Field


class Animal(BaseModel):
    name: str
    species: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
