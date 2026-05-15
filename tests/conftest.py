import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from src.database.session import get_session
from src.main import create_app


@pytest.fixture(name="client")
def client_fixture():
    app = create_app(init_database=False)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def get_test_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
