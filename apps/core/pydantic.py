from typing import TypeVar, List, Generic

from pydantic import BaseModel, ConfigDict


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


T = TypeVar("T", bound=BaseModel)


class PaginationSchema(Schema):
    page: int
    page_size: int
    total: int
    total_pages: int


class PaginatedResponseSchema(BaseModel, Generic[T]):
    pagination: PaginationSchema
    results: List[T]
