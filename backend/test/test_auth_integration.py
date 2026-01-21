import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db import get_session
from app.auth import get_current_user


@pytest.fixture
def client():
    return TestClient(app)


def _register(client: TestClient, *, email: str, password: str, user_name: str | None = None) -> dict:
    payload: dict = {"email": email, "password": password}
    if user_name is not None:
        payload["user_name"] = user_name
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()


def _login(client: TestClient, *, email: str, password: str) -> str:
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "access_token" in data
    return data["access_token"]


class TestAuthIntegration:
    def test_register_login_me(self, client: TestClient):
        user = _register(
            client,
            email="newuser@example.com",
            password="Strong_password_123!",
            user_name="New User",
        )
        token = _login(client, email="newuser@example.com", password="Strong_password_123!")

        me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200, me.text
        me_data = me.json()
        assert me_data["id"] == user["id"]
        assert me_data["email"] == "newuser@example.com"

    def test_change_password_flow(self, client: TestClient):
        _register(client, email="test@example.com", password="Old_password_123!", user_name="Test")
        token = _login(client, email="test@example.com", password="Old_password_123!")

        change = client.post(
            "/auth/change-password",
            json={"old_password": "Old_password_123!", "new_password": "New_password_123!"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert change.status_code == 200, change.text
        assert "成功" in change.json()["message"]

        token2 = _login(client, email="test@example.com", password="New_password_123!")
        me2 = client.get("/auth/me", headers={"Authorization": f"Bearer {token2}"})
        assert me2.status_code == 200, me2.text
        assert me2.json()["email"] == "test@example.com"


class TestAuthErrorScenarios:
    def test_register_then_login_with_wrong_password(self, client: TestClient):
        _register(client, email="user@example.com", password="Strong_password_123!")
        resp = client.post(
            "/auth/login",
            json={"email": "user@example.com", "password": "wrong_password"},
        )
        assert resp.status_code == 401

    def test_duplicate_register(self, client: TestClient):
        _register(client, email="dup@example.com", password="Strong_password_123!")
        resp = client.post(
            "/auth/register",
            json={"email": "dup@example.com", "password": "Strong_password_123!"},
        )
        assert resp.status_code == 400


class TestAuthUserIsolation:
    def test_tokens_map_to_correct_user(self, client: TestClient):
        _register(client, email="user1@example.com", password="Strong_password_123!")
        _register(client, email="user2@example.com", password="Strong_password_123!")

        token1 = _login(client, email="user1@example.com", password="Strong_password_123!")
        token2 = _login(client, email="user2@example.com", password="Strong_password_123!")

        me1 = client.get("/auth/me", headers={"Authorization": f"Bearer {token1}"})
        me2 = client.get("/auth/me", headers={"Authorization": f"Bearer {token2}"})
        assert me1.status_code == 200
        assert me2.status_code == 200
        assert me1.json()["email"] == "user1@example.com"
        assert me2.json()["email"] == "user2@example.com"

