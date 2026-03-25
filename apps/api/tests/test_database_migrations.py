from __future__ import annotations

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


def test_alembic_upgrade_head_bootstraps_schema(tmp_path: Path) -> None:
    database_path = tmp_path / "migration-test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"

    repo_root = Path(__file__).resolve().parents[3]
    alembic_config = Config(str(repo_root / "alembic.ini"))

    command.upgrade(alembic_config, "head")

    engine = create_engine(os.environ["DATABASE_URL"], future=True)
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    assert "alembic_version" in table_names
    assert {
        "projects",
        "task_runs",
        "project_files",
        "source_bundles",
        "presentation_briefs",
        "outlines",
        "slide_plans",
        "slide_artifacts",
        "templates",
        "exports",
    }.issubset(table_names)

    with engine.connect() as connection:
        current_revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()

    assert current_revision == "20260325_0001"


@pytest.mark.skipif(
    not os.environ.get("TEST_POSTGRES_MIGRATION_URL"),
    reason="TEST_POSTGRES_MIGRATION_URL is required for PostgreSQL migration smoke",
)
def test_alembic_upgrade_head_bootstraps_postgresql_schema() -> None:
    database_url = os.environ["TEST_POSTGRES_MIGRATION_URL"]
    os.environ["DATABASE_URL"] = database_url

    repo_root = Path(__file__).resolve().parents[3]
    alembic_config = Config(str(repo_root / "alembic.ini"))

    engine = create_engine(database_url.replace("postgresql://", "postgresql+psycopg://", 1), future=True)
    with engine.begin() as connection:
        inspector = inspect(connection)
        existing_tables = inspector.get_table_names()
        if existing_tables:
            pytest.skip("TEST_POSTGRES_MIGRATION_URL must point to an empty PostgreSQL database")

    command.upgrade(alembic_config, "head")

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    assert "alembic_version" in table_names
    assert {
        "projects",
        "task_runs",
        "project_files",
        "source_bundles",
        "presentation_briefs",
        "outlines",
        "slide_plans",
        "slide_artifacts",
        "templates",
        "exports",
    }.issubset(table_names)
