import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.main import app
from app.database import get_session
from app.config import get_settings, Settings

# In-memory SQLite for tests (no /data directory needed)
TEST_DATABASE_URL = "sqlite+aiosqlite://"


@pytest.fixture
def test_settings():
    """Settings with test values — Kroger credentials populated so guard middleware passes."""
    return Settings(
        kroger_client_id="test_client_id",
        kroger_client_secret="test_client_secret",
        llm_api_key="test_llm_key",
        database_url=TEST_DATABASE_URL,
        session_secret_key="test-secret",
        base_url="http://testserver",
    )


@pytest.fixture
async def test_db():
    """Async in-memory SQLite engine + session for tests."""
    engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def client(test_settings, test_db):
    """FastAPI test client with overridden dependencies."""
    async def override_get_session():
        yield test_db

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_settings] = lambda: test_settings

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()
