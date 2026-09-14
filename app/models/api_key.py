from pydantic import BaseModel, Field, field_serializer, field_validator, ConfigDict
from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId


class APIKey(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    project: str
    description: str
    encrypted_key: str
    hashed_key: str
    active: bool = True
    internal: bool
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    revoked_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    @field_validator("id", mode="before")
    @classmethod
    def parse_object_id(cls, value):
        """For `model_dump_json()`"""
        if isinstance(value, ObjectId):
            return value

        if isinstance(value, str) and ObjectId.is_valid(value):
            return ObjectId(value)

        raise ValueError("Invalid MongoDB ObjectId")

    @field_serializer("id", when_used="json")
    def serialize_object_id(self, value: ObjectId) -> str:
        """For `model_dump_json()`"""
        return str(value)


class APIKeyDTO(BaseModel):
    id: str
    project: str
    description: str
    active: bool
    internal: bool
    created_at: datetime

    def __init__(self, key: APIKey):
        self.id = (str(key.id),)
        self.project = (key.project,)
        self.description = (key.description,)
        self.active = (key.active,)
        self.internal = (key.internal,)
        self.created_at = (key.created_at,)
