from typing import List
from fastapi import APIRouter, Depends

from app.dependency import get_plant_service, require_api_key
from app.models import Plant
from app.services import PlantService

plant_router = APIRouter(
    prefix="/plants", tags=["plants"], dependencies=[Depends(require_api_key)]
)


@plant_router.get("", response_model=List[Plant])
@plant_router.get("/", response_model=List[Plant], include_in_schema=False)
async def get_plants(plant_service: PlantService = Depends(get_plant_service)):
    return plant_service.get_plants()
