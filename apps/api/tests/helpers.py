from __future__ import annotations

import os
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config


REPO_ROOT = Path(__file__).resolve().parents[3]


def bootstrap_sqlite_database(database_path: Path, *, use_migrations: bool = True) -> None:
    os.environ["DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"
    os.environ["AUTO_CREATE_TABLES"] = "true"

    for module_name in ("app.main", "app.db.session"):
        sys.modules.pop(module_name, None)

    if not use_migrations:
        return

    alembic_config = Config(str(REPO_ROOT / "alembic.ini"))
    command.upgrade(alembic_config, "head")