from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Column:
    id: int
    name: str
    visible: bool = True


@dataclass(frozen=True)
class Row:
    id: int
    values: tuple[str, ...]


@dataclass(frozen=True)
class Dataset:
    category: str
    columns: tuple[Column, ...]
    rows: tuple[Row, ...]


class Repository:
    """Small read/write boundary around the existing Latflix EAV schema.

    The UI never reaches into sqlite directly. That is deliberate.
    """

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=15.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = NORMAL")
        return connection

    def _ensure_schema(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    sort_order INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS columns_meta (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    is_visible INTEGER NOT NULL DEFAULT 1,
                    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
                    UNIQUE (category_id, name)
                );
                CREATE TABLE IF NOT EXISTS records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER NOT NULL,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    deleted_at TEXT,
                    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS cell_values (
                    record_id INTEGER NOT NULL,
                    column_id INTEGER NOT NULL,
                    value TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY (record_id, column_id),
                    FOREIGN KEY (record_id) REFERENCES records(id) ON DELETE CASCADE,
                    FOREIGN KEY (column_id) REFERENCES columns_meta(id) ON DELETE CASCADE
                );
                """
            )
            count = connection.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
            if count == 0:
                self._seed_minimal(connection)

    @staticmethod
    def _seed_minimal(connection: sqlite3.Connection) -> None:
        seeds = {
            "Girls": ("Jméno", "Typ", "Národnost", "Věk", "Stav", "Hodnocení", "Tagy", "Posl. kontrola"),
            "Oblíbené": ("Jméno", "Typ", "Národnost", "Věk", "Stav", "Hodnocení", "Tagy", "Posl. kontrola"),
            "Videa": ("Název", "Typ", "Studio", "Dívka 1", "Dívka 2", "Dívka 3", "Stav", "Kvalita", "Dost. kv.", "Velikost", "Tagy"),
            "Odkazy": ("Typ", "Název", "Herečka", "URL", "Kontrola", "Staženo", "Poslední text"),
            "Studia": ("Název", "Typ", "Země", "Web", "Hodnocení", "Poznámka"),
            "Stavy": ("Název", "Barva"),
            "Tagy": ("Název", "Barva"),
            "Typy": ("Název", "Barva"),
            "Kvality": ("Název", "Barva"),
        }
        for category_order, (name, columns) in enumerate(seeds.items()):
            cursor = connection.execute(
                "INSERT INTO categories(name, sort_order) VALUES (?, ?)",
                (name, category_order),
            )
            category_id = int(cursor.lastrowid)
            connection.executemany(
                "INSERT INTO columns_meta(category_id, name, sort_order) VALUES (?, ?, ?)",
                [(category_id, column, index) for index, column in enumerate(columns)],
            )

    def categories(self) -> list[str]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT name FROM categories ORDER BY sort_order, id"
            ).fetchall()
        return [str(row["name"]) for row in rows]

    def resolve_category(self, requested: str) -> str:
        requested = str(requested or "").strip()
        available = set(self.categories())
        if requested in available:
            return requested
        aliases = {
            "Videa": "Scény / filmy",
            "Scény / filmy": "Videa",
        }
        alias = aliases.get(requested)
        if alias in available:
            return alias
        return requested

    def load(self, requested_category: str) -> Dataset:
        category = self.resolve_category(requested_category)
        with self.connect() as connection:
            category_row = connection.execute(
                "SELECT id FROM categories WHERE name = ? LIMIT 1",
                (category,),
            ).fetchone()
            if category_row is None:
                return Dataset(requested_category, (), ())
            category_id = int(category_row["id"])

            column_rows = connection.execute(
                """
                SELECT id, name, is_visible
                FROM columns_meta
                WHERE category_id = ?
                ORDER BY sort_order, id
                """,
                (category_id,),
            ).fetchall()
            columns = tuple(
                Column(int(row["id"]), str(row["name"]), bool(row["is_visible"]))
                for row in column_rows
            )

            record_rows = connection.execute(
                """
                SELECT id
                FROM records
                WHERE category_id = ? AND deleted_at IS NULL
                ORDER BY sort_order, id
                """,
                (category_id,),
            ).fetchall()
            record_ids = [int(row["id"]) for row in record_rows]
            if not record_ids:
                return Dataset(requested_category, columns, ())

            values_by_record = {record_id: {} for record_id in record_ids}
            placeholders = ",".join("?" for _ in record_ids)
            value_rows = connection.execute(
                f"""
                SELECT record_id, column_id, value
                FROM cell_values
                WHERE record_id IN ({placeholders})
                """,
                record_ids,
            ).fetchall()
            for row in value_rows:
                values_by_record[int(row["record_id"])][int(row["column_id"])] = str(row["value"] or "")

            rows = tuple(
                Row(
                    record_id,
                    tuple(values_by_record[record_id].get(column.id, "") for column in columns),
                )
                for record_id in record_ids
            )
            return Dataset(requested_category, columns, rows)

    def update_cell(self, record_id: int, column_id: int, value: str) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO cell_values(record_id, column_id, value)
                VALUES (?, ?, ?)
                ON CONFLICT(record_id, column_id)
                DO UPDATE SET value = excluded.value
                """,
                (int(record_id), int(column_id), str(value or "")),
            )
            connection.execute(
                "UPDATE records SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (int(record_id),),
            )

    def add_record(self, category_name: str) -> int:
        category = self.resolve_category(category_name)
        with self.connect() as connection:
            category_row = connection.execute(
                "SELECT id FROM categories WHERE name = ? LIMIT 1", (category,)
            ).fetchone()
            if category_row is None:
                raise ValueError(f"Neznámá sekce: {category_name}")
            category_id = int(category_row["id"])
            order = int(
                connection.execute(
                    "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM records WHERE category_id = ?",
                    (category_id,),
                ).fetchone()[0]
            )
            cursor = connection.execute(
                "INSERT INTO records(category_id, sort_order) VALUES (?, ?)",
                (category_id, order),
            )
            return int(cursor.lastrowid)

    def soft_delete(self, record_ids: Iterable[int]) -> None:
        ids = tuple(dict.fromkeys(int(value) for value in record_ids))
        if not ids:
            return
        placeholders = ",".join("?" for _ in ids)
        with self.connect() as connection:
            connection.execute(
                f"""
                UPDATE records
                SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id IN ({placeholders})
                """,
                ids,
            )
