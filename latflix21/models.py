from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Callable

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QSortFilterProxyModel, Qt
from PySide6.QtGui import QColor

from .db import CatalogRow, Girl, Link, Repository, Studio, Video


ROLE_RECORD_ID = Qt.UserRole + 1
ROLE_LOCKED = Qt.UserRole + 2
ROLE_SORT = Qt.UserRole + 3


@dataclass(frozen=True)
class Col:
    key: str
    title: str
    kind: str = "text"
    width: int = 120
    source: str | None = None
    read_only: bool = False
    primary_text: bool = False


def age_display(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        number = int(text)
    except Exception:
        return text
    if 1 <= number <= 100:
        return str(number)
    if 1800 <= number <= date.today().year:
        return str(date.today().year - number)
    return text


class BaseModel(QAbstractTableModel):
    columns: tuple[Col, ...] = ()

    def __init__(self, repo: Repository):
        super().__init__()
        self.repo = repo
        self.rows = []
        self.title_overrides: dict[str, str] = {}
        self.reload()

    def reload(self) -> None:
        self.beginResetModel()
        self.rows = list(self.load_rows())
        self.endResetModel()

    def load_rows(self):
        return []

    def record_id(self, row: int) -> int:
        return int(self.rows[row].id)

    def locked(self, row: int) -> bool:
        return bool(getattr(self.rows[row], "locked", False))

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.columns) + 2

    def col(self, column: int) -> Col:
        if column == 0:
            return Col("_lock", "", kind="lock", width=36)
        if column == 1:
            return Col("_row", "#", kind="row", width=44, read_only=True)
        return self.columns[column - 2]

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation != Qt.Horizontal or role != Qt.DisplayRole:
            return None
        col = self.col(section)
        if col.key == "_lock":
            return ""
        return self.title_overrides.get(col.key, col.title)

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        base = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        col = self.col(index.column())
        if col.kind == "lock":
            return base | Qt.ItemIsEditable
        if self.locked(index.row()) or col.read_only or col.kind in {"row", "computed", "button", "image_button"}:
            return base
        return base | Qt.ItemIsEditable

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        record = self.rows[index.row()]
        col = self.col(index.column())

        if role == ROLE_RECORD_ID:
            return int(record.id)
        if role == ROLE_LOCKED:
            return bool(getattr(record, "locked", False))

        if role in (Qt.DisplayRole, Qt.EditRole):
            if col.kind == "lock":
                return "🔒" if self.locked(index.row()) else "🔓"
            if col.kind == "row":
                return index.row() + 1
            value = self.value(record, col.key)
            if col.key == "age_source" and role == Qt.DisplayRole:
                return age_display(value)
            return value

        if role == ROLE_SORT:
            if col.kind == "row":
                return index.row() + 1
            if col.kind == "lock":
                return int(self.locked(index.row()))
            return self.sort_value(record, col.key)

        if role == Qt.TextAlignmentRole and col.kind in {"row", "computed", "lock", "button", "image_button"}:
            return int(Qt.AlignCenter)

        if role == Qt.BackgroundRole and col.kind == "lock":
            return QColor("#454545") if self.locked(index.row()) else QColor("#ffffff")
        if role == Qt.ForegroundRole and col.kind == "lock" and self.locked(index.row()):
            return QColor("#ffffff")

        return self.extra_data(record, col, index, role)

    def value(self, record, key):
        return getattr(record, key, "")

    def sort_value(self, record, key):
        value = self.value(record, key)
        if isinstance(value, (int, float)):
            return value
        if key == "age_source":
            shown = age_display(str(value))
            try:
                return int(shown)
            except Exception:
                return -1
        return str(value or "").casefold()

    def extra_data(self, record, col, index, role):
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole or not index.isValid():
            return False
        col = self.col(index.column())
        record = self.rows[index.row()]
        if col.kind == "lock":
            self.set_locked(record.id, not self.locked(index.row()))
            self.reload()
            return True
        if not (self.flags(index) & Qt.ItemIsEditable):
            return False
        ok = self.set_value(record, col, str(value or ""))
        if ok:
            self.reload()
        return ok

    def set_locked(self, row_id: int, value: bool):
        raise NotImplementedError

    def set_value(self, record, col, value) -> bool:
        return False

    def search_blob(self, row: int) -> str:
        return " ".join(
            str(self.data(self.index(row, column), Qt.DisplayRole) or "")
            for column in range(2, self.columnCount())
        )

    def set_title_override(self, key: str, title: str) -> None:
        self.title_overrides[key] = title
        self.headerDataChanged.emit(Qt.Horizontal, 0, self.columnCount() - 1)


