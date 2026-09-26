from __future__ import annotations

from datetime import date

from PySide6.QtCore import QModelIndex, QSortFilterProxyModel, Qt
from PySide6.QtGui import QColor

from .model import GirlTableModel
from .schema import display_age


class GirlFilterProxy(QSortFilterProxyModel):
    """One filter/sort layer. It never owns or mutates application data."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._search = ""
        self._filters: dict[str, str] = {}
        self.setDynamicSortFilter(True)

    @property
    def search_text(self) -> str:
        return self._search

    @property
    def filters(self) -> dict[str, str]:
        return dict(self._filters)

    def set_search(self, text: str) -> None:
        value = str(text or "").strip().casefold()
        if value == self._search:
            return
        self._search = value
        self.invalidateFilter()

    def set_filter(self, key: str, value: str) -> None:
        value = str(value or "").strip()
        if value:
            self._filters[str(key)] = value
        else:
            self._filters.pop(str(key), None)
        self.invalidateFilter()

    def clear_filters(self) -> None:
        self._filters.clear()
        self.invalidateFilter()

    def _model(self) -> GirlTableModel | None:
        model = self.sourceModel()
        return model if isinstance(model, GirlTableModel) else None

    def matches_filters(self, source_row: int) -> bool:
        model = self._model()
        if model is None:
            return True
        record = model.record_at(source_row)
        if record is None:
            return False

        for key, wanted in self._filters.items():
            wanted_folded = wanted.casefold()
            if key == "profile":
                actual = "Ano" if record.profile_path.strip() else "Ne"
            elif key == "tags":
                if not any(wanted_folded == value.casefold() for value in record.tags):
                    return False
                continue
            else:
                actual = str(getattr(record, key, "") or "")
            if actual.casefold() != wanted_folded:
                return False
        return True

    def _matches_search(self, source_row: int) -> bool:
        if not self._search:
            return True
        model = self._model()
        if model is None:
            return True
        record = model.record_at(source_row)
        if record is None:
            return False
        values = (
            record.name, *record.aliases, record.face, record.sex, record.type_name,
            record.nudity, display_age(record.age_source, date.today().year),
            record.nationality, *record.tags, str(record.tracking), record.last_check,
            str(record.occurrences), record.note, record.status,
        )
        return any(self._search in str(value or "").casefold() for value in values)

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        return self.matches_filters(source_row) and self._matches_search(source_row)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole and index.column() == 1:
            return index.row() + 1
        if role == Qt.BackgroundRole:
            if index.column() == 0:
                return QColor("#f5f5f5")
            return QColor("#ffffff" if index.row() % 2 == 0 else "#f2f2f2")
        return super().data(index, role)

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        model = self._model()
        if model is None:
            return super().lessThan(left, right)
        spec = model.column_spec(left.column())
        l_record = model.record_at(left.row())
        r_record = model.record_at(right.row())
        if spec is None or l_record is None or r_record is None:
            return super().lessThan(left, right)

        if spec.key == "age_source":
            def age_num(raw: str) -> int:
                value = display_age(raw, date.today().year)
                try:
                    return int(value)
                except ValueError:
                    return -1
            return age_num(l_record.age_source) < age_num(r_record.age_source)

        if spec.key in {"tracking", "occurrences"}:
            return int(getattr(l_record, spec.key)) < int(getattr(r_record, spec.key))

        if spec.key == "tags":
            return ", ".join(l_record.tags).casefold() < ", ".join(r_record.tags).casefold()

        return str(getattr(l_record, spec.key, "") or "").casefold() < str(
            getattr(r_record, spec.key, "") or ""
        ).casefold()

    def source_rows_matching_filters(self) -> list[int]:
        model = self._model()
        if model is None:
            return []
        return [row for row in range(model.rowCount()) if self.matches_filters(row)]
