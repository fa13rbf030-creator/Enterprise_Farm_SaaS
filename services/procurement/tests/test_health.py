from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from procurement_service.db.session import get_db_session
from procurement_service.main import app


def test_health_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "procurement",
        "environment": "development",
    }


def test_ready_checks_database() -> None:
    session = AsyncMock()

    async def override_get_db_session():
        yield session

    app.dependency_overrides[get_db_session] = (
        override_get_db_session
    )

    try:
        with TestClient(app) as client:
            response = client.get("/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "service": "procurement",
    }

    session.execute.assert_awaited_once()


def test_ready_returns_503_when_database_unavailable() -> None:
    session = AsyncMock()
    session.execute.side_effect = SQLAlchemyError(
        "database unavailable"
    )

    async def override_get_db_session():
        yield session

    app.dependency_overrides[get_db_session] = (
        override_get_db_session
    )

    try:
        with TestClient(
            app,
            raise_server_exceptions=False,
        ) as client:
            response = client.get("/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "detail": "procurement database is unavailable",
    }
