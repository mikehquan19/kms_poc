from typing import List
from fastapi import APIRouter, Depends

from app.dependency import get_vehicle_service, require_api_key
from app.models import Vehicle
from app.services import VehicleService

vehicle_router = APIRouter(
    prefix="/vehicles", tags=["vehicles"], dependencies=[Depends(require_api_key)]
)


@vehicle_router.get("", response_model=List[Vehicle])
@vehicle_router.get("/", response_model=List[Vehicle], include_in_schema=False)
async def get_vehicles(vehicle_service: VehicleService = Depends(get_vehicle_service)):
    return vehicle_service.get_vehicles()
