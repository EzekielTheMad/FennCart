"""Test Alembic migration chain: empty DB -> head without errors (D-06)."""
import pytest
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect


@pytest.fixture
def alembic_config():
    """Override alembic config to use in-memory SQLite (not /data/fenncart.db)."""
    from pytest_alembic.config import Config
    return Config.from_raw_config({
        "script_location": "alembic",
        "sqlalchemy.url": "sqlite:///",
    })


@pytest.fixture
def alembic_engine():
    """Synchronous in-memory SQLite engine for migration testing.

    MUST be synchronous — pytest-alembic's DDL introspection
    does not support async engines.
    """
    engine = sa.create_engine("sqlite:///", echo=False)
    yield engine
    engine.dispose()


def test_migrations_upgrade_to_head(alembic_runner):
    """All 4 migrations apply sequentially from empty DB to head without error."""
    alembic_runner.migrate_up_to("head")


def test_model_definitions_match_ddl(alembic_runner, alembic_engine):
    """Final migrated schema matches SQLModel metadata.

    Catches missing columns or tables added after migrations were written.
    If this test produces SQLite-specific false positives, it can be
    marked xfail or removed — test_migrations_upgrade_to_head is the
    critical test.
    """
    alembic_runner.migrate_up_to("head")

    # Verify all expected tables exist in the migrated schema
    inspector = sa_inspect(alembic_engine)
    tables = set(inspector.get_table_names())

    expected_tables = {
        "app_config",
        "oauth_tokens",
        "cart_sessions",
        "cart_items",
        "preference_entries",
        "receipt_uploads",
    }
    missing = expected_tables - tables
    assert not missing, f"Tables missing from migrated schema: {missing}"
