from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class GirlRecord:
    id: int
    name: str = ""
    face: str = ""
    sex: str = ""
    type_name: str = ""
    nudity: str = ""
    age_source: str = ""
    nationality: str = ""
    tags: tuple[str, ...] = ()
    tracking: int = 0
    last_check: str = ""
    occurrences: int = 0
    note: str = ""
    status: str = ""
    locked: bool = False
    favorite: bool = False
    profile_path: str = ""
    aliases: tuple[str, ...] = ()
    sort_order: int = 0
    is_new: bool = False


@dataclass(frozen=True)
class CatalogEntry:
    id: int
    kind: str
    name: str
    color: str
    sort_order: int


@dataclass(frozen=True)
class LinkRecord:
    id: int
    girl_id: int
    girl_name: str
    source: str
    url: str
    sort_order: int


class Repository:
    """Single persistence boundary for the clean Latflix 2.0 rewrite."""

    GIRL_FIELDS = {
        "name", "face", "sex", "type_name", "nudity", "age_source",
        "nationality", "last_check", "note", "status", "profile_path",
    }

    def __init__(self, path: Path):
        self.path = Path(path).expanduser().resolve()
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
                CREATE TABLE IF NOT EXISTS lf2_girls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL DEFAULT '',
                    face TEXT NOT NULL DEFAULT '',
                    sex TEXT NOT NULL DEFAULT '',
                    type_name TEXT NOT NULL DEFAULT '',
                    nudity TEXT NOT NULL DEFAULT '',
                    age_source TEXT NOT NULL DEFAULT '',
                    nationality TEXT NOT NULL DEFAULT '',
                    last_check TEXT NOT NULL DEFAULT '',
                    note TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT '',
                    locked INTEGER NOT NULL DEFAULT 0,
                    favorite INTEGER NOT NULL DEFAULT 0,
                    profile_path TEXT NOT NULL DEFAULT '',
                    aliases_json TEXT NOT NULL DEFAULT '[]',
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    is_new INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS lf2_catalog (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL,
                    name TEXT NOT NULL,
                    color TEXT NOT NULL DEFAULT '#d7e9ff',
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    UNIQUE(kind, name)
                );

                CREATE TABLE IF NOT EXISTS lf2_girl_tags (
                    girl_id INTEGER NOT NULL,
                    tag_id INTEGER NOT NULL,
                    PRIMARY KEY(girl_id, tag_id),
                    FOREIGN KEY(girl_id) REFERENCES lf2_girls(id) ON DELETE CASCADE,
                    FOREIGN KEY(tag_id) REFERENCES lf2_catalog(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS lf2_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    girl_id INTEGER NOT NULL,
                    source TEXT NOT NULL DEFAULT '',
                    url TEXT NOT NULL DEFAULT '',
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY(girl_id) REFERENCES lf2_girls(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS lf2_occurrences (
                    girl_id INTEGER PRIMARY KEY,
                    count INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY(girl_id) REFERENCES lf2_girls(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_lf2_girls_sort ON lf2_girls(sort_order DESC, id DESC);
                CREATE INDEX IF NOT EXISTS idx_lf2_girls_favorite ON lf2_girls(favorite, sort_order DESC);
                CREATE INDEX IF NOT EXISTS idx_lf2_girls_name ON lf2_girls(name COLLATE NOCASE);
                CREATE INDEX IF NOT EXISTS idx_lf2_links_girl ON lf2_links(girl_id, sort_order, id);
                CREATE INDEX IF NOT EXISTS idx_lf2_catalog_kind ON lf2_catalog(kind, sort_order, id);
                """
            )
            self._seed_catalogs(connection)

    @staticmethod
    def _seed_catalogs(connection: sqlite3.Connection) -> None:
        seeds = {
            "types": ("Herečka", "Modelka", "Amatérka"),
            "nationalities": (
                "Česká", "Americká", "Britská", "Německá", "Francouzská",
                "Italská", "Španělská", "Kanadská", "Australská", "Japonská", "Slovenská",
            ),
            "tags": ("Latex", "Ruined", "Softdomme"),
            "link_sources": (
                "Instagram", "Facebook", "Redgifs", "Pornhub", "Linktree",
                "X", "TikTok", "Reddit", "YouTube",
            ),
        }
        for kind, names in seeds.items():
            existing = connection.execute(
                "SELECT COUNT(*) FROM lf2_catalog WHERE kind = ?", (kind,)
            ).fetchone()[0]
            if existing:
                continue
            connection.executemany(
                "INSERT INTO lf2_catalog(kind, name, sort_order) VALUES (?, ?, ?)",
                [(kind, name, index) for index, name in enumerate(names)],
            )

    @staticmethod
    def _json_list(raw: str) -> tuple[str, ...]:
        try:
            value = json.loads(raw or "[]")
        except (TypeError, json.JSONDecodeError):
            return ()
        if not isinstance(value, list):
            return ()
        return tuple(str(item).strip() for item in value if str(item).strip())

    def _tag_map(self, connection: sqlite3.Connection, ids: list[int]) -> dict[int, tuple[str, ...]]:
        if not ids:
            return {}
        placeholders = ",".join("?" for _ in ids)
        rows = connection.execute(
            f"""
            SELECT gt.girl_id, c.name
            FROM lf2_girl_tags gt
            JOIN lf2_catalog c ON c.id = gt.tag_id
            WHERE gt.girl_id IN ({placeholders})
            ORDER BY c.sort_order, c.id
            """,
            ids,
        ).fetchall()
        result: dict[int, list[str]] = {girl_id: [] for girl_id in ids}
        for row in rows:
            result[int(row["girl_id"])].append(str(row["name"]))
        return {key: tuple(value) for key, value in result.items()}

    def list_girls(self, favorites: bool = False) -> tuple[GirlRecord, ...]:
        with self.connect() as connection:
            where = "WHERE g.favorite = 1" if favorites else ""
            rows = connection.execute(
                f"""
                SELECT g.*,
                       COALESCE(o.count, 0) AS occurrences,
                       (SELECT COUNT(*) FROM lf2_links l WHERE l.girl_id = g.id) AS tracking
                FROM lf2_girls g
                LEFT JOIN lf2_occurrences o ON o.girl_id = g.id
                {where}
                ORDER BY g.sort_order DESC, g.id DESC
                """
            ).fetchall()
            ids = [int(row["id"]) for row in rows]
            tags = self._tag_map(connection, ids)

        return tuple(
            GirlRecord(
                id=int(row["id"]),
                name=str(row["name"] or ""),
                face=str(row["face"] or ""),
                sex=str(row["sex"] or ""),
                type_name=str(row["type_name"] or ""),
                nudity=str(row["nudity"] or ""),
                age_source=str(row["age_source"] or ""),
                nationality=str(row["nationality"] or ""),
                tags=tags.get(int(row["id"]), ()),
                tracking=int(row["tracking"] or 0),
                last_check=str(row["last_check"] or ""),
                occurrences=int(row["occurrences"] or 0),
                note=str(row["note"] or ""),
                status=str(row["status"] or ""),
                locked=bool(row["locked"]),
                favorite=bool(row["favorite"]),
                profile_path=str(row["profile_path"] or ""),
                aliases=self._json_list(str(row["aliases_json"] or "[]")),
                sort_order=int(row["sort_order"] or 0),
                is_new=bool(row["is_new"]),
            )
            for row in rows
        )

    def girl(self, girl_id: int) -> GirlRecord | None:
        records = self.list_girls(False)
        return next((record for record in records if record.id == int(girl_id)), None)

    def add_girls(self, count: int = 1) -> list[int]:
        count = max(1, int(count))
        with self.connect() as connection:
            maximum = int(
                connection.execute("SELECT COALESCE(MAX(sort_order), 0) FROM lf2_girls").fetchone()[0]
            )
            result: list[int] = []
            for offset in range(count):
                cursor = connection.execute(
                    "INSERT INTO lf2_girls(sort_order, is_new) VALUES (?, 1)",
                    (maximum + count - offset,),
                )
                result.append(int(cursor.lastrowid))
        return result

    def update_field(self, girl_id: int, key: str, value: str) -> None:
        if key not in self.GIRL_FIELDS:
            raise KeyError(f"Unsupported girl field: {key}")
        text = str(value or "")
        touched = 1 if text.strip() else 0
        with self.connect() as connection:
            connection.execute(
                f"""
                UPDATE lf2_girls
                SET {key} = ?,
                    is_new = CASE WHEN ? = 1 THEN 0 ELSE is_new END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (text, touched, int(girl_id)),
            )

    def set_aliases(self, girl_id: int, aliases: Iterable[str]) -> None:
        cleaned = [str(value).strip() for value in aliases if str(value).strip()]
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE lf2_girls
                SET aliases_json = ?, is_new = CASE WHEN ? THEN 0 ELSE is_new END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (json.dumps(cleaned, ensure_ascii=False), bool(cleaned), int(girl_id)),
            )

    def set_locked(self, girl_id: int, locked: bool) -> None:
        with self.connect() as connection:
            connection.execute(
                "UPDATE lf2_girls SET locked = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (1 if locked else 0, int(girl_id)),
            )

    def set_favorite(self, girl_id: int, favorite: bool) -> None:
        with self.connect() as connection:
            connection.execute(
                "UPDATE lf2_girls SET favorite = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (1 if favorite else 0, int(girl_id)),
            )

    def set_tags(self, girl_id: int, names: Iterable[str]) -> None:
        wanted = [str(name).strip() for name in names if str(name).strip()]
        with self.connect() as connection:
            connection.execute("DELETE FROM lf2_girl_tags WHERE girl_id = ?", (int(girl_id),))
            for name in wanted:
                row = connection.execute(
                    "SELECT id FROM lf2_catalog WHERE kind = 'tags' AND name = ? LIMIT 1",
                    (name,),
                ).fetchone()
                if row is None:
                    continue
                connection.execute(
                    "INSERT OR IGNORE INTO lf2_girl_tags(girl_id, tag_id) VALUES (?, ?)",
                    (int(girl_id), int(row["id"])),
                )
            if wanted:
                connection.execute(
                    "UPDATE lf2_girls SET is_new = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (int(girl_id),),
                )

    def delete_unlocked(self, girl_ids: Iterable[int]) -> int:
        ids = list(dict.fromkeys(int(value) for value in girl_ids))
        if not ids:
            return 0
        placeholders = ",".join("?" for _ in ids)
        with self.connect() as connection:
            cursor = connection.execute(
                f"DELETE FROM lf2_girls WHERE id IN ({placeholders}) AND locked = 0",
                ids,
            )
            return int(cursor.rowcount)

    def cleanup_blank_new_rows(self) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                DELETE FROM lf2_girls
                WHERE is_new = 1
                  AND TRIM(name) = ''
                  AND TRIM(face) = ''
                  AND TRIM(sex) = ''
                  AND TRIM(type_name) = ''
                  AND TRIM(nudity) = ''
                  AND TRIM(age_source) = ''
                  AND TRIM(nationality) = ''
                  AND TRIM(last_check) = ''
                  AND TRIM(note) = ''
                  AND TRIM(status) = ''
                  AND TRIM(profile_path) = ''
                  AND favorite = 0
                  AND NOT EXISTS (SELECT 1 FROM lf2_girl_tags gt WHERE gt.girl_id = lf2_girls.id)
                  AND NOT EXISTS (SELECT 1 FROM lf2_links l WHERE l.girl_id = lf2_girls.id)
                  AND COALESCE((SELECT count FROM lf2_occurrences o WHERE o.girl_id = lf2_girls.id), 0) = 0
                """
            )
            return int(cursor.rowcount)

    def catalog(self, kind: str) -> tuple[CatalogEntry, ...]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM lf2_catalog WHERE kind = ? ORDER BY sort_order, id",
                (str(kind),),
            ).fetchall()
        return tuple(
            CatalogEntry(
                int(row["id"]), str(row["kind"]), str(row["name"]),
                str(row["color"]), int(row["sort_order"]),
            )
            for row in rows
        )

    def catalog_names(self, kind: str) -> tuple[str, ...]:
        return tuple(entry.name for entry in self.catalog(kind))

    def add_catalog_entry(self, kind: str, name: str = "", color: str = "#d7e9ff") -> int:
        with self.connect() as connection:
            order = int(
                connection.execute(
                    "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM lf2_catalog WHERE kind = ?",
                    (str(kind),),
                ).fetchone()[0]
            )
            base = str(name).strip() or f"Nová položka {order + 1}"
            candidate = base
            suffix = 2
            while connection.execute(
                "SELECT 1 FROM lf2_catalog WHERE kind = ? AND name = ?",
                (str(kind), candidate),
            ).fetchone():
                candidate = f"{base} {suffix}"
                suffix += 1
            cursor = connection.execute(
                "INSERT INTO lf2_catalog(kind, name, color, sort_order) VALUES (?, ?, ?, ?)",
                (str(kind), candidate, str(color), order),
            )
            return int(cursor.lastrowid)

    def update_catalog_entry(self, entry_id: int, *, name: str | None = None, color: str | None = None) -> None:
        parts: list[str] = []
        values: list[object] = []
        if name is not None:
            parts.append("name = ?")
            values.append(str(name).strip())
        if color is not None:
            parts.append("color = ?")
            values.append(str(color).strip() or "#d7e9ff")
        if not parts:
            return
        values.append(int(entry_id))
        with self.connect() as connection:
            connection.execute(
                f"UPDATE lf2_catalog SET {', '.join(parts)} WHERE id = ?",
                values,
            )

    def delete_catalog_entries(self, ids: Iterable[int]) -> None:
        values = list(dict.fromkeys(int(value) for value in ids))
        if not values:
            return
        placeholders = ",".join("?" for _ in values)
        with self.connect() as connection:
            connection.execute(f"DELETE FROM lf2_catalog WHERE id IN ({placeholders})", values)

    def links(self, girl_id: int) -> tuple[LinkRecord, ...]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT l.*, g.name AS girl_name
                FROM lf2_links l
                JOIN lf2_girls g ON g.id = l.girl_id
                WHERE l.girl_id = ?
                ORDER BY l.sort_order, l.id
                """,
                (int(girl_id),),
            ).fetchall()
        return tuple(
            LinkRecord(
                int(row["id"]), int(row["girl_id"]), str(row["girl_name"] or ""),
                str(row["source"] or ""), str(row["url"] or ""), int(row["sort_order"]),
            )
            for row in rows
        )

    def all_links(self, girl_id: int | None = None) -> tuple[LinkRecord, ...]:
        params: tuple[object, ...] = ()
        where = ""
        if girl_id is not None:
            where = "WHERE l.girl_id = ?"
            params = (int(girl_id),)
        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT l.*, g.name AS girl_name
                FROM lf2_links l
                JOIN lf2_girls g ON g.id = l.girl_id
                {where}
                ORDER BY l.id DESC
                """,
                params,
            ).fetchall()
        return tuple(
            LinkRecord(
                int(row["id"]), int(row["girl_id"]), str(row["girl_name"] or ""),
                str(row["source"] or ""), str(row["url"] or ""), int(row["sort_order"]),
            )
            for row in rows
        )

    def add_link(self, girl_id: int, source: str, url: str) -> int | None:
        url = str(url or "").strip()
        if not url:
            return None
        source = str(source or "").strip()
        with self.connect() as connection:
            order = int(
                connection.execute(
                    "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM lf2_links WHERE girl_id = ?",
                    (int(girl_id),),
                ).fetchone()[0]
            )
            cursor = connection.execute(
                "INSERT INTO lf2_links(girl_id, source, url, sort_order) VALUES (?, ?, ?, ?)",
                (int(girl_id), source, url, order),
            )
            connection.execute(
                "UPDATE lf2_girls SET is_new = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (int(girl_id),),
            )
            if source:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO lf2_catalog(kind, name, sort_order)
                    VALUES ('link_sources', ?, 9999)
                    """,
                    (source,),
                )
            return int(cursor.lastrowid)

    def update_link(self, link_id: int, source: str, url: str) -> None:
        with self.connect() as connection:
            connection.execute(
                "UPDATE lf2_links SET source = ?, url = ? WHERE id = ?",
                (str(source or "").strip(), str(url or "").strip(), int(link_id)),
            )

    def delete_link(self, link_id: int) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM lf2_links WHERE id = ?", (int(link_id),))

    def source_rank(self) -> dict[str, int]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT LOWER(TRIM(source)) AS normalized, COUNT(DISTINCT girl_id) AS used
                FROM lf2_links
                WHERE TRIM(source) <> ''
                GROUP BY LOWER(TRIM(source))
                ORDER BY used DESC, normalized
                """
            ).fetchall()
        return {str(row["normalized"]): index for index, row in enumerate(rows)}

    def nationality_rank(self) -> tuple[str, ...]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT nationality, COUNT(*) AS used
                FROM lf2_girls
                WHERE TRIM(nationality) <> ''
                GROUP BY nationality
                ORDER BY used DESC, LOWER(nationality)
                """
            ).fetchall()
        return tuple(str(row["nationality"]) for row in rows)

    def name_suggestions(self, query: str = "", favorites: bool = False) -> list[str]:
        query = str(query or "").strip().casefold()
        rows = self.list_girls(favorites)
        ranked: list[tuple[int, int, str]] = []
        for row in rows:
            if not row.name.strip():
                continue
            names = (row.name, *row.aliases)
            folded = [value.casefold() for value in names]
            if not query:
                quality = 0
            elif any(value.startswith(query) for value in folded):
                quality = 0
            elif any(query in value for value in folded):
                quality = 1
            else:
                continue
            ranked.append((quality, -int(row.occurrences), row.name))
        ranked.sort(key=lambda item: (item[0], item[1], item[2].casefold()))
        result: list[str] = []
        seen: set[str] = set()
        for _quality, _occ, name in ranked:
            folded = name.casefold()
            if folded not in seen:
                seen.add(folded)
                result.append(name)
        return result

    def overview_counts(self) -> dict[str, int]:
        with self.connect() as connection:
            girls = int(connection.execute("SELECT COUNT(*) FROM lf2_girls").fetchone()[0])
            favorites = int(connection.execute("SELECT COUNT(*) FROM lf2_girls WHERE favorite = 1").fetchone()[0])
            links = int(connection.execute("SELECT COUNT(*) FROM lf2_links").fetchone()[0])
        return {"Girls": girls, "Oblíbené": favorites, "Odkazy": links}
