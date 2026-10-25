import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.infrastructure.database import Base, get_db
from app.main import create_app

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite://")


@pytest.fixture
def db_session() -> Iterator[Session]:
    if TEST_DATABASE_URL.startswith("sqlite"):
        engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    else:
        engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def create_customer(client: TestClient):
    def _create(name: str = "Juan Pérez", email: str = "juan@example.com") -> dict:
        response = client.post("/customers", json={"name": name, "email": email})
        assert response.status_code == 201, response.text
        return response.json()["data"]

    return _create
