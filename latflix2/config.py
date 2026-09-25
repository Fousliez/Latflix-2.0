from __future__ import annotations

import os
from pathlib import Path


APP_NAME = "Latflix 2.0"
DATA_ENV = "LATFLIX2_DATA_DIR"
DATABASE_ENV = "LATFLIX2_DATABASE"


def data_root() -> Path:
    explicit = os.environ.get(DATA_ENV, "").strip()
    if explicit:
        return Path(explicit).expanduser().resolve()
    return Path.home() / ".local" / "share" / "latflix2"


def database_path() -> Path:
    explicit = os.environ.get(DATABASE_ENV, "").strip()
    if explicit:
        return Path(explicit).expanduser().resolve()
    return data_root() / "database" / "latflix2.db"
