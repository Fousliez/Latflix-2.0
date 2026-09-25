from __future__ import annotations

from PySide6.QtCore import QSortFilterProxyModel, Qt


class TableFilterProxy(QSortFilterProxyModel):
    """Jedna rychlá filtrační vrstva pro text i sloupcové filtry."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._search = ""
        self._column_filters: dict[int, str] = {}
        self.setDynamicSortFilter(True)

    def set_search(self, text: str) -> None:
        value = str(text or "").strip().casefold()
        if value == self._search:
            return
        self._search = value
        self.invalidateFilter()

    def set_column_filter(self, column: int, value: str) -> None:
        value = str(value or "").strip()
        if not value or value == "Vše":
            self._column_filters.pop(int(column), None)
        else:
            self._column_filters[int(column)] = value.casefold()
        self.invalidateFilter()

    def clear_column_filters(self) -> None:
        if not self._column_filters:
            return
        self._column_filters.clear()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent) -> bool:
        model = self.sourceModel()
        if model is None:
            return True

        for column, wanted in self._column_filters.items():
            index = model.index(source_row, column, source_parent)
            actual = str(model.data(index, Qt.EditRole) or "").casefold()
            if wanted not in actual:
                return False

        if not self._search:
            return True
        for column in range(model.columnCount(source_parent)):
            index = model.index(source_row, column, source_parent)
            value = str(model.data(index, Qt.EditRole) or "").casefold()
            if self._search in value:
                return True
        return False
