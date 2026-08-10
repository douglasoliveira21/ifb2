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


def test_trigger_sync_returns_202_immediately_without_running_sync_inline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A chamada não deve bloquear esperando `run_sync()` terminar — só
    agendar. Um `run_sync` que nunca retorna (While True) provaria isso
    travando o teste; em vez disso, usamos um contador para confirmar que
    foi chamado, sem depender de tempo real."""
    calls = {"count": 0}

    def fake_main() -> None:
        calls["count"] += 1

    monkeypatch.setattr("app.sync.run.main", fake_main)

    response = client.post("/api/admin/sync", headers=_basic_auth_header("admin", "test-pass"))

    assert response.status_code == 202
    assert response.json() == {"status": "iniciado"}
    assert calls["count"] == 1


def test_trigger_sync_rejects_concurrent_calls_while_running(monkeypatch: pytest.MonkeyPatch) -> None:
    """Enquanto uma sync está marcada como em andamento, uma segunda
    chamada deve ser rejeitada com 409 em vez de empilhar sync duplicada."""
    import app.api.admin as admin_module

    monkeypatch.setattr(admin_module, "_sync_running", True)

    response = client.post("/api/admin/sync", headers=_basic_auth_header("admin", "test-pass"))

    assert response.status_code == 409


def test_trigger_sync_releases_lock_after_completion(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.sync.run.main", lambda: None)

    first = client.post("/api/admin/sync", headers=_basic_auth_header("admin", "test-pass"))
    assert first.status_code == 202

    second = client.post("/api/admin/sync", headers=_basic_auth_header("admin", "test-pass"))
    assert second.status_code == 202  # lock foi liberado após a primeira terminar
