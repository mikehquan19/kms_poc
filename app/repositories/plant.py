from typing import List
from pymongo.collection import Collection
from app.models import Plant


class PlantRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def find(self) -> List[Plant]:
        docs = self.collection.find()
        return [Plant(**doc) for doc in docs]
