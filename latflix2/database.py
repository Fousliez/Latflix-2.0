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
    favorite_ids: frozenset[int] = frozenset()


class Repository:
    """Jediná SQLite hranice Latflixu 2.0."""

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
                CREATE TABLE IF NOT EXISTS favorite_girls (
                    record_id INTEGER PRIMARY KEY,
                    FOREIGN KEY (record_id) REFERENCES records(id) ON DELETE CASCADE
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
        aliases = {"Videa": "Scény / filmy", "Scény / filmy": "Videa"}
        alias = aliases.get(requested)
        if alias in available:
            return alias
        return requested

    def favorite_ids(self) -> frozenset[int]:
        with self.connect() as connection:
            rows = connection.execute("SELECT record_id FROM favorite_girls").fetchall()
        return frozenset(int(row["record_id"]) for row in rows)

    def is_favorite(self, record_id: int | None) -> bool:
        if record_id is None:
            return False
        with self.connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM favorite_girls WHERE record_id = ? LIMIT 1",
                (int(record_id),),
            ).fetchone()
        return row is not None

    def set_favorite(self, record_id: int, favorite: bool) -> None:
        with self.connect() as connection:
            if favorite:
                connection.execute(
                    "INSERT OR IGNORE INTO favorite_girls(record_id) VALUES (?)",
                    (int(record_id),),
                )
            else:
                connection.execute(
                    "DELETE FROM favorite_girls WHERE record_id = ?",
                    (int(record_id),),
                )

    def _load_base(self, requested_category: str) -> Dataset:
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
            favorites = self.favorite_ids() if requested_category in {"Girls", "Oblíbené"} else frozenset()
            if not record_ids:
                return Dataset(requested_category, columns, (), favorites)

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
        return Dataset(requested_category, columns, rows, favorites)

    def load(self, requested_category: str) -> Dataset:
        if requested_category == "Oblíbené":
            girls = self._load_base("Girls")
            rows = tuple(row for row in girls.rows if row.id in girls.favorite_ids)
            return Dataset("Oblíbené", girls.columns, rows, girls.favorite_ids)
        return self._load_base(requested_category)

    def overview_counts(self) -> dict[str, int]:
        result: dict[str, int] = {}
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT categories.name, COUNT(records.id) AS total
                FROM categories
                LEFT JOIN records
                  ON records.category_id = categories.id
                 AND records.deleted_at IS NULL
                GROUP BY categories.id
                ORDER BY categories.sort_order, categories.id
                """
            ).fetchall()
            result.update({str(row["name"]): int(row["total"]) for row in rows})
            result["Oblíbené"] = int(
                connection.execute("SELECT COUNT(*) FROM favorite_girls").fetchone()[0]
            )
        if "Scény / filmy" in result and "Videa" not in result:
            result["Videa"] = result["Scény / filmy"]
        return result

    @staticmethod
    def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
        row = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ? LIMIT 1",
            (str(table_name),),
        ).fetchone()
        return row is not None

    def person_links(self, record_id: int | None) -> list[dict[str, str]]:
        """Vrátí odkazy osoby ze starého schématu, pokud jsou v DB dostupné."""
        if record_id is None:
            return []

        definitions = (
            ("social_links", "Sociální"),
            ("source_links", "Zdroj"),
            ("directory_links", "Adresář"),
        )
        result: list[dict[str, str]] = []
        with self.connect() as connection:
            for table_name, type_label in definitions:
                if not self._table_exists(connection, table_name):
                    continue
                rows = connection.execute(
                    f"""
                    SELECT site, url
                    FROM {table_name}
                    WHERE record_id = ?
                    ORDER BY sort_order, id
                    """,
                    (int(record_id),),
                ).fetchall()
                result.extend(
                    {
                        "type": table_name,
                        "type_label": type_label,
                        "site": str(row["site"] or "").strip(),
                        "url": str(row["url"] or "").strip(),
                    }
                    for row in rows
                    if str(row["site"] or "").strip() or str(row["url"] or "").strip()
                )
        return result

    def missing_source_names(self, record_id: int | None) -> list[str]:
        """Zdrojové weby používané v databázi, které vybraná osoba nemá."""
        if record_id is None:
            return []
        with self.connect() as connection:
            if not self._table_exists(connection, "source_links"):
                return []

            assigned = {
                str(row["site"] or "").strip().casefold()
                for row in connection.execute(
                    "SELECT site FROM source_links WHERE record_id = ?",
                    (int(record_id),),
                ).fetchall()
                if str(row["site"] or "").strip()
            }
            rows = connection.execute(
                """
                SELECT MIN(TRIM(site)) AS display_name,
                       LOWER(TRIM(site)) AS normalized_name,
                       COUNT(DISTINCT record_id) AS people_count
                FROM source_links
                WHERE TRIM(COALESCE(site, '')) <> ''
                GROUP BY LOWER(TRIM(site))
                ORDER BY people_count DESC, normalized_name ASC
                """
            ).fetchall()

        return [
            str(row["display_name"])
            for row in rows
            if str(row["normalized_name"] or "").casefold() not in assigned
        ]

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

    def update_named_cell(self, record_id: int, category_name: str, column_name: str, value: str) -> bool:
        category = self.resolve_category(category_name)
        if category_name == "Oblíbené":
            category = self.resolve_category("Girls")
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT columns_meta.id
                FROM columns_meta
                JOIN categories ON categories.id = columns_meta.category_id
                WHERE categories.name = ? AND columns_meta.name = ?
                LIMIT 1
                """,
                (category, column_name),
            ).fetchone()
        if row is None:
            return False
        self.update_cell(record_id, int(row["id"]), value)
        return True

    def add_record(self, category_name: str) -> int:
        favorite_after = category_name == "Oblíbené"
        category = "Girls" if favorite_after else self.resolve_category(category_name)
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
            record_id = int(cursor.lastrowid)
        if favorite_after:
            self.set_favorite(record_id, True)
        return record_id

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
