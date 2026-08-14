from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class Animal(BaseModel):
    name: str
    species: str
    scientific_name: Optional[str] = None

    habitat: str
    region: str
    diet: str

    average_weight_kg: Optional[float] = None
    average_lifespan_years: Optional[int] = None

    endangered: bool = False

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
