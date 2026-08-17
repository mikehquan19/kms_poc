import os
import logging
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import APIKeyHeader

from app.models import APIKey, APIKeyDTO
from app.repositories import MongoDB, RedisCache, APIKeyRepository, AnimalRepository
from app.services import APIKeyService, AnimalService
from app.constants import (
    DEFAULT_MONGO_URL,
    API_KEY_COLLECTION,
    ANIMAL_COLLECTION,
    DEFAULT_REDIS_HOST,
    DEFAULT_REDIS_PORT,
    DEFAULT_REDIS_USERNAME,
    DEFAULT_REDIS_PASSWORD,
)

logging.basicConfig(
    level=logging.INFO,
    format="\033[32m%(levelname)s\033[0m:     %(message)s",
)
logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name="x-api-key", auto_error=True)
mongo_conn = MongoDB(os.getenv("MONGO_URL", DEFAULT_MONGO_URL))
cache = RedisCache(
    os.getenv("REDIS_HOST", DEFAULT_REDIS_HOST),
    os.getenv("REDIS_PORT", DEFAULT_REDIS_PORT),
    os.getenv("REDIS_USERNAME", DEFAULT_REDIS_USERNAME),
    os.getenv("REDIS_PASSWORD", DEFAULT_REDIS_PASSWORD),
)


def get_api_key_repository() -> APIKeyRepository:
    """API key repo dependency"""
    collection = mongo_conn.get_collection(API_KEY_COLLECTION)
    return APIKeyRepository(collection)


def get_animal_repository() -> AnimalRepository:
    """Animal repo dependency"""
    collection = mongo_conn.get_collection(ANIMAL_COLLECTION)
    return AnimalRepository(collection)


def get_api_key_service(
    repository: APIKeyRepository = Depends(get_api_key_repository),
) -> APIKeyService:
    """API key service dependency"""
    return APIKeyService(repository, cache)


def get_animal_service(
    repository: AnimalRepository = Depends(get_animal_repository),
) -> AnimalService:
    """Animal service dependency"""
    return AnimalService(repository)


def require_api_key(
    key: str = Security(api_key_header),
    service: APIKeyService = Depends(get_api_key_service),
) -> APIKeyDTO:
    """Dependency injected to endpoint that requires API Key"""
    api_key_doc = service.validate_key(key)
    if api_key_doc is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your API key is invalid",
        )

    if not api_key_doc.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your API key has been revoked. Please contact us",
        )

    return api_key_doc


def require_internal_api_key(
    api_key_doc: APIKeyDTO = Depends(require_api_key),
) -> APIKeyDTO:
    """Dependency injected to endpoint that requires internal API Key"""
    if not api_key_doc.internal:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your API key doesn't have access to this. Please contact us",
        )

    return api_key_doc
