from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.repositories import MongoDB, RedisCache, APIKeyRepository, AnimalRepository
from app.services import APIKeyService, AnimalService
from app.constants import (
    DEFAULT_MONGO_URL,
    API_KEY_COLLECTION,
    ANIMAL_COLLECTION,
    DEFAULT_REDIS_HOST,
    DEFAULT_REDIS_PORT,
)

import os

import logging

logging.basicConfig(
    level=logging.INFO,
    format="\033[32m%(levelname)s\033[0m:     %(message)s",
)
logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)
conn = MongoDB(os.getenv("MONGO_URL", DEFAULT_MONGO_URL))
cache = RedisCache(
    os.getenv("REDIS_HOST", DEFAULT_REDIS_HOST),
    os.getenv("REDIS_PORT", DEFAULT_REDIS_PORT),
)


def get_api_key_repository() -> APIKeyRepository:
    collection = conn.get_collection(API_KEY_COLLECTION)
    return APIKeyRepository(collection)


def get_animal_repository() -> AnimalRepository:
    collection = conn.get_collection(ANIMAL_COLLECTION)
    return AnimalRepository(collection)


def get_api_key_service(
    repository: APIKeyRepository = Depends(get_api_key_repository),
) -> APIKeyService:
    return APIKeyService(repository, cache)


def get_animal_service(
    repository: AnimalRepository = Depends(get_animal_repository),
) -> AnimalService:
    return AnimalService(repository)


def require_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service: APIKeyService = Depends(get_api_key_service),
):
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication",
            headers={"WWW-Authenticate": "Bearer"},
        )

    api_key_doc = service.validate_key(credentials.credentials)
    if api_key_doc is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your API key is invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not api_key_doc.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your API key has been revoked. Please contact us",
            headers={"WWW-Authenticate": "Bearer"},
        )
