from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from finance_service.db.session import get_db_session
from finance_service.main import app


def test_health_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["service"] == "finance"
    assert response.json()["status"] == "ok"


def test_ready_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "service": "finance",
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
        "service": "finance",
    }

    session.execute.assert_awaited_once()


def test_ready_returns_503_when_database_unavailable() -> None:
    session = AsyncMock()
    session.execute.side_effect = RuntimeError(
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
        "detail": "finance database is unavailable",
    }

    session.execute.assert_awaited_once()
