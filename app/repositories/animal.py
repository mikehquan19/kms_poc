from typing import List
from pymongo.collection import Collection
from app.models import Animal


class AnimalRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def find(self) -> List[Animal]:
        docs = self.collection.find()
        return [Animal(**doc) for doc in docs]

    def create(self, animal: Animal) -> Animal:
        doc = animal.model_dump(mode="json")
        self.collection.insert_one(doc)
        return animal
