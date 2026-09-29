from typing import List
from pymongo.collection import Collection
from app.models import Book


class BookRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def find(self) -> List[Book]:
        docs = self.collection.find()
        return [Book(**doc) for doc in docs]
