from fastapi import APIRouter, Depends
from typing import List

from app.models.animal import Animal
from app.dependency import get_animal_service, require_api_key
from app.services import AnimalService

animal_router = APIRouter(
    prefix="/animals", tags=["animals"], dependencies=[Depends(require_api_key)]
)


@animal_router.get(
    "",
    response_model=List[Animal],
)
@animal_router.get(
    "/",
    response_model=List[Animal],
    include_in_schema=False,
)
def get_animals(
    animal_service: AnimalService = Depends(get_animal_service),
):
    return animal_service.get_animals()
