from typing import TypeVar

from pydantic import BaseModel, ConfigDict


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


T = TypeVar("T", bound=BaseModel)


class PaginationSchema(Schema):
    page: int
    page_size: int
    total: int
    total_pages: int


class PaginatedResponseSchema[T](BaseModel):
    pagination: PaginationSchema
    results: list[T]
