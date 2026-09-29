from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class Vehicle(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    make: str
    model: str
    model_year: int
    vehicle_type: str
    fuel_type: str
    transmission: str
    mileage_km: int
    color: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

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
