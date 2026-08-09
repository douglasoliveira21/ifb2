import base64

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app

client = TestClient(app)


def _basic_auth_header(username: str, password: str) -> dict[str, str]:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_admin_unreachable_without_password_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.core.security.get_settings",
        lambda: Settings(admin_password=None),
    )

    response = client.get("/api/admin/indicators", headers=_basic_auth_header("admin", "whatever"))

    assert response.status_code == 503


def test_admin_rejects_wrong_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.core.security.get_settings",
        lambda: Settings(admin_password="correct-horse"),
    )

    response = client.get("/api/admin/indicators", headers=_basic_auth_header("admin", "wrong"))

    assert response.status_code == 401


def test_admin_rejects_missing_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.core.security.get_settings",
        lambda: Settings(admin_password="correct-horse"),
    )

    response = client.get("/api/admin/indicators")

    assert response.status_code == 401
