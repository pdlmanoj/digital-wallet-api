from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import create_engine, func
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declared_attr,
    mapped_column,
    sessionmaker,
)

from apps.core.config import settings

engine = create_engine(url=settings.database_url.unicode_string())

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        return mapped_column(
            server_default=func.now(),
            deferred=True,
            deferred_raiseload=True,
            deferred_group="timestamps",
        )

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:
        return mapped_column(
            server_default=func.now(),
            onupdate=func.now(),
            deferred=True,
            deferred_raiseload=True,
            deferred_group="timestamps",
        )


def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def get_db_context():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
