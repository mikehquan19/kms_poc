import os
import secrets
import hashlib
from typing import Optional, Any, List
from datetime import datetime, timezone

from app.models import APIKey, APIKeyDTO
from app.repositories import APIKeyRepository, L1Cache, RedisCache
from app.constants import API_KEY_PREFIX
from cryptography.fernet import Fernet

from dotenv import load_dotenv
import logging
from opentelemetry import trace

load_dotenv()


logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class APIKeyService:
    def __init__(
        self, repository: APIKeyRepository, redis_cache: RedisCache, l1_cache: L1Cache
    ):
        self.repository = repository
        self.redis_cache = redis_cache
        self.redis_cache_ttl = 5 * 60

        self.l1_cache = l1_cache
        self.l1_cache_ttl = 15

        fernet_key = os.getenv("FERNET_KEY")
        if not fernet_key:
            raise Exception("No fernet for encryption/decryption")
        self.fernet = Fernet(os.getenv("FERNET_KEY"))

    def _hash_key(self, api_key: str) -> str:
        return hashlib.sha256(api_key.encode("utf-8")).hexdigest()

    def _insert_redis_cache(self, doc: APIKey):
        try:
            self.redis_cache.set(
                f"{API_KEY_PREFIX}:{doc.hashed_key}",
                doc.model_dump_json(),
                self.redis_cache_ttl,
            )
            logger.info("Key inserted to redis cache")
        except Exception as e:
            logger.error(f"Failed to cache key in redis: {e}")

    def _delete_redis_cache(self, key_hash: str):
        try:
            self.redis_cache.delete(f"{API_KEY_PREFIX}:{key_hash}")
            logger.info("Key deleted from redis cache")
        except Exception as e:
            logger.error(f"Failed to delete cached key in redis: {e}")

    def _insert_l1_cache(self, doc: APIKey):
        try:
            self.l1_cache.set(
                f"{API_KEY_PREFIX}:{doc.hashed_key}",
                doc.model_dump_json(),
                self.l1_cache_ttl,
            )
            logger.info("Key inserted to l1 cache")
        except Exception as e:
            logger.error(f"Failed to cache key in l1: {e}")

    def _delete_l1_cache(self, key_hash: str):
        try:
            self.l1_cache.delete(f"{API_KEY_PREFIX}:{key_hash}")
            logger.info("Key deleted from l1 cache")
        except Exception as e:
            logger.error(f"Failed to delete cached key in l1: {e}")

    def _delete_cache(self, key_hash: str):
        self._delete_redis_cache(key_hash)
        self._delete_l1_cache(key_hash)

    def create_key(
        self, project: str, description: str, internal: bool
    ) -> Optional[dict[str, Any]]:
        """
        Strategy for API key generation:
            - Format: `nebula_api_<32 bytes of base64-encoded string>`
            - Encrypt using Fernet so we can see the key again
            - Hash using SHA-256 so we can search for the unique hash more efficiently
            - Insert to MongoDB
            - Insert to Redis cache (expiring every 5 for testing)
        """
        with tracer.start_as_current_span("api_key.create"):
            api_key = f"nebula_api_{secrets.token_urlsafe(32)}"
            key_hash = self._hash_key(api_key)
            created_doc = self.repository.create(
                APIKey(
                    project=project,
                    description=description,
                    encrypted_key=self.fernet.encrypt(api_key.encode()),
                    hashed_key=key_hash,
                    internal=internal,
                )
            )
            if not created_doc:
                return None

            return {
                "id": str(created_doc.id),
                "project": created_doc.project,
                "description": created_doc.description,
                "api_key": api_key,
                "active": created_doc.active,
                "created_at": created_doc.created_at,
                "internal": created_doc.internal,
            }

    def validate_key(self, api_key: str) -> Optional[APIKeyDTO]:
        """
        Strategy for API key validation:
            - Hash using SHA-256
            - Check Redis cache. If cache hits, return the result
            - If cache misses,
            -   Check MongoDB. If key exists,
            -       Re-insert the key in cache
            -       Return result
            - Return none
        """
        with tracer.start_as_current_span("api_key.validate"):
            key_hash = self._hash_key(api_key)

            with tracer.start_as_current_span("l1.get_api_key") as span:
                data = self.l1_cache.get(f"{API_KEY_PREFIX}:{key_hash}")
                if data:
                    # Cache hit
                    span.set_attribute("l1.hit", True)
                    logger.info("Key found in l1 cache")

                    return APIKeyDTO(APIKey.model_validate_json(data))
                else:
                    span.set_attribute("l1.hit", False)

            with tracer.start_as_current_span("redis.get_api_key") as span:
                data = self.redis_cache.get(f"{API_KEY_PREFIX}:{key_hash}")
                if data:
                    # Cache hit
                    span.set_attribute("redis.hit", True)
                    logger.info("Key found in redis cache")

                    doc = APIKey.model_validate_json(data)
                    with tracer.start_as_current_span("l1.set_api_key"):
                        # Key expires in L1 cache so reinsert it
                        self._insert_l1_cache(doc)

                    return APIKeyDTO(doc)
                else:
                    span.set_attribute("redis.hit", False)

            # Cache miss
            with tracer.start_as_current_span("mongo.find_key"):
                doc = self.repository.find_by_hash(key_hash=key_hash)
                if not doc:
                    return None

            if doc.active:
                # Cache misses because key expires
                with tracer.start_as_current_span("cache.set_api_key"):
                    self._insert_redis_cache(doc)
                    self._insert_l1_cache(doc)

            return APIKeyDTO(doc)

    def revoke_key(self, key_id: str) -> Optional[APIKeyDTO]:
        with tracer.start_as_current_span("api_key.revoke"):
            with tracer.start_as_current_span("mongo.revoke_api_key") as span:
                doc = self.repository.revoke(key_id)
                if not doc:
                    return None

                span.set_attributes(
                    {
                        "api_key.revoked_at": doc.revoked_at,
                        "api_key.deleted_at": doc.deleted_at,
                    }
                )

            with tracer.start_as_current_span("cache.delete_api_key"):
                self._delete_cache(doc.hashed_key)

            return APIKeyDTO(doc)

    def reactivate_key(self, key_id: str) -> Optional[APIKeyDTO]:
        with tracer.start_as_current_span("api_key.reactivate"):
            doc = self.repository.reactivate(key_id)
            if not doc:
                return None

            return APIKeyDTO(doc)

    def force_delete_key(self, key_id: str) -> Optional[APIKeyDTO]:
        with tracer.start_as_current_span("api_key.force_delete"):
            with tracer.start_as_current_span("mongo.delete_api_key") as span:
                doc = self.repository.force_delete(key_id)
                if not doc:
                    return None
                now = datetime.now(timezone.utc)
                span.set_attribute("api_key.deleted_at", now)

            with tracer.start_as_current_span("cache.delete_api_key"):
                self._delete_cache(doc.hashed_key)

            return APIKeyDTO(doc)

    def get_keys(self, project: str) -> List[dict[str, Any]]:
        with tracer.start_as_current_span("api_key.get"):
            docs = self.repository.find_by_project(project)

            return [
                {
                    "id": str(doc.id),
                    "project": doc.project,
                    "description": doc.description,
                    "api_key": self.fernet.decrypt(doc.encrypted_key).decode(),
                    "active": doc.active,
                    "created_at": doc.created_at,
                    "internal": doc.internal,
                }
                for doc in docs
            ]