GIRL_COLS = (
    Col("name", "Jméno", width=190, primary_text=True),
    Col("face", "Obličej", "choice", 105, source="face"),
    Col("sex", "Sex", "choice", 90, source="yes"),
    Col("type_name", "Typ", "choice", 120, source="types"),
    Col("nudity", "Nahota", "choice", 100, source="yes"),
    Col("age_source", "Věk", width=70),
    Col("nationality", "Národnost", "choice", 130, source="nationalities"),
    Col("tags", "Tagy", "tags", 170),
    Col("tracking", "Sledování", "computed", 90, read_only=True),
    Col("last_check", "Posl. kontrola", width=120),
    Col("occurrences", "Počet výskytů", "computed", 110, read_only=True),
    Col("note", "Pozn.", "note", 210),
    Col("status", "Stav", "choice", 110, source="girl_status"),
)


class GirlsModel(BaseModel):
    columns = GIRL_COLS

    def __init__(self, repo: Repository, favorites: bool = False):
        self.favorites = favorites
        super().__init__(repo)

    def load_rows(self):
        return self.repo.girls(self.favorites)

    def value(self, record: Girl, key):
        if key == "tags":
            return ", ".join(record.tags)
        return super().value(record, key)

    def set_locked(self, row_id, value):
        self.repo.set_girl_locked(row_id, value)

    def set_value(self, record, col, value):
        self.repo.update_girl(record.id, col.key, value)
        return True

    def search_blob(self, row):
        girl = self.rows[row]
        return super().search_blob(row) + " " + " ".join(girl.aliases)


STUDIO_COLS = (
    Col("name", "Název", width=220),
    Col("type_name", "Typ", width=170),
    Col("url", "Odkaz", width=320),
    Col("occurrences", "Počet výskytů", "computed", 120, read_only=True),
)


class StudiosModel(BaseModel):
    columns = STUDIO_COLS

    def load_rows(self):
        return self.repo.studios()

    def set_locked(self, row_id, value):
        self.repo.set_studio_locked(row_id, value)

    def set_value(self, record, col, value):
        self.repo.update_studio(record.id, col.key, value)
        return True


VIDEO_COLS = (
    Col("title", "Název", width=250, primary_text=True),
    Col("studio_name", "Studio", "autocomplete", 180, source="studios"),
    Col("release_date", "Datum vydání", width=110),
    Col("girl0", "Dívka 1", "autocomplete", 165, source="girls"),
    Col("girl1", "Dívka 2", "autocomplete", 165, source="girls"),
    Col("girl2", "Dívka 3", "autocomplete", 165, source="girls"),
    Col("state", "Stav", "choice", 105, source="states"),
    Col("quality", "Kvalita", "choice", 100, source="qualities"),
    Col("available_quality", "Dostup. kvalita", "choice", 120, source="qualities"),
    Col("size", "Velikost", width=95),
    Col("duration", "Délka", width=85),
    Col("mixed_gender", "M+Ž", "choice", 75, source="yesno"),
    Col("note", "Poznámka", "note", 220),
)


