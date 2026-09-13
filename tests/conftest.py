import pytest
import requests_mock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.core.config import test_settings
from apps.db.session import Base, get_db
from apps.main import app

DATABASE_URL = test_settings.test_database_url.unicode_string()


@pytest.fixture(scope="session")
def pg_engine_maker():
    engine = create_engine(url=DATABASE_URL)
    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture(scope="function")
def pg_db(pg_engine_maker):

    TestSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=pg_engine_maker
    )

    session = TestSessionLocal()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(pg_db):

    def override_get_db():
        yield pg_db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def mock_requests():
    """create mock HTTP environment"""
    with requests_mock.Mocker() as req_mock:
        yield req_mock


@pytest.fixture(scope="function")
def monkey_patch():
    mon_patch = pytest.MonkeyPatch()
    try:
        yield mon_patch
    finally:
        mon_patch.undo()
