from typing import List

from opentelemetry import trace

from app.models import Vehicle
from app.repositories import VehicleRepository

tracer = trace.get_tracer(__name__)


class VehicleService:
    def __init__(self, repository: VehicleRepository):
        self.repository = repository

    def get_vehicles(self) -> List[Vehicle]:
        with tracer.start_as_current_span("vehicle.find"):
            vehicles = self.repository.find()
            return vehicles