class VideosModel(BaseModel):
    columns = VIDEO_COLS

    def __init__(self, repo, super_only=False):
        self.super_only = super_only
        self.unknown_girl: Callable[[str], int | None] | None = None
        self.unknown_studio: Callable[[str], Any] | None = None
        super().__init__(repo)

    def load_rows(self):
        return self.repo.videos(self.super_only)

    def value(self, record: Video, key):
        if key.startswith("girl") and key[-1].isdigit():
            idx = int(key[-1])
            return record.participants[idx][1] if idx < len(record.participants) else ""
        return super().value(record, key)

    def sort_value(self, record: Video, key):
        if key.startswith("girl") and key[-1].isdigit():
            return str(self.value(record, key) or "").casefold()
        return super().sort_value(record, key)

    def set_locked(self, row_id, value):
        self.repo.set_video_locked(row_id, value)

    def flags(self, index):
        flags = super().flags(index)
        if not index.isValid():
            return flags
        col = self.col(index.column())
        if (
            self.rows[index.row()].state.strip().upper() == "NECHCI"
            and col.key in {"quality", "available_quality", "size"}
        ):
            return flags & ~Qt.ItemIsEditable
        return flags

    def extra_data(self, record, col, index, role):
        if role == Qt.BackgroundRole and record.state.strip().upper() == "NECHCI":
            if col.key in {"state", "_row"}:
                return QColor("#ef9a9a")
            if col.key in {"quality", "available_quality", "size"}:
                return QColor("#d7d7d7")
        if role == Qt.ForegroundRole and record.state.strip().upper() == "NECHCI":
            if col.key in {"quality", "available_quality", "size"}:
                return QColor("#777777")
        return None

    def set_value(self, record: Video, col, value):
        if col.key == "studio_name":
            text = value.strip()
            if not text:
                self.repo.set_video_studio(record.id, None)
                return True
            studio = self.repo.studio_by_name(text)
            if not studio and self.unknown_studio:
                studio = self.unknown_studio(text)
            if not studio:
                return False
            studio_id = studio.id if hasattr(studio, "id") else int(studio)
            self.repo.set_video_studio(record.id, studio_id)
            return True

        if col.key.startswith("girl") and col.key[-1].isdigit():
            text = value.strip()
            slot = int(col.key[-1])
            if not text:
                self.repo.replace_video_participant_slot(record.id, slot, None)
                return True
            found = self.repo.find_girl_exact(text)
            if not found and self.unknown_girl:
                girl_id = self.unknown_girl(text)
                found = (girl_id, text) if girl_id else None
            if not found:
                return False
            self.repo.replace_video_participant_slot(record.id, slot, found[0])
            return True

        self.repo.update_video(record.id, col.key, value)
        return True

    def search_blob(self, row):
        video = self.rows[row]
        chunks = [super().search_blob(row)]
        for girl_id, _, _ in video.participants:
            girl = self.repo.girl(girl_id)
            if girl:
                chunks.append(" ".join((girl.name, *girl.aliases)))
        return " ".join(chunks)


LINK_COLS = (
    Col("type_name", "Název", "choice", 180, source="link_types"),
    Col("girl_name", "Herečka", "autocomplete", 180, source="girls"),
    Col("url", "URL", width=360),
    Col("check_value", "Kontrola", width=110),
    Col("downloaded", "Staženo", width=100),
    Col("active", "Akt.", "choice", 70, source="active"),
    Col("web", "Web", "button", 80, read_only=True),
    Col("last_text", "Poslední text", width=240),
    Col("last_image", "Poslední obrázek", "image_button", 180, read_only=True),
)


