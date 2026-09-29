from typing import List
from pymongo.collection import Collection
from app.models import Vehicle


class VehicleRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def find(self) -> List[Vehicle]:
        docs = self.collection.find()
        return [Vehicle(**doc) for doc in docs]
