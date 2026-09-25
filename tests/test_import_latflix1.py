import sqlite3
from pathlib import Path

import pytest

from tools.import_latflix1 import copy_database


def _source_database(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE sample(id INTEGER PRIMARY KEY, value TEXT)")
        connection.execute("INSERT INTO sample(value) VALUES ('original')")


def test_import_copies_without_modifying_source(tmp_path: Path):
    source = tmp_path / "source.db"
    target = tmp_path / "target.db"
    _source_database(source)

    copy_database(source, target)

    with sqlite3.connect(source) as connection:
        assert connection.execute("SELECT value FROM sample").fetchone()[0] == "original"
    with sqlite3.connect(target) as connection:
        assert connection.execute("SELECT value FROM sample").fetchone()[0] == "original"


def test_import_refuses_overwrite_without_force(tmp_path: Path):
    source = tmp_path / "source.db"
    target = tmp_path / "target.db"
    _source_database(source)
    _source_database(target)

    with pytest.raises(FileExistsError):
        copy_database(source, target)
