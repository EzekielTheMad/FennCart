"""Test configuration and shared fixtures for FennCart tests."""
import pytest
import pytest_asyncio
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from sqlmodel import SQLModel

from app.main import app
from app.database import get_session
from app.config import get_settings, Settings


# In-memory SQLite for tests
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
def test_settings():
    """Settings with test values — Kroger credentials populated so guard middleware passes."""
    return Settings(
        kroger_client_id="test_client_id",
        kroger_client_secret="test_client_secret",
        llm_api_key="test_llm_key",
        database_url=TEST_DB_URL,
        session_secret_key="test-secret",
        base_url="http://testserver",
    )


@pytest_asyncio.fixture(scope="function")
async def test_db():
    """Create a fresh in-memory database for each test."""
    async with test_engine.begin() as conn:
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        await conn.run_sync(SQLModel.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(test_settings, test_db):
    """Async HTTP client with the test database injected.

    Both the FastAPI dependency injection and the middleware's direct
    session factory are patched to use the test in-memory database.
    """

    async def override_get_session():
        yield test_db

    # Override get_session for FastAPI dependency injection (routers)
    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_settings] = lambda: test_settings

    # Also patch the async_session factory used directly by SetupGuardMiddleware
    # so it uses the same test database rather than /data/fenncart.db
    import app.database as db_module

    with patch.object(db_module, "async_session", TestSessionLocal):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
            yield ac

    app.dependency_overrides.clear()