class LinksModel(BaseModel):
    columns = LINK_COLS

    def __init__(self, repo):
        self.unknown_girl: Callable[[str], int | None] | None = None
        super().__init__(repo)

    def load_rows(self):
        return self.repo.links()

    def value(self, record: Link, key):
        if key == "web":
            return "Otevřít"
        if key == "last_image":
            return record.last_image if record.last_image else "Nahrát"
        return super().value(record, key)

    def set_locked(self, row_id, value):
        self.repo.set_link_locked(row_id, value)

    def search_blob(self, row):
        link = self.rows[row]
        text = super().search_blob(row)
        if link.girl_id:
            girl = self.repo.girl(link.girl_id)
            if girl:
                text += " " + " ".join((girl.name, *girl.aliases))
        return text

    def set_value(self, record: Link, col, value):
        if col.key == "type_name":
            text = value.strip()
            if not text:
                self.repo.set_link_type(record.id, None)
                return True
            item = next(
                (
                    x
                    for x in self.repo.link_types()
                    if str(x["name"]).casefold() == text.casefold()
                ),
                None,
            )
            if not item:
                return False
            self.repo.set_link_type(record.id, int(item["id"]))
            return True

        if col.key == "girl_name":
            text = value.strip()
            if not text:
                self.repo.set_link_girl(record.id, None)
                return True
            found = self.repo.find_girl_exact(text)
            if not found and self.unknown_girl:
                girl_id = self.unknown_girl(text)
                found = (girl_id, text) if girl_id else None
            if not found:
                return False
            self.repo.set_link_girl(record.id, found[0])
            return True

        self.repo.update_link(record.id, col.key, value)
        return True


class CatalogModel(BaseModel):
    def __init__(self, repo: Repository, kind: str, with_color: bool = False):
        self.kind = kind
        self.with_color = with_color
        self.columns = (
            (Col("name", "Název", width=260), Col("color", "Barva", kind="color", width=150))
            if with_color
            else (Col("name", "Název", width=280),)
        )
        super().__init__(repo)

    def load_rows(self):
        return self.repo.catalog_rows(self.kind)

    def set_locked(self, row_id, value):
        self.repo.set_catalog_locked(row_id, value)

    def extra_data(self, record: CatalogRow, col, index, role):
        if self.with_color and col.key == "color" and role == Qt.BackgroundRole:
            try:
                return QColor(record.color)
            except Exception:
                return None
        return None

    def set_value(self, record: CatalogRow, col, value):
        if col.key == "name":
            self.repo.update_catalog(record.id, name=value)
        elif col.key == "color":
            self.repo.update_catalog(record.id, color=value)
        else:
            return False
        return True


class SmartProxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.query = ""
        self.filters: dict[str, set[str]] = {}
        self.predicate: Callable[[Any], bool] | None = None
        self.setDynamicSortFilter(True)
        self.setSortCaseSensitivity(Qt.CaseInsensitive)

    def set_query(self, query: str):
        self.query = query.strip().casefold()
        self.invalidateFilter()

    def set_filter_values(self, key: str, values: set[str]):
        self.filters[key] = set(values)
        self.invalidateFilter()

    def clear_filters(self):
        self.query = ""
        self.filters.clear()
        self.predicate = None
        self.invalidateFilter()

    def accepts_without_query(self, source_row: int) -> bool:
        model = self.sourceModel()
        record = model.rows[source_row]
        for key, values in self.filters.items():
            if not values:
                continue
            if str(getattr(record, key, "")) not in values:
                return False
        if self.predicate and not self.predicate(record):
            return False
        return True

    def filterAcceptsRow(self, source_row, parent):
        model = self.sourceModel()
        if self.query and self.query not in model.search_blob(source_row).casefold():
            return False
        return self.accepts_without_query(source_row)

    def lessThan(self, left, right):
        lv = left.data(ROLE_SORT)
        rv = right.data(ROLE_SORT)
        if isinstance(lv, (int, float)) and isinstance(rv, (int, float)):
            return lv < rv
        return str(lv or "").casefold() < str(rv or "").casefold()

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and index.column() == 1 and role in (Qt.DisplayRole, Qt.EditRole, ROLE_SORT):
            return index.row() + 1
        return super().data(index, role)
