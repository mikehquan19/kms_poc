import secrets
import hashlib
import os
from typing import Optional, Any
from datetime import datetime, timezone

from app.models import APIKey, APIKeyDTO
from app.repositories import APIKeyRepository, RedisCache
from app.constants import API_KEY_PREFIX

from dotenv import load_dotenv
import logging
from opentelemetry import trace

load_dotenv()


logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class APIKeyService:
    def __init__(
        self, repository: APIKeyRepository, cache: RedisCache, cache_ttl: int = 2 * 60
    ):
        self.repository = repository
        self.cache = cache
        self.cache_ttl = cache_ttl
        self.use_cache = os.getenv("USE_CACHE", "false").lower() == "true"

    def _hash_key(self, api_key: str) -> str:
        return hashlib.sha256(api_key.encode("utf-8")).hexdigest()

    def _insert_cache(self, doc: APIKey):
        try:
            self.cache.set(
                f"{API_KEY_PREFIX}:{doc.hashed_key}",
                doc.model_dump_json(),
                self.cache_ttl,
            )
            logger.info("Key inserted to cache")
        except Exception as e:
            logger.error(f"Failed to cache API key: {e}")

    def _delete_cache(self, key_hash: str):
        try:
            self.cache.delete(f"{API_KEY_PREFIX}:{key_hash}")
            logger.info("Key deleted from cache")
        except Exception as e:
            logger.error(f"Failed to delete cached API key: {e}")

    def create_key(
        self, project: str, description: str, internal: bool
    ) -> Optional[dict[str, Any]]:
        """
        Strategy for API key generation:
            - Format: `nebula_api_<32 bytes of base64-encoded string>`
            - Hash using SHA-256
            - Insert to MongoDB
            - Insert to Redis cache (expiring every 1.5 mins for testing)
        """
        with tracer.start_as_current_span("api_key.create"):
            api_key = f"nebula_api_{secrets.token_urlsafe(32)}"
            key_hash = self._hash_key(api_key)

            created_doc = self.repository.create(
                APIKey(
                    project=project,
                    description=description,
                    hashed_key=key_hash,
                    internal=internal,
                )
            )
            if created_doc is None:
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

            if self.use_cache:
                with tracer.start_as_current_span("redis.get_api_key") as span:
                    serialized = self.cache.get(f"{API_KEY_PREFIX}:{key_hash}")
                    if serialized:
                        # Cache hit
                        span.set_attribute("cache.hit", True)
                        logger.info("Key found in cache")
                        return APIKey.model_validate_json(serialized)
                    else:
                        span.set_attribute("cache.hit", False)

            # Cache miss
            with tracer.start_as_current_span("mongo.find_api_key"):
                doc = self.repository.find_by_hash(key_hash=key_hash)
                if not doc:
                    return None

            if self.use_cache and doc.active:
                # Cache misses because key expires
                with tracer.start_as_current_span("redis.set_api_key"):
                    self._insert_cache(doc)

            return doc.convert_dto()

    def revoke_key(self, key_id: str) -> Optional[APIKeyDTO]:
        with tracer.start_as_current_span("api_key.revoke"):
            with tracer.start_as_current_span("mongo.revoke_api_key") as span:
                doc = self.repository.revoke(key_id)
                if not doc:
                    return None

                span.set_attributes(
                    {
                        "api_key.revoked_at": doc.revoked_at,
                        "api_key.deleted_expected_at": doc.deleted_at,
                    }
                )

            if self.use_cache:
                with tracer.start_as_current_span("redis.delete_api_key"):
                    self._delete_cache(doc.hashed_key)

            return doc.convert_dto()

    def reactivate_key(self, key_id: str) -> Optional[APIKeyDTO]:
        with tracer.start_as_current_span("api_key.reactivate"):
            doc = self.repository.reactivate(key_id)
            if not doc:
                return None

            return doc.convert_dto()

    def force_delete_key(self, key_id: str) -> Optional[APIKeyDTO]:
        with tracer.start_as_current_span("api_key.force_delete"):
            with tracer.start_as_current_span("mongo.delete_api_key") as span:
                doc = self.repository.force_delete(key_id)
                if not doc:
                    return None

                span.set_attribute(
                    "api_key.force_deleted_at", datetime.now(timezone.utc)
                )

            if self.use_cache:
                with tracer.start_as_current_span("redis.delete_api_key"):
                    self._delete_cache(doc.hashed_key)

            return doc.convert_dto()
