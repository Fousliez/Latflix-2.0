from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


@dataclass(frozen=True)
class Girl:
    id: int
    name: str = ""
    face: str = ""
    sex: str = ""
    type_name: str = ""
    nudity: str = ""
    age_source: str = ""
    nationality: str = ""
    last_check: str = ""
    note: str = ""
    status: str = ""
    locked: bool = False
    favorite: bool = False
    profile_path: str = ""
    aliases: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    tracking: int = 0
    occurrences: int = 0
    created_seq: int = 0


@dataclass(frozen=True)
class Studio:
    id: int
    name: str = ""
    type_name: str = ""
    url: str = ""
    locked: bool = False
    occurrences: int = 0
    created_seq: int = 0


@dataclass(frozen=True)
class Video:
    id: int
    title: str = ""
    studio_id: int | None = None
    studio_name: str = ""
    release_date: str = ""
    state: str = ""
    quality: str = ""
    available_quality: str = ""
    size: str = ""
    duration: str = ""
    mixed_gender: str = ""
    note: str = ""
    locked: bool = False
    in_super: bool = False
    participants: tuple[tuple[int, str, int], ...] = ()
    created_seq: int = 0


@dataclass(frozen=True)
class Link:
    id: int
    type_id: int | None
    type_name: str
    category: str
    girl_id: int | None
    girl_name: str
    url: str
    check_value: str = ""
    downloaded: str = ""
    active: str = "Akt."
    last_text: str = ""
    last_image: str = ""
    locked: bool = False
    created_seq: int = 0


