from fastapi import APIRouter, Depends, status, HTTPException

from pydantic import BaseModel

from app.dependency import get_api_key_service
from app.services import APIKeyService

api_key_router = APIRouter(prefix="/keys", tags=["keys"])


class CreateAPIKeyRequest(BaseModel):
    project: str
    description: str
    internal: bool


@api_key_router.post("/")
async def create_key(
    request: CreateAPIKeyRequest,
    api_key_service: APIKeyService = Depends(get_api_key_service),
):
    dto = api_key_service.create_key(
        request.project, request.description, request.internal
    )
    if not dto:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Can not create the key"},
        )
    return dto


class RevokeAPIKeyRequest(BaseModel):
    key_id: str


@api_key_router.post("/revoke/")
async def revoke_key(
    request: RevokeAPIKeyRequest,
    api_key_service: APIKeyService = Depends(get_api_key_service),
):
    dto = api_key_service.revoke_key(request.key_id)
    if not dto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Key not found"},
        )
    return dto


@api_key_router.post("/reactivate/")
async def reactivate_key(
    request: RevokeAPIKeyRequest,
    api_key_service: APIKeyService = Depends(get_api_key_service),
):
    dto = api_key_service.reactivate_key(request.key_id)
    if not dto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Key not found"},
        )
    return dto


@api_key_router.post("/force-delete/")
async def force_delete_key(
    request: RevokeAPIKeyRequest,
    api_key_service: APIKeyService = Depends(get_api_key_service),
):
    dto = api_key_service.force_delete_key(request.key_id)
    if not dto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Key not found"},
        )
    return dto
