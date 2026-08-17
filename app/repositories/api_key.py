from pymongo import ReturnDocument
from pymongo.collection import Collection
from app.models import APIKey
from app.constants import GRACE_PERIOD
from typing import Optional
from bson import ObjectId
from datetime import datetime, timezone, timedelta

import logging

logger = logging.getLogger(__name__)


class APIKeyRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def create(self, api_key: APIKey) -> Optional[APIKey]:
        result = self.collection.insert_one(
            api_key.model_dump(mode="python", by_alias=True)
        )
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
        """
        Deactivate the key.
        The key still exists in the database for period of time
        before being deleted.
        During the period, user can contact us if they wish to re-activate the key.
        """
        now = datetime.now(timezone.utc)
        revoked_doc = self.collection.find_one_and_update(
            {"_id": ObjectId(key_id), "active": True},
            {
                "$set": {
                    "active": False,
                    "revoked_at": now,
                    "deleted_at": now + timedelta(days=GRACE_PERIOD),
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        if revoked_doc is None:
            return None

        logger.info("Key revoked in database")
        return APIKey(**revoked_doc)

    def reactivate(self, key_id: str) -> Optional[APIKey]:
        reactivated_doc = self.collection.find_one_and_update(
            {"_id": ObjectId(key_id), "active": False},
            {
                "$set": {
                    "active": True,
                },
                "$unset": {
                    "revoked_at": None,
                    "deleted_at": None,
                },
            },
            return_document=ReturnDocument.AFTER,
        )
        if reactivated_doc is None:
            return None

        logger.info("Key reactivated in database")
        return APIKey(**reactivated_doc)

    def force_delete(self, key_id: str) -> Optional[APIKey]:
        """Delete the key from the system. Not recommended"""
        deleted_doc = self.collection.find_one_and_delete({"_id": ObjectId(key_id)})

        if deleted_doc is None:
            return None

        logger.info("Key force deleted from DB")
        return APIKey(**deleted_doc)
