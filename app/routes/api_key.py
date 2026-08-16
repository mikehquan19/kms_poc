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
def create_key(
    request: CreateAPIKeyRequest,
    api_key_service: APIKeyService = Depends(get_api_key_service),
):
    json = api_key_service.create_key(
        request.project, request.description, request.internal
    )
    if json is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Can not create the key",
        )
    return json


class RevokeAPIKeyRequest(BaseModel):
    key_id: str


@api_key_router.post("/revoke/")
def revoke_key(
    request: RevokeAPIKeyRequest,
    api_key_service: APIKeyService = Depends(get_api_key_service),
):
    acknowledged = api_key_service.revoke_key(request.key_id)
    if not acknowledged:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Can not revoke the key",
        )
    return acknowledged
