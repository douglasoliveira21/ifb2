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
def _authenticated(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("app.core.security.get_settings", lambda: Settings(admin_password="test-pass"))
    yield
    get_settings.cache_clear()


def test_trigger_claim_scan_returns_202_immediately_without_running_inline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"count": 0}

    def fake_main() -> None:
        calls["count"] += 1

    monkeypatch.setattr("app.sync.claim_scan.main", fake_main)

    response = client.post("/api/admin/claim-scan", headers=_basic_auth_header("admin", "test-pass"))

    assert response.status_code == 202
    assert response.json() == {"status": "iniciado"}
    assert calls["count"] == 1


def test_trigger_claim_scan_rejects_concurrent_calls_while_running(monkeypatch: pytest.MonkeyPatch) -> None:
    import app.api.admin as admin_module

    monkeypatch.setattr(admin_module, "_claim_scan_running", True)

    response = client.post("/api/admin/claim-scan", headers=_basic_auth_header("admin", "test-pass"))

    assert response.status_code == 409


def test_trigger_claim_scan_releases_lock_after_completion(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.sync.claim_scan.main", lambda: None)

    first = client.post("/api/admin/claim-scan", headers=_basic_auth_header("admin", "test-pass"))
    assert first.status_code == 202

    second = client.post("/api/admin/claim-scan", headers=_basic_auth_header("admin", "test-pass"))
    assert second.status_code == 202  # lock foi liberado após a primeira terminar
