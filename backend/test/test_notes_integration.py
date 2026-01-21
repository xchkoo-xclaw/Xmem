import asyncio

import pytest
from fastapi.testclient import TestClient

from app.main import app

pytestmark = pytest.mark.integration


@pytest.fixture
def client():
    """创建 FastAPI 测试客户端。"""
    return TestClient(app)


def _register(client: TestClient, *, email: str, password: str) -> dict:
    """注册一个新用户并返回响应 JSON。"""
    resp = client.post("/auth/register", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _login(client: TestClient, *, email: str, password: str) -> str:
    """登录并返回 access_token。"""
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _count_files_by_url(url_path: str) -> int:
    """按 url_path 统计 files 表记录数量。"""

    async def _run() -> int:
        from sqlalchemy import select, func
        from app.db import AsyncSessionLocal
        from app import models

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(func.count(models.File.id)).where(models.File.url_path == url_path)
            )
            return int(result.scalar() or 0)

    return asyncio.run(_run())


class TestNotesIntegration:
    def test_full_flow_create_list_update_delete(self, client: TestClient):
        """测试笔记完整流程：创建 -> 列表 -> 更新 -> 删除。"""
        _register(client, email="note@example.com", password="Strong_password_123!")
        token = _login(client, email="note@example.com", password="Strong_password_123!")
        headers = {"Authorization": f"Bearer {token}"}

        create = client.post(
            "/notes",
            json={"body_md": "# 测试笔记", "images": None, "files": None},
            headers=headers,
        )
        assert create.status_code == 200, create.text
        note_id = create.json()["id"]

        lst = client.get("/notes", headers=headers)
        assert lst.status_code == 200, lst.text
        ids = [n["id"] for n in lst.json()]
        assert note_id in ids

        update = client.patch(
            f"/notes/{note_id}",
            json={"body_md": "更新后的内容", "images": None, "files": None},
            headers=headers,
        )
        assert update.status_code == 200, update.text
        assert update.json()["id"] == note_id
        assert update.json()["body_md"] == "更新后的内容"

        delete = client.delete(f"/notes/{note_id}", headers=headers)
        assert delete.status_code == 200, delete.text
        assert delete.json()["ok"] is True

    def test_full_flow_with_pin_and_search(self, client: TestClient):
        """测试置顶与搜索：置顶一个笔记并验证排序/搜索结果。"""
        _register(client, email="pin@example.com", password="Strong_password_123!")
        token = _login(client, email="pin@example.com", password="Strong_password_123!")
        headers = {"Authorization": f"Bearer {token}"}

        n1 = client.post(
            "/notes",
            json={"body_md": "置顶笔记内容", "images": None, "files": None},
            headers=headers,
        ).json()
        n2 = client.post(
            "/notes",
            json={"body_md": "普通笔记内容", "images": None, "files": None},
            headers=headers,
        ).json()

        pin = client.patch(f"/notes/{n2['id']}/pin", headers=headers)
        assert pin.status_code == 200, pin.text
        assert pin.json()["is_pinned"] is True

        lst = client.get("/notes", headers=headers)
        assert lst.status_code == 200
        notes = lst.json()
        assert notes[0]["is_pinned"] is True

        search = client.get("/notes?q=置顶", headers=headers)
        assert search.status_code == 200, search.text
        results = search.json()
        assert len(results) == 1
        assert results[0]["id"] == n1["id"]

    def test_full_flow_with_upload(self, client: TestClient, sample_image_bytes, monkeypatch):
        """测试图片上传与 files 表落库记录。"""
        _register(client, email="upload@example.com", password="Strong_password_123!")
        token = _login(client, email="upload@example.com", password="Strong_password_123!")
        headers = {"Authorization": f"Bearer {token}"}

        async def fake_save_uploaded_img(_file, _dir):
            """伪造保存上传图片返回路径。"""
            return "uploads/images/test.jpg"

        monkeypatch.setattr("app.routers.notes.save_uploaded_img", fake_save_uploaded_img)

        upload = client.post(
            "/notes/upload-image",
            files={"file": ("test.png", sample_image_bytes, "image/png")},
            headers=headers,
        )
        assert upload.status_code == 200, upload.text
        image_url = upload.json()["url"]

        assert _count_files_by_url(image_url) == 1

        create = client.post(
            "/notes",
            json={"body_md": f"![图片]({image_url})", "images": [image_url], "files": None},
            headers=headers,
        )
        assert create.status_code == 200, create.text
        note = create.json()
        assert image_url in (note.get("images") or [])

