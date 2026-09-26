from __future__ import annotations

from dataclasses import replace
from datetime import date

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from .database import GirlRecord, Repository
from .schema import GIRL_COLUMNS, ColumnSpec, display_age


ROLE_RECORD_ID = Qt.UserRole + 1
ROLE_COLUMN_KEY = Qt.UserRole + 2
ROLE_LOCKED = Qt.UserRole + 3
ROLE_RAW_VALUE = Qt.UserRole + 4
ROLE_COLUMN_KIND = Qt.UserRole + 5


class GirlTableModel(QAbstractTableModel):
    SYSTEM_COLUMNS = 2

    def __init__(self, repository: Repository, parent=None):
        super().__init__(parent)
        self.repository = repository
        self.category = "Girls"
        self.records: list[GirlRecord] = []
        self.title_overrides: dict[str, str] = {}
        self.header_locked = True

    def set_records(self, records: tuple[GirlRecord, ...] | list[GirlRecord], category: str) -> None:
        self.beginResetModel()
        self.records = list(records)
        self.category = str(category)
        self.endResetModel()

    def set_title_overrides(self, values: dict[str, str]) -> None:
        self.title_overrides = dict(values)
        if self.columnCount():
            self.headerDataChanged.emit(Qt.Horizontal, 0, self.columnCount() - 1)

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.records)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else self.SYSTEM_COLUMNS + len(GIRL_COLUMNS)

    def column_spec(self, column: int) -> ColumnSpec | None:
        index = int(column) - self.SYSTEM_COLUMNS
        if 0 <= index < len(GIRL_COLUMNS):
            return GIRL_COLUMNS[index]
        return None

    def record_at(self, row: int) -> GirlRecord | None:
        if 0 <= row < len(self.records):
            return self.records[row]
        return None

    def record_id(self, row: int) -> int | None:
        record = self.record_at(row)
        return None if record is None else record.id

    def index_for_record(self, record_id: int, column: int = 2) -> QModelIndex:
        for row, record in enumerate(self.records):
            if record.id == int(record_id):
                return self.index(row, column)
        return QModelIndex()

    def _raw(self, record: GirlRecord, spec: ColumnSpec):
        return getattr(record, spec.key)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        record = self.records[index.row()]
        column = index.column()

        if role == ROLE_RECORD_ID:
            return record.id
        if role == ROLE_LOCKED:
            return record.locked

        if column == 0:
            if role == Qt.DisplayRole:
                return "🔒" if record.locked else "🔓"
            if role == Qt.TextAlignmentRole:
                return int(Qt.AlignCenter)
            return None

        if column == 1:
            if role == Qt.DisplayRole:
                return index.row() + 1
            if role == Qt.TextAlignmentRole:
                return int(Qt.AlignCenter)
            return None

        spec = self.column_spec(column)
        if spec is None:
            return None

        if role == ROLE_COLUMN_KEY:
            return spec.key
        if role == ROLE_COLUMN_KIND:
            return spec.kind

        raw = self._raw(record, spec)
        if role == ROLE_RAW_VALUE:
            return raw

        if role in (Qt.DisplayRole, Qt.EditRole):
            if spec.kind == "age":
                return record.age_source if role == Qt.EditRole else display_age(record.age_source, date.today().year)
            if spec.kind == "tags":
                return ", ".join(record.tags)
            if spec.key in {"tracking", "occurrences"}:
                return str(int(raw))
            return str(raw or "")

        if role == Qt.ToolTipRole and spec.key == "note":
            return record.note or None

        if role == Qt.TextAlignmentRole and spec.key in {"tracking", "occurrences", "age_source"}:
            return int(Qt.AlignCenter)

        return None

    def headerData(self, section: int, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Vertical:
            return None
        if section == 0:
            return "🔒" if self.header_locked else "🔓"
        if section == 1:
            return "#"
        spec = self.column_spec(section)
        if spec is None:
            return None
        return self.title_overrides.get(spec.key, spec.title)

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.NoItemFlags
        base = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        record = self.records[index.row()]
        if index.column() < self.SYSTEM_COLUMNS:
            return base
        spec = self.column_spec(index.column())
        if spec is None or record.locked or spec.read_only:
            return base
        if spec.kind in {"text", "choice", "age"}:
            return base | Qt.ItemIsEditable
        return base

    def setData(self, index: QModelIndex, value, role=Qt.EditRole) -> bool:
        if role != Qt.EditRole or not index.isValid():
            return False
        record = self.records[index.row()]
        spec = self.column_spec(index.column())
        if spec is None or record.locked or spec.read_only:
            return False
        text = str(value or "")
        current = str(getattr(record, spec.key) or "")
        if current == text:
            return True
        self.repository.update_field(record.id, spec.key, text)
        self.records[index.row()] = replace(record, **{spec.key: text}, is_new=False if text.strip() else record.is_new)
        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole, ROLE_RAW_VALUE])
        return True

    def refresh_record(self, record_id: int) -> bool:
        fresh = self.repository.girl(record_id)
        if fresh is None:
            return False
        for row, record in enumerate(self.records):
            if record.id == int(record_id):
                self.records[row] = fresh
                left = self.index(row, 0)
                right = self.index(row, self.columnCount() - 1)
                self.dataChanged.emit(left, right)
                return True
        return False
