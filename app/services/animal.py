from typing import List
from app.models import Animal
from app.repositories import AnimalRepository

from opentelemetry import trace

tracer = trace.get_tracer(__name__)


class AnimalService:
    def __init__(self, repository: AnimalRepository):
        self.repository = repository

    def get_animals(self) -> List[Animal]:
        with tracer.start_as_current_span("animal.find"):
            return self.repository.find()
