"""Tests for session provisioning endpoints."""

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from backend.database import get_db
from backend.main import app
from backend.models.models import ActiveSession, LabTemplate


client = TestClient(app)


def test_create_session_returns_details(monkeypatch):
    """POST /sessions should create a session record and return metadata."""
    fake_db = MagicMock()
    fake_template = LabTemplate(
        id=1,
        name="Kali Lab",
        image_tag="kalilinux/kali-rolling:latest",
        cpu_limit="0.5",
        ram_limit="256m",
    )
    fake_db.query.return_value.filter.return_value.first.return_value = (
        fake_template
    )

    def fake_get_free_port() -> int:
        return 16000

    def fake_spawn_container(
        image_tag: str,
        cpu_limit: str,
        ram_limit: str,
        port: int,
    ) -> str:
        return "container-123"

    monkeypatch.setattr("backend.api.sessions.get_free_port", fake_get_free_port)
    monkeypatch.setattr(
        "backend.api.sessions.spawn_container",
        fake_spawn_container,
    )
    app.dependency_overrides[get_db] = lambda: fake_db

    response = client.post(
        "/sessions",
        json={"template_id": 1, "user_id": 2},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["template_id"] == 1
    assert payload["user_id"] == 2
    assert payload["container_id"] == "container-123"
    assert payload["port"] == 16000
    assert payload["access_url"] == "http://localhost:16000"
    fake_db.add.assert_called_once()
    fake_db.commit.assert_called_once()


def test_delete_session_removes_record(monkeypatch):
    """DELETE /sessions/{id} should stop the container and delete the record."""
    fake_db = MagicMock()
    fake_session = ActiveSession(
        id=7,
        user_id=2,
        template_id=1,
        container_id="container-456",
        port=17000,
    )
    fake_db.query.return_value.filter.return_value.first.return_value = (
        fake_session
    )

    def fake_kill_container(container_id: str) -> None:
        return None

    monkeypatch.setattr("backend.api.sessions.kill_container", fake_kill_container)
    app.dependency_overrides[get_db] = lambda: fake_db

    response = client.delete("/sessions/7")

    assert response.status_code == 200
    assert response.json()["message"] == "Session deleted successfully"
    fake_db.delete.assert_called_once_with(fake_session)
    fake_db.commit.assert_called_once()
