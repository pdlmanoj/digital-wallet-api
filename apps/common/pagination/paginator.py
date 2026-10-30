from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session


class Paginator:
    def __init__(self, db: Session, page: int, page_size: int):
        self.db = db
        self.page = page
        self.page_size = page_size

    def _get_offset(self) -> int:
        return (self.page - 1) * self.page_size

    def _get_total_pages(self, query: Select) -> int:
        count = (
            self.db.scalar(
                select(func.count()).select_from(query.order_by(None).subquery())
            )
            or 0
        )
        return count

    def _get_results(self, query: Select):
        offset = self._get_offset()
        return self.db.scalars(query.offset(offset).limit(self.page_size)).all()

    def paginated_response(self, query: Select):
        count = self._get_total_pages(query)
        total_pages = (int(count) + self.page_size - 1) // self.page_size
        results = self._get_results(query)
        pagination = {
            "page": self.page,
            "page_size": self.page_size,
            "total": count,
            "total_pages": total_pages,
        }
        response = {
            "pagination": pagination,
            "results": results,
        }

        return response
