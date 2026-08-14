from pymongo.collection import Collection
from app.models import APIKey
from typing import Optional
from bson import ObjectId

import logging

logger = logging.getLogger(__name__)


class APIKeyRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def create(self, api_key: APIKey) -> Optional[APIKey]:
        result = self.collection.insert_one(api_key.model_dump(mode="json"))
        if not result.acknowledged:
            return None

        logger.info("Key inserted to DB")
        return api_key

    def find_by_hash(self, key_hash: str) -> Optional[APIKey]:
        doc = self.collection.find_one({"hashed_key": key_hash})
        if doc is None:
            return None

        logger.info("Key found in DB")
        return APIKey(**doc)

    def revoke(self, key_id: str) -> Optional[APIKey]:
        result = self.collection.update_one(
            {"_id": ObjectId(key_id), "active": True},
            {
                "$set": {
                    "active": False,
                }
            },
        )
        if result.modified_count == 0:
            return None

        doc = self.collection.find_one({"_id": ObjectId(key_id)})
        if doc is None:
            return None

        logger.info("Key revoked in DB")
        return APIKey(**doc)
