import pytest
from fastapi.testclient import TestClient

from app.main import app

pytestmark = pytest.mark.integration


@pytest.fixture
def client():
    return TestClient(app)


def _register(client: TestClient, *, email: str, password: str) -> None:
    resp = client.post("/auth/register", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text


def _login(client: TestClient, *, email: str, password: str) -> str:
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


class TestTodosIntegration:
    def test_full_flow_create_list_toggle_delete(self, client: TestClient):
        _register(client, email="todo@example.com", password="Strong_password_123!")
        token = _login(client, email="todo@example.com", password="Strong_password_123!")
        headers = {"Authorization": f"Bearer {token}"}

        create = client.post("/todos", json={"title": "第一个待办", "group_id": None}, headers=headers)
        assert create.status_code == 200, create.text
        todo_id = create.json()["id"]

        lst = client.get("/todos", headers=headers)
        assert lst.status_code == 200, lst.text
        ids = [t["id"] for t in lst.json()]
        assert todo_id in ids

        toggle = client.patch(f"/todos/{todo_id}/toggle", headers=headers)
        assert toggle.status_code == 200, toggle.text
        assert toggle.json()["completed"] is True

        delete = client.delete(f"/todos/{todo_id}", headers=headers)
        assert delete.status_code == 200, delete.text
        assert delete.json()["ok"] is True

    def test_user_isolation(self, client: TestClient):
        _register(client, email="u1@example.com", password="Strong_password_123!")
        _register(client, email="u2@example.com", password="Strong_password_123!")

        token1 = _login(client, email="u1@example.com", password="Strong_password_123!")
        token2 = _login(client, email="u2@example.com", password="Strong_password_123!")

        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}

        todo = client.post("/todos", json={"title": "u1 的待办", "group_id": None}, headers=headers1).json()

        not_found = client.patch(f"/todos/{todo['id']}/toggle", headers=headers2)
        assert not_found.status_code == 404

        delete = client.delete(f"/todos/{todo['id']}", headers=headers2)
        assert delete.status_code == 200
        assert delete.json()["ok"] is True

