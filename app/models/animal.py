from datetime import datetime, timezone
from typing import Optional
from pydantic import (
    BaseModel,
    Field,
    field_serializer,
    field_validator,
)
from bson import ObjectId


class Animal(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
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

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }

    @field_validator("id", mode="before")
    @classmethod
    def parse_object_id(cls, value):
        if isinstance(value, ObjectId):
            return value

        if isinstance(value, str) and ObjectId.is_valid(value):
            return ObjectId(value)

        raise ValueError("Invalid MongoDB ObjectId")

    @field_serializer("id", when_used="json")
    def serialize_object_id(self, value: ObjectId) -> str:
        return str(value)
