from pydantic import (
    BaseModel,
    Field,
    field_serializer,
    field_validator,
)
from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId


class APIKeyDTO(BaseModel):
    id: str
    project: str
    description: str
    active: bool
    internal: bool
    created_at: datetime


class APIKey(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    project: str
    description: str
    hashed_key: str
    active: bool = True
    internal: bool
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    revoked_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    def convert_dto(self) -> APIKeyDTO:
        return APIKeyDTO(
            id=str(self.id),
            project=self.project,
            description=self.description,
            active=self.active,
            internal=self.internal,
            created_at=self.created_at,
        )

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
