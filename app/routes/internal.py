from fastapi import APIRouter, Depends

from app.dependency import require_internal_api_key

internal_router = APIRouter(
    prefix="/internal",
    tags=["internal"],
    dependencies=[Depends(require_internal_api_key)],
)


@internal_router.get("/")
def get_internal():
    return {
        "message": "This is internal information",
    }
