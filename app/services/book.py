from typing import List

from opentelemetry import trace

from app.models import Book
from app.repositories import BookRepository

tracer = trace.get_tracer(__name__)


class BookService:
    def __init__(self, repository: BookRepository):
        self.repository = repository

    def get_books(self) -> List[Book]:
        with tracer.start_as_current_span("book.find"):
            books = self.repository.find()
            return books
