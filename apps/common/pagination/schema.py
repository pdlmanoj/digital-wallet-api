from pydantic import BaseModel


class PaginationSchema(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class PaginatedResponseSchema[T](BaseModel):
    pagination: PaginationSchema
    results: list[T]
