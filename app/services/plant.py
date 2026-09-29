from typing import List

from opentelemetry import trace

from app.models import Plant
from app.repositories import PlantRepository

tracer = trace.get_tracer(__name__)


class PlantService:
    def __init__(self, repository: PlantRepository):
        self.repository = repository

    def get_plants(self) -> List[Plant]:
        with tracer.start_as_current_span("plant.find"):
            return self.repository.find()
