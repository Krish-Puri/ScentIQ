"""Tests for Database Migrations (EPIC-02).
Verifies Alembic upgrade and downgrade run cleanly on an isolated test database.
"""
import os
import tempfile
from pathlib import Path
from alembic.config import Config
from alembic import command
import pytest

from app.core.config import ROOT_DIR


def test_alembic_migrations():
    # Use an isolated temporary SQLite database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_db_path = tmp.name

    try:
        api_dir = ROOT_DIR / "apps" / "api"
        current_cwd = os.getcwd()
        try:
            os.chdir(str(api_dir))
            config = Config("alembic.ini")
            # Override sqlalchemy.url in config to use temporary database
            temp_db_url = f"sqlite:///{Path(tmp_db_path).as_posix()}"
            config.set_main_option("sqlalchemy.url", temp_db_url)

            # 1. Upgrade to head
            command.upgrade(config, "head")

            # 2. Downgrade to base
            command.downgrade(config, "base")

            # 3. Re-upgrade to head
            command.upgrade(config, "head")
        finally:
            os.chdir(current_cwd)
    finally:
        if os.path.exists(tmp_db_path):
            try:
                os.remove(tmp_db_path)
            except Exception:
                pass
