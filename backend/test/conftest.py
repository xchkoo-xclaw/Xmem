"""
Pytest 配置文件
"""
import asyncio
import pytest
from pathlib import Path
import os
import sys
import io
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock
from PIL import Image

# 添加项目根目录到 Python 路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# 允许不显式设置时也能跑测试（CI / Testcontainers 会覆盖）
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("OCR_PROVIDER", "local")

# 测试图片目录
TEST_IMG_DIR = Path(__file__).parent / "img"

_POSTGRES_CONTAINER = None
_TESTCONTAINERS_ENABLED = False


def _is_truthy_env(name: str) -> bool:
    """判断环境变量是否为真值（1/true/yes/on）。"""
    value = os.getenv(name)
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _is_ci() -> bool:
    """判断是否运行在 CI 环境（兼容 GitHub Actions）。"""
    return _is_truthy_env("CI") or _is_truthy_env("GITHUB_ACTIONS")


def pytest_addoption(parser):
    parser.addoption(
        "--no-testcontainers",
        action="store_true",
        default=False,
        help="Disable Postgres testcontainers for integration tests.",
    )


def _build_asyncpg_url(sync_url: str) -> str:
    if sync_url.startswith("postgresql+asyncpg://"):
        return sync_url
    if sync_url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + sync_url.removeprefix("postgresql://")
    return sync_url


async def _init_schema():
    __import__("app.models")
    from app.db import Base, engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def pytest_configure(config):
    global _POSTGRES_CONTAINER, _TESTCONTAINERS_ENABLED

    if config.getoption("--no-testcontainers"):
        if _is_ci():
            raise pytest.UsageError("CI 环境不允许禁用 PostgreSQL Testcontainers（--no-testcontainers）。")
        return

    try:
        from testcontainers.postgres import PostgresContainer
    except Exception as e:
        if _is_ci():
            raise pytest.UsageError(f"CI 环境需要 PostgreSQL Testcontainers，但 testcontainers 不可用：{e}") from e
        return

    try:
        container = PostgresContainer("postgres:16")
        container.start()
        _POSTGRES_CONTAINER = container

        asyncpg_url = _build_asyncpg_url(container.get_connection_url())
        os.environ["DATABASE_URL"] = asyncpg_url
        os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
        os.environ.setdefault("ALLOW_INSECURE_HTTP", "true")

        asyncio.run(_init_schema())
        _TESTCONTAINERS_ENABLED = True
    except Exception as e:
        try:
            if _POSTGRES_CONTAINER is not None:
                _POSTGRES_CONTAINER.stop()
        finally:
            _POSTGRES_CONTAINER = None
            _TESTCONTAINERS_ENABLED = False
        if _is_ci():
            raise pytest.UsageError(f"CI 环境启动 PostgreSQL Testcontainers 失败：{e}") from e


def pytest_sessionfinish(session, exitstatus):
    global _POSTGRES_CONTAINER
    if _POSTGRES_CONTAINER is None:
        return
    try:
        _POSTGRES_CONTAINER.stop()
    finally:
        _POSTGRES_CONTAINER = None


def pytest_collection_modifyitems(config, items):
    if _TESTCONTAINERS_ENABLED:
        return
    if config.getoption("--no-testcontainers"):
        return
    if _is_ci() and any("integration" in item.keywords for item in items):
        raise pytest.UsageError(
            "CI 环境检测到 integration 测试，但 PostgreSQL Testcontainers 未启用/不可用；请确保 Docker 可用并允许测试拉起容器。"
        )
    skip_integration = pytest.mark.skip(reason="PostgreSQL testcontainers not available")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


@pytest.fixture
def test_img_dir():
    """返回测试图片目录路径"""
    return TEST_IMG_DIR


@pytest.fixture
def sample_image_path(test_img_dir):
    """返回示例图片路径（如果存在）"""
    # 查找目录中的第一个图片文件
    image_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".gif"]
    for ext in image_extensions:
        for img_file in test_img_dir.glob(f"*{ext}"):
            return str(img_file)
        for img_file in test_img_dir.glob(f"*{ext.upper()}"):
            return str(img_file)
    return None


@pytest.fixture
def sample_image_bytes():
    """创建测试图片字节流"""
    # 创建一个简单的测试图片（100x100 像素的 PNG）
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes


@pytest.fixture
def mock_user():
    """模拟用户对象"""
    user = MagicMock()
    user.id = 1
    user.email = "test@example.com"
    user.user_name = "Test User"
    return user


@pytest.fixture
def mock_ledger_entry():
    """模拟 LedgerEntry 对象"""
    from app import models
    entry = models.LedgerEntry(
        id=1,
        user_id=1,
        raw_text="测试文本",
        status="pending",
        amount=None,
        currency="CNY",
        category=None,
        merchant=None,
        event_time=None,
        meta=None,
        task_id=None,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        updated_at=None
    )
    return entry


@pytest.fixture
def mock_async_session():
    """模拟异步数据库会话"""
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.query = MagicMock()
    return session


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """为测试设置环境变量"""
    # 设置测试环境变量，避免影响实际配置
    monkeypatch.setenv("OCR_PROVIDER", "local")
    # 如果 TESSERACT_CMD 未设置，尝试使用系统默认路径
    if not os.getenv("TESSERACT_CMD"):
        # 不设置，让代码使用系统默认路径
        pass


@pytest.fixture(autouse=True)
async def reset_db_between_tests():
    if not _TESTCONTAINERS_ENABLED:
        return
    __import__("app.models")
    from app.db import Base, engine

    table_names = [t.name for t in Base.metadata.sorted_tables]
    if not table_names:
        return

    quoted = ", ".join(f"\"{name}\"" for name in table_names)
    async with engine.begin() as conn:
        await conn.exec_driver_sql(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE")
