import secrets
import hashlib
import os
from typing import Any, Optional

from app.models import APIKey
from app.repositories import APIKeyRepository, RedisCache
from app.constants import API_KEY_PREFIX

from dotenv import load_dotenv
load_dotenv()

import logging
logger = logging.getLogger(__name__)

from opentelemetry import trace
tracer = trace.get_tracer(__name__)

class APIKeyService:
    def __init__(
        self, 
        repository: APIKeyRepository, 
        cache: RedisCache, 
        cache_ttl: int = 30, # Configurable here
    ):
        self.repository = repository
        self.cache = cache
        self.cache_ttl = cache_ttl
        self.use_cache = os.getenv("USE_CACHE", "false").lower() == "true"

    def _hash_key(self, api_key: str) -> str:
        return hashlib.sha256(api_key.encode("utf-8")).hexdigest()

    def _insert_cache(self, key_hash: str, doc: APIKey):
        try:
            self.cache.set(
                f"{API_KEY_PREFIX}:{key_hash}",
                doc.model_dump_json(),
                self.cache_ttl
            )
            logger.info("Key inserted to cache")
        except Exception:
            logger.info("Failed to cache API key")

    def create_key(self, project: str, description: str) -> Optional[dict[str, Any]]:
        """
        Strategy for API key generation:
            - Format: `nebula_api_<32 bytes of base64-encoded string>`
            - Hash using SHA-256
            - Insert to MongoDB
            - Insert to Redis cache (expiring every 30 secs for testing)
        """
        with tracer.start_as_current_span("api_key.create"):
            api_key = f"nebula_api_{secrets.token_urlsafe(32)}"
            key_hash = self._hash_key(api_key)

            with tracer.start_as_current_span("mongo.insert_api_key"):
                created_doc = self.repository.create(APIKey(
                    project=project,
                    description=description,
                    hashed_key=key_hash,
                ))
                if created_doc is None:
                    return None

            if self.use_cache:
                with tracer.start_as_current_span("redis.set_api_key"):
                    self._insert_cache(key_hash, created_doc)

            return {
                "project": created_doc.project,
                "description": created_doc.description,
                "api_key": api_key,
                "active": created_doc.active,
                "created_at": created_doc.created_at,
            }

    def validate_key(self, api_key: str) -> Optional[APIKey]:
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

            # Cache misses probably because of expiry
            if self.use_cache and doc is not None and doc.active:
                with tracer.start_as_current_span("redis.set_api_key"):
                    self._insert_cache(key_hash, doc)

            return doc

    def revoke_key(self, key_id: str) -> bool:
        with tracer.start_as_current_span("api_key.revoke"):
            with tracer.start_as_current_span("mongo.revoke_api_key"):
                doc = self.repository.revoke(key_id)
                if doc is None:
                    return False

            if self.use_cache:
                with tracer.start_as_current_span("redis.delete_api_key"):
                    self.cache.delete(f"{API_KEY_PREFIX}:{doc.hashed_key}")
                    logger.info("Key deleted from cache")

            return True
        