class Repository:
    """Persistence boundary for Latflix 2.1.

    New lf21_* tables keep the 2.0 prototype intact. On first start the useful
    lf2 Girls/catalog/link data is copied when available.
    """

    def __init__(self, path: Path):
        self.path = Path(path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()
        self._migrate_from_lf2_once()

    def connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=20.0)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        db.execute("PRAGMA journal_mode = WAL")
        db.execute("PRAGMA synchronous = NORMAL")
        return db

    @staticmethod
    def _seq(c: sqlite3.Connection, table: str) -> int:
        return int(c.execute(f"SELECT COALESCE(MAX(created_seq),0)+1 FROM {table}").fetchone()[0])

    @staticmethod
    def _json_tuple(raw: str) -> tuple[str, ...]:
        try:
            value = json.loads(raw or "[]")
        except Exception:
            return ()
        return tuple(str(x).strip() for x in value if str(x).strip()) if isinstance(value, list) else ()

    def _ensure_schema(self) -> None:
        with self.connect() as c:
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS lf21_meta(
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS lf21_girls(
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
                    created_seq INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS lf21_catalog(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL,
                    name TEXT NOT NULL,
                    color TEXT NOT NULL DEFAULT '#d7e9ff',
                    created_seq INTEGER NOT NULL DEFAULT 0,
                    UNIQUE(kind, name COLLATE NOCASE)
                );

                CREATE TABLE IF NOT EXISTS lf21_girl_tags(
                    girl_id INTEGER NOT NULL REFERENCES lf21_girls(id) ON DELETE CASCADE,
                    tag_id INTEGER NOT NULL REFERENCES lf21_catalog(id) ON DELETE CASCADE,
                    PRIMARY KEY(girl_id, tag_id)
                );

                CREATE TABLE IF NOT EXISTS lf21_studios(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL DEFAULT '',
                    type_name TEXT NOT NULL DEFAULT '',
                    url TEXT NOT NULL DEFAULT '',
                    locked INTEGER NOT NULL DEFAULT 0,
                    created_seq INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS lf21_videos(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL DEFAULT '',
                    studio_id INTEGER REFERENCES lf21_studios(id) ON DELETE SET NULL,
                    release_date TEXT NOT NULL DEFAULT '',
                    state TEXT NOT NULL DEFAULT '',
                    quality TEXT NOT NULL DEFAULT '',
                    available_quality TEXT NOT NULL DEFAULT '',
                    size TEXT NOT NULL DEFAULT '',
                    duration TEXT NOT NULL DEFAULT '',
                    mixed_gender TEXT NOT NULL DEFAULT '',
                    note TEXT NOT NULL DEFAULT '',
                    locked INTEGER NOT NULL DEFAULT 0,
                    in_super INTEGER NOT NULL DEFAULT 0,
                    created_seq INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS lf21_video_girls(
                    video_id INTEGER NOT NULL REFERENCES lf21_videos(id) ON DELETE CASCADE,
                    girl_id INTEGER NOT NULL REFERENCES lf21_girls(id) ON DELETE CASCADE,
                    PRIMARY KEY(video_id, girl_id)
                );

                CREATE TABLE IF NOT EXISTS lf21_link_types(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL DEFAULT 'Zdroj',
                    name TEXT NOT NULL DEFAULT '',
                    general_web TEXT NOT NULL DEFAULT '',
                    visible_all INTEGER NOT NULL DEFAULT 1,
                    visible_category INTEGER NOT NULL DEFAULT 1,
                    created_seq INTEGER NOT NULL DEFAULT 0,
                    UNIQUE(name COLLATE NOCASE)
                );

                CREATE TABLE IF NOT EXISTS lf21_links(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type_id INTEGER REFERENCES lf21_link_types(id) ON DELETE SET NULL,
                    girl_id INTEGER REFERENCES lf21_girls(id) ON DELETE SET NULL,
                    url TEXT NOT NULL DEFAULT '',
                    check_value TEXT NOT NULL DEFAULT '',
                    downloaded TEXT NOT NULL DEFAULT '',
                    active TEXT NOT NULL DEFAULT 'Akt.',
                    last_text TEXT NOT NULL DEFAULT '',
                    last_image TEXT NOT NULL DEFAULT '',
                    locked INTEGER NOT NULL DEFAULT 0,
                    created_seq INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_lf21_girls_new ON lf21_girls(created_seq DESC, id DESC);
                CREATE INDEX IF NOT EXISTS idx_lf21_girls_fav ON lf21_girls(favorite, created_seq DESC);
                CREATE INDEX IF NOT EXISTS idx_lf21_video_studio ON lf21_videos(studio_id);
                CREATE INDEX IF NOT EXISTS idx_lf21_video_super ON lf21_videos(in_super, created_seq DESC);
                CREATE INDEX IF NOT EXISTS idx_lf21_video_girls_girl ON lf21_video_girls(girl_id, video_id);
                CREATE INDEX IF NOT EXISTS idx_lf21_links_type ON lf21_links(type_id);
                CREATE INDEX IF NOT EXISTS idx_lf21_links_girl ON lf21_links(girl_id);
                """
            )
            self._seed(c)

    @staticmethod
    def _seed(c: sqlite3.Connection) -> None:
        seeds = {
            "types": ("Herečka", "Modelka", "Amatérka"),
            "nationalities": (
                "Česká", "Americká", "Britská", "Německá", "Francouzská",
                "Italská", "Španělská", "Kanadská", "Australská", "Japonská",
                "Slovenská", "Ruská", "Ukrajinská",
            ),
            "tags": ("Latex", "Ruined", "Softdomme"),
            "states": ("NOVÉ", "CHCI", "MÁM", "NECHCI"),
            "qualities": ("4K", "2160p", "1440p", "1080p", "720p", "480p"),
        }
        for kind, values in seeds.items():
            if c.execute("SELECT 1 FROM lf21_catalog WHERE kind=? LIMIT 1", (kind,)).fetchone():
                continue
            for idx, value in enumerate(values, 1):
                c.execute(
                    "INSERT OR IGNORE INTO lf21_catalog(kind,name,created_seq) VALUES(?,?,?)",
                    (kind, value, idx),
                )

        defaults = (
            ("Síť", "Instagram", "https://instagram.com"),
            ("Síť", "X / Twitter", "https://x.com"),
            ("Zdroj", "OnlyFans", ""),
            ("Zdroj", "Babepedia", "https://babepedia.com"),
            ("Zdroj", "Fansly", "https://fansly.com"),
            ("Zdroj", "PornBB.org", "https://pornbb.org"),
            ("Síť", "Reddit", "https://reddit.com"),
            ("Zdroj", "PornHub", "https://pornhub.com"),
            ("Síť", "TikTok", "https://tiktok.com"),
            ("Zdroj", "RedGifs", "https://redgifs.com"),
            ("Rozcestník", "Linktree", "https://linktr.ee"),
            ("Síť", "Facebook", "https://facebook.com"),
            ("Síť", "Telegram", "https://telegram.org"),
            ("Síť", "YouTube", "https://youtube.com"),
            ("Rozcestník", "AllMyLinks", "https://allmylinks.com"),
        )
        for idx, (category, name, web) in enumerate(defaults, 1):
            c.execute(
                "INSERT OR IGNORE INTO lf21_link_types(category,name,general_web,created_seq) VALUES(?,?,?,?)",
                (category, name, web, idx),
            )

    def _migrate_from_lf2_once(self) -> None:
        with self.connect() as c:
            if c.execute("SELECT value FROM lf21_meta WHERE key='migrated_lf2'").fetchone():
                return
            names = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "lf2_girls" in names and not c.execute("SELECT 1 FROM lf21_girls LIMIT 1").fetchone():
                rows = c.execute("SELECT * FROM lf2_girls ORDER BY sort_order, id").fetchall()
                id_map: dict[int, int] = {}
                for seq, r in enumerate(rows, 1):
                    cur = c.execute(
                        """INSERT INTO lf21_girls(
                               name,face,sex,type_name,nudity,age_source,nationality,last_check,note,status,
                               locked,favorite,profile_path,aliases_json,created_seq
                           ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (
                            r["name"], r["face"], r["sex"], r["type_name"], r["nudity"],
                            r["age_source"], r["nationality"], r["last_check"], r["note"],
                            r["status"], r["locked"], r["favorite"], r["profile_path"],
                            r["aliases_json"], seq,
                        ),
                    )
                    id_map[int(r["id"])] = int(cur.lastrowid)

                if "lf2_catalog" in names:
                    for r in c.execute("SELECT kind,name,color,sort_order FROM lf2_catalog").fetchall():
                        c.execute(
                            "INSERT OR IGNORE INTO lf21_catalog(kind,name,color,created_seq) VALUES(?,?,?,?)",
                            (r["kind"], r["name"], r["color"], r["sort_order"]),
                        )

                if "lf2_girl_tags" in names and "lf2_catalog" in names:
                    tag_by_name = {
                        r["name"]: r["id"]
                        for r in c.execute("SELECT id,name FROM lf21_catalog WHERE kind='tags'")
                    }
                    for r in c.execute(
                        "SELECT gt.girl_id,c.name FROM lf2_girl_tags gt "
                        "JOIN lf2_catalog c ON c.id=gt.tag_id"
                    ).fetchall():
                        new_girl = id_map.get(int(r["girl_id"]))
                        new_tag = tag_by_name.get(str(r["name"]))
                        if new_girl and new_tag:
                            c.execute(
                                "INSERT OR IGNORE INTO lf21_girl_tags(girl_id,tag_id) VALUES(?,?)",
                                (new_girl, new_tag),
                            )

                if "lf2_links" in names:
                    for seq, r in enumerate(
                        c.execute("SELECT * FROM lf2_links ORDER BY sort_order,id").fetchall(), 1
                    ):
                        new_girl = id_map.get(int(r["girl_id"]))
                        source = str(r["source"] or "").strip()
                        if not new_girl:
                            continue
                        row = c.execute(
                            "SELECT id FROM lf21_link_types WHERE name=? COLLATE NOCASE",
                            (source,),
                        ).fetchone()
                        if row is None:
                            cur = c.execute(
                                "INSERT INTO lf21_link_types(category,name,created_seq) VALUES('Zdroj',?,?)",
                                (source, seq),
                            )
                            type_id = int(cur.lastrowid)
                        else:
                            type_id = int(row["id"])
                        c.execute(
                            "INSERT INTO lf21_links(type_id,girl_id,url,created_seq) VALUES(?,?,?,?)",
                            (type_id, new_girl, r["url"], seq),
                        )
            c.execute("INSERT OR REPLACE INTO lf21_meta(key,value) VALUES('migrated_lf2','1')")

    def catalog(self, kind: str) -> list[str]:
        with self.connect() as c:
            return [
                str(r[0])
                for r in c.execute(
                    "SELECT name FROM lf21_catalog WHERE kind=? ORDER BY created_seq,name COLLATE NOCASE",
                    (kind,),
                )
            ]

    def catalog_rows(self, kind: str) -> list[dict]:
        with self.connect() as c:
            return [
                dict(r)
                for r in c.execute(
                    "SELECT id,name,color,created_seq FROM lf21_catalog "
                    "WHERE kind=? ORDER BY created_seq DESC,id DESC",
                    (kind,),
                )
            ]

    def add_catalog(self, kind: str, name: str, color: str = "#d7e9ff") -> int:
        name = name.strip()
        with self.connect() as c:
            row = c.execute(
                "SELECT id FROM lf21_catalog WHERE kind=? AND name=? COLLATE NOCASE",
                (kind, name),
            ).fetchone()
            if row:
                return int(row[0])
            cur = c.execute(
                "INSERT INTO lf21_catalog(kind,name,color,created_seq) VALUES(?,?,?,?)",
                (kind, name, color, self._seq(c, "lf21_catalog")),
            )
            return int(cur.lastrowid)

    def update_catalog(self, row_id: int, name: str, color: str | None = None) -> None:
        with self.connect() as c:
            if color is None:
                c.execute("UPDATE lf21_catalog SET name=? WHERE id=?", (name, row_id))
            else:
                c.execute(
                    "UPDATE lf21_catalog SET name=?,color=? WHERE id=?",
                    (name, color, row_id),
                )

    def delete_catalog(self, row_id: int) -> None:
        with self.connect() as c:
            c.execute("DELETE FROM lf21_catalog WHERE id=?", (row_id,))

    def _valid_video_sql(self, alias: str = "v") -> str:
        a = alias
        field_count = (
            f"((TRIM({a}.title)<>'')+"
            f"(CASE WHEN {a}.studio_id IS NOT NULL THEN 1 ELSE 0 END)+"
            f"(TRIM({a}.release_date)<>'')+(TRIM({a}.state)<>'')+"
            f"(TRIM({a}.quality)<>'')+(TRIM({a}.available_quality)<>'')+"
            f"(TRIM({a}.size)<>'')+(TRIM({a}.duration)<>'')+"
            f"(TRIM({a}.mixed_gender)<>'')+(TRIM({a}.note)<>'')+"
            f"(CASE WHEN EXISTS(SELECT 1 FROM lf21_video_girls vg0 "
            f"WHERE vg0.video_id={a}.id) THEN 1 ELSE 0 END))"
        )
        key_count = (
            f"((TRIM({a}.title)<>'')+"
            f"(CASE WHEN {a}.studio_id IS NOT NULL THEN 1 ELSE 0 END)+"
            f"(CASE WHEN EXISTS(SELECT 1 FROM lf21_video_girls vg1 "
            f"WHERE vg1.video_id={a}.id) THEN 1 ELSE 0 END))"
        )
        return f"({field_count}>=4 AND {key_count}>=2)"

    def girls(self, favorites: bool = False) -> list[Girl]:
        with self.connect() as c:
            where = "WHERE g.favorite=1" if favorites else ""
            rows = c.execute(
                f"""
                SELECT g.*,
                  (SELECT COUNT(*) FROM lf21_links l WHERE l.girl_id=g.id) tracking,
                  (SELECT COUNT(*) FROM lf21_video_girls vg
                   JOIN lf21_videos v ON v.id=vg.video_id
                   WHERE vg.girl_id=g.id AND {self._valid_video_sql('v')}) occurrences
                FROM lf21_girls g {where}
                ORDER BY g.created_seq DESC,g.id DESC
                """
            ).fetchall()
            out: list[Girl] = []
            for r in rows:
                tags = tuple(
                    x[0]
                    for x in c.execute(
                        "SELECT c.name FROM lf21_girl_tags gt "
                        "JOIN lf21_catalog c ON c.id=gt.tag_id "
                        "WHERE gt.girl_id=? ORDER BY c.name COLLATE NOCASE",
                        (r["id"],),
                    )
                )
                out.append(
                    Girl(
                        id=int(r["id"]),
                        name=r["name"],
                        face=r["face"],
                        sex=r["sex"],
                        type_name=r["type_name"],
                        nudity=r["nudity"],
                        age_source=r["age_source"],
                        nationality=r["nationality"],
                        last_check=r["last_check"],
                        note=r["note"],
                        status=r["status"],
                        locked=bool(r["locked"]),
                        favorite=bool(r["favorite"]),
                        profile_path=r["profile_path"],
                        aliases=self._json_tuple(r["aliases_json"]),
                        tags=tags,
                        tracking=int(r["tracking"]),
                        occurrences=int(r["occurrences"]),
                        created_seq=int(r["created_seq"]),
                    )
                )
            return out

    def girl(self, girl_id: int) -> Girl | None:
        return next((g for g in self.girls(False) if g.id == girl_id), None)

    def add_girl(self, name: str = "") -> int:
        with self.connect() as c:
            cur = c.execute(
                "INSERT INTO lf21_girls(name,created_seq) VALUES(?,?)",
                (name.strip(), self._seq(c, "lf21_girls")),
            )
            return int(cur.lastrowid)

    def add_girls(self, count: int = 1) -> list[int]:
        return [self.add_girl("") for _ in range(max(1, count))]

    def find_girl_exact(self, text: str) -> tuple[int, str] | None:
        q = text.strip().casefold()
        if not q:
            return None
        for g in self.girls(False):
            if g.name.casefold() == q:
                return g.id, g.name
            for alias in g.aliases:
                if alias.casefold() == q:
                    return g.id, alias
        return None

    def girl_suggestions(self, text: str = "") -> list[tuple[str, int, int]]:
        q = text.strip().casefold()
        out: list[tuple[str, int, int]] = []
        for g in self.girls(False):
            names = (g.name,) + g.aliases
            if not q:
                if g.name:
                    out.append((g.name, g.id, g.occurrences))
                continue
            for name in names:
                n = name.strip()
                if n and q in n.casefold():
                    out.append((n, g.id, g.occurrences))
        out.sort(
            key=lambda x: (
                0 if x[0].casefold().startswith(q) else 1,
                -x[2],
                x[0].casefold(),
            )
        )
        return out

    def update_girl(self, girl_id: int, field: str, value) -> None:
        allowed = {
            "name", "face", "sex", "type_name", "nudity", "age_source",
            "nationality", "last_check", "note", "status", "profile_path",
        }
        if field not in allowed:
            raise KeyError(field)
        with self.connect() as c:
            c.execute(
                f"UPDATE lf21_girls SET {field}=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (str(value or ""), girl_id),
            )

    def set_girl_locked(self, girl_id: int, value: bool) -> None:
        with self.connect() as c:
            c.execute("UPDATE lf21_girls SET locked=? WHERE id=?", (int(value), girl_id))

    def set_favorite(self, girl_id: int, value: bool) -> None:
        with self.connect() as c:
            c.execute("UPDATE lf21_girls SET favorite=? WHERE id=?", (int(value), girl_id))

    def set_aliases(self, girl_id: int, aliases: Iterable[str]) -> None:
        cleaned = [str(x).strip() for x in aliases if str(x).strip()]
        with self.connect() as c:
            c.execute(
                "UPDATE lf21_girls SET aliases_json=? WHERE id=?",
                (json.dumps(cleaned, ensure_ascii=False), girl_id),
            )

    def set_tags(self, girl_id: int, tags: Iterable[str]) -> None:
        with self.connect() as c:
            c.execute("DELETE FROM lf21_girl_tags WHERE girl_id=?", (girl_id,))
            for tag in tags:
                name = str(tag).strip()
                if not name:
                    continue
                row = c.execute(
                    "SELECT id FROM lf21_catalog WHERE kind='tags' AND name=? COLLATE NOCASE",
                    (name,),
                ).fetchone()
                if row is None:
                    cur = c.execute(
                        "INSERT INTO lf21_catalog(kind,name,created_seq) VALUES('tags',?,?)",
                        (name, self._seq(c, "lf21_catalog")),
                    )
                    tag_id = int(cur.lastrowid)
                else:
                    tag_id = int(row[0])
                c.execute(
                    "INSERT OR IGNORE INTO lf21_girl_tags(girl_id,tag_id) VALUES(?,?)",
                    (girl_id, tag_id),
                )

    def delete_girls(self, ids: Sequence[int]) -> int:
        if not ids:
            return 0
        placeholders = ",".join("?" * len(ids))
        with self.connect() as c:
            cur = c.execute(
                f"DELETE FROM lf21_girls WHERE id IN ({placeholders}) AND locked=0",
                tuple(ids),
            )
            return int(cur.rowcount)

    def cleanup_blank_girls(self) -> None:
        with self.connect() as c:
            c.execute(
                """
                DELETE FROM lf21_girls
                WHERE TRIM(name)='' AND TRIM(face)='' AND TRIM(sex)=''
                  AND TRIM(type_name)='' AND TRIM(nudity)='' AND TRIM(age_source)=''
                  AND TRIM(nationality)='' AND TRIM(last_check)='' AND TRIM(note)=''
                  AND TRIM(status)='' AND favorite=0
                  AND NOT EXISTS(SELECT 1 FROM lf21_links l WHERE l.girl_id=lf21_girls.id)
                  AND NOT EXISTS(SELECT 1 FROM lf21_video_girls vg WHERE vg.girl_id=lf21_girls.id)
                """
            )

    def studios(self) -> list[Studio]:
        with self.connect() as c:
            rows = c.execute(
                f"""
                SELECT s.*,
                  (SELECT COUNT(*) FROM lf21_videos v
                   WHERE v.studio_id=s.id AND {self._valid_video_sql('v')}) occurrences
                FROM lf21_studios s
                ORDER BY s.created_seq DESC,s.id DESC
                """
            ).fetchall()
            return [
                Studio(
                    int(r["id"]), r["name"], r["type_name"], r["url"],
                    bool(r["locked"]), int(r["occurrences"]), int(r["created_seq"]),
                )
                for r in rows
            ]

    def add_studio(self, name: str = "") -> int:
        with self.connect() as c:
            existing = c.execute(
                "SELECT id FROM lf21_studios WHERE name=? COLLATE NOCASE",
                (name.strip(),),
            ).fetchone()
            if existing and name.strip():
                return int(existing[0])
            cur = c.execute(
                "INSERT INTO lf21_studios(name,created_seq) VALUES(?,?)",
                (name.strip(), self._seq(c, "lf21_studios")),
            )
            return int(cur.lastrowid)

    def update_studio(self, studio_id: int, field: str, value) -> None:
        if field not in {"name", "type_name", "url"}:
            raise KeyError(field)
        with self.connect() as c:
            c.execute(
                f"UPDATE lf21_studios SET {field}=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (str(value or ""), studio_id),
            )

    def set_studio_locked(self, studio_id: int, value: bool) -> None:
        with self.connect() as c:
            c.execute(
                "UPDATE lf21_studios SET locked=? WHERE id=?",
                (int(value), studio_id),
            )

    def delete_studios(self, ids: Sequence[int]) -> int:
        if not ids:
            return 0
        placeholders = ",".join("?" * len(ids))
        with self.connect() as c:
            cur = c.execute(
                f"DELETE FROM lf21_studios WHERE id IN ({placeholders}) AND locked=0",
                tuple(ids),
            )
            return int(cur.rowcount)

    def studio_suggestions(self, text: str = "") -> list[tuple[str, int, int]]:
        q = text.strip().casefold()
        rows = self.studios()
        rows.sort(key=lambda s: (-s.occurrences, s.name.casefold()))
        if not q:
            return [(s.name, s.id, s.occurrences) for s in rows if s.name]
        found = [s for s in rows if q in s.name.casefold()]
        found.sort(
            key=lambda s: (
                0 if s.name.casefold().startswith(q) else 1,
                -s.occurrences,
                s.name.casefold(),
            )
        )
        return [(s.name, s.id, s.occurrences) for s in found]

    def studio_by_name(self, name: str) -> Studio | None:
        q = name.strip().casefold()
        return next((s for s in self.studios() if s.name.casefold() == q), None)

    def videos(self, super_only: bool = False) -> list[Video]:
        with self.connect() as c:
            where = "WHERE v.in_super=1" if super_only else ""
            rows = c.execute(
                f"""
                SELECT v.*,COALESCE(s.name,'') studio_name
                FROM lf21_videos v
                LEFT JOIN lf21_studios s ON s.id=v.studio_id
                {where}
                ORDER BY v.created_seq DESC,v.id DESC
                """
            ).fetchall()
            occurrences = {g.id: g.occurrences for g in self.girls(False)}
            out: list[Video] = []
            for r in rows:
                participants = []
                for p in c.execute(
                    "SELECT g.id,g.name FROM lf21_video_girls vg "
                    "JOIN lf21_girls g ON g.id=vg.girl_id WHERE vg.video_id=?",
                    (r["id"],),
                ):
                    participants.append(
                        (int(p["id"]), str(p["name"]), occurrences.get(int(p["id"]), 0))
                    )
                participants.sort(key=lambda x: (-x[2], x[1].casefold()))
                out.append(
                    Video(
                        int(r["id"]), r["title"], r["studio_id"], r["studio_name"],
                        r["release_date"], r["state"], r["quality"],
                        r["available_quality"], r["size"], r["duration"],
                        r["mixed_gender"], r["note"], bool(r["locked"]),
                        bool(r["in_super"]), tuple(participants), int(r["created_seq"]),
                    )
                )
            return out

    def add_video(self) -> int:
        with self.connect() as c:
            cur = c.execute(
                "INSERT INTO lf21_videos(created_seq) VALUES(?)",
                (self._seq(c, "lf21_videos"),),
            )
            return int(cur.lastrowid)

    def update_video(self, video_id: int, field: str, value) -> None:
        allowed = {
            "title", "release_date", "state", "quality", "available_quality",
            "size", "duration", "mixed_gender", "note",
        }
        if field not in allowed:
            raise KeyError(field)
        with self.connect() as c:
            c.execute(
                f"UPDATE lf21_videos SET {field}=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (str(value or ""), video_id),
            )

    def set_video_studio(self, video_id: int, studio_id: int | None) -> None:
        with self.connect() as c:
            c.execute(
                "UPDATE lf21_videos SET studio_id=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (studio_id, video_id),
            )

    def set_video_locked(self, video_id: int, value: bool) -> None:
        with self.connect() as c:
            c.execute(
                "UPDATE lf21_videos SET locked=? WHERE id=?",
                (int(value), video_id),
            )

    def set_video_super(self, ids: Sequence[int], value: bool) -> None:
        if not ids:
            return
        placeholders = ",".join("?" * len(ids))
        with self.connect() as c:
            c.execute(
                f"UPDATE lf21_videos SET in_super=? WHERE id IN ({placeholders})",
                (int(value), *ids),
            )

    def set_video_participants(self, video_id: int, girl_ids: Iterable[int]) -> None:
        unique = list(dict.fromkeys(int(x) for x in girl_ids))
        with self.connect() as c:
            c.execute("DELETE FROM lf21_video_girls WHERE video_id=?", (video_id,))
            c.executemany(
                "INSERT OR IGNORE INTO lf21_video_girls(video_id,girl_id) VALUES(?,?)",
                [(video_id, girl_id) for girl_id in unique],
            )

    def replace_video_participant_slot(
        self, video_id: int, slot: int, girl_id: int | None
    ) -> None:
        video = next((v for v in self.videos(False) if v.id == video_id), None)
        ids = [p[0] for p in (video.participants if video else ())]
        while len(ids) <= slot:
            ids.append(0)
        ids[slot] = int(girl_id or 0)
        self.set_video_participants(video_id, [x for x in ids if x])

    def delete_videos(self, ids: Sequence[int]) -> int:
        if not ids:
            return 0
        placeholders = ",".join("?" * len(ids))
        with self.connect() as c:
            cur = c.execute(
                f"DELETE FROM lf21_videos WHERE id IN ({placeholders}) AND locked=0",
                tuple(ids),
            )
            return int(cur.rowcount)

    def link_types(self) -> list[dict]:
        with self.connect() as c:
            rows = c.execute(
                """
                SELECT t.*,COUNT(DISTINCT l.girl_id) distinct_girls,COUNT(l.id) total_links
                FROM lf21_link_types t
                LEFT JOIN lf21_links l ON l.type_id=t.id
                GROUP BY t.id
                ORDER BY distinct_girls DESC,total_links DESC,t.name COLLATE NOCASE
                """
            ).fetchall()
            return [dict(r) for r in rows]

    def add_link_type(self, category: str, name: str, web: str = "") -> int:
        with self.connect() as c:
            row = c.execute(
                "SELECT id FROM lf21_link_types WHERE name=? COLLATE NOCASE",
                (name.strip(),),
            ).fetchone()
            if row:
                return int(row[0])
            cur = c.execute(
                "INSERT INTO lf21_link_types(category,name,general_web,created_seq) VALUES(?,?,?,?)",
                (category, name.strip(), web.strip(), self._seq(c, "lf21_link_types")),
            )
            return int(cur.lastrowid)

    def update_link_type(self, type_id: int, category: str, name: str, web: str) -> None:
        with self.connect() as c:
            c.execute(
                "UPDATE lf21_link_types SET category=?,name=?,general_web=? WHERE id=?",
                (category, name, web, type_id),
            )

    def set_link_type_visibility(
        self,
        type_id: int,
        all_visible: bool | None = None,
        category_visible: bool | None = None,
    ) -> None:
        with self.connect() as c:
            if all_visible is not None:
                c.execute(
                    "UPDATE lf21_link_types SET visible_all=? WHERE id=?",
                    (int(all_visible), type_id),
                )
            if category_visible is not None:
                c.execute(
                    "UPDATE lf21_link_types SET visible_category=? WHERE id=?",
                    (int(category_visible), type_id),
                )

    def delete_link_type(self, type_id: int) -> None:
        with self.connect() as c:
            c.execute("DELETE FROM lf21_link_types WHERE id=?", (type_id,))

    def links(self) -> list[Link]:
        with self.connect() as c:
            rows = c.execute(
                """
                SELECT l.*,COALESCE(t.name,'') type_name,
                       COALESCE(t.category,'Zdroj') category,
                       COALESCE(g.name,'') girl_name
                FROM lf21_links l
                LEFT JOIN lf21_link_types t ON t.id=l.type_id
                LEFT JOIN lf21_girls g ON g.id=l.girl_id
                ORDER BY l.created_seq DESC,l.id DESC
                """
            ).fetchall()
            return [
                Link(
                    int(r["id"]), r["type_id"], r["type_name"], r["category"],
                    r["girl_id"], r["girl_name"], r["url"], r["check_value"],
                    r["downloaded"], r["active"], r["last_text"], r["last_image"],
                    bool(r["locked"]), int(r["created_seq"]),
                )
                for r in rows
            ]

    def detect_link_type(self, url: str) -> int | None:
        low = url.casefold()
        best = None
        for item in self.link_types():
            name = str(item["name"]).casefold().replace(" / ", " ").replace(".com", "")
            web = str(item["general_web"] or "").casefold()
            host = web.replace("https://", "").replace("http://", "").split("/")[0].replace("www.", "")
            tokens = [x for x in name.replace("/", " ").split() if len(x) > 2]
            if host and host in low:
                return int(item["id"])
            if any(token in low for token in tokens):
                best = int(item["id"])
        return best

    def add_link(self, type_id: int | None, girl_id: int | None, url: str, **extra) -> int:
        with self.connect() as c:
            cur = c.execute(
                """INSERT INTO lf21_links(
                       type_id,girl_id,url,check_value,downloaded,active,last_text,last_image,created_seq
                   ) VALUES(?,?,?,?,?,?,?,?,?)""",
                (
                    type_id, girl_id, url, extra.get("check_value", ""),
                    extra.get("downloaded", ""), extra.get("active", "Akt."),
                    extra.get("last_text", ""), extra.get("last_image", ""),
                    self._seq(c, "lf21_links"),
                ),
            )
            return int(cur.lastrowid)

    def update_link(self, link_id: int, field: str, value) -> None:
        if field not in {
            "url", "check_value", "downloaded", "active", "last_text", "last_image"
        }:
            raise KeyError(field)
        with self.connect() as c:
            c.execute(
                f"UPDATE lf21_links SET {field}=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (str(value or ""), link_id),
            )

    def set_link_type(self, link_id: int, type_id: int | None) -> None:
        with self.connect() as c:
            c.execute("UPDATE lf21_links SET type_id=? WHERE id=?", (type_id, link_id))

    def set_link_girl(self, link_id: int, girl_id: int | None) -> None:
        with self.connect() as c:
            c.execute("UPDATE lf21_links SET girl_id=? WHERE id=?", (girl_id, link_id))

    def set_link_locked(self, link_id: int, value: bool) -> None:
        with self.connect() as c:
            c.execute("UPDATE lf21_links SET locked=? WHERE id=?", (int(value), link_id))

    def delete_links(self, ids: Sequence[int]) -> int:
        if not ids:
            return 0
        placeholders = ",".join("?" * len(ids))
        with self.connect() as c:
            cur = c.execute(
                f"DELETE FROM lf21_links WHERE id IN ({placeholders}) AND locked=0",
                tuple(ids),
            )
            return int(cur.rowcount)

    def overview(self) -> dict:
        girls = self.girls(False)
        favorites = [g for g in girls if g.favorite]
        videos = self.videos(False)
        super_videos = [v for v in videos if v.in_super]
        return {
            "girls": len(girls),
            "favorites": len(favorites),
            "videos": len(videos),
            "super": len(super_videos),
            "studios": len(self.studios()),
            "links": len(self.links()),
            "tags": len(self.catalog_rows("tags")),
        }
