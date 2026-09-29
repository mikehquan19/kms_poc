from typing import List
from fastapi import APIRouter, Depends

from app.dependency import get_book_service, require_api_key
from app.models import Book
from app.services import BookService

book_router = APIRouter(
    prefix="/books", tags=["books"], dependencies=[Depends(require_api_key)]
)


@book_router.get("", response_model=List[Book])
@book_router.get("/", response_model=List[Book], include_in_schema=False)
async def get_books(book_service: BookService = Depends(get_book_service)):
    return book_service.get_books()
