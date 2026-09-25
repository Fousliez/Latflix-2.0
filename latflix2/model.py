from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from .database import Dataset, Repository, Row


class TableModel(QAbstractTableModel):
    def __init__(self, repository: Repository, parent=None):
        super().__init__(parent)
        self.repository = repository
        self.dataset = Dataset("", (), ())

    def set_dataset(self, dataset: Dataset) -> None:
        self.beginResetModel()
        self.dataset = dataset
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.dataset.rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.dataset.columns)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = self.dataset.rows[index.row()]
        column = self.dataset.columns[index.column()]
        raw = row.values[index.column()]
        if role == Qt.DisplayRole:
            if (
                self.dataset.category in {"Girls", "Oblíbené"}
                and column.name == "Jméno"
                and row.id in self.dataset.favorite_ids
            ):
                return f"{raw} ★"
            return raw
        if role == Qt.EditRole:
            return raw
        if role == Qt.TextAlignmentRole:
            return int(Qt.AlignVCenter | Qt.AlignLeft)
        if role == Qt.UserRole:
            return row.id
        return None

    def headerData(self, section: int, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            if 0 <= section < len(self.dataset.columns):
                return self.dataset.columns[section].name
            return None
        return str(section + 1)

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def setData(self, index: QModelIndex, value, role=Qt.EditRole) -> bool:
        if role != Qt.EditRole or not index.isValid():
            return False
        row = self.dataset.rows[index.row()]
        column = self.dataset.columns[index.column()]
        text = str(value or "")
        if text == row.values[index.column()]:
            return True
        self.repository.update_cell(row.id, column.id, text)

        values = list(row.values)
        values[index.column()] = text
        rows = list(self.dataset.rows)
        rows[index.row()] = Row(row.id, tuple(values))
        self.dataset = Dataset(
            self.dataset.category,
            self.dataset.columns,
            tuple(rows),
            self.dataset.favorite_ids,
        )
        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
        return True

    def record_id(self, source_row: int) -> int | None:
        if 0 <= source_row < len(self.dataset.rows):
            return self.dataset.rows[source_row].id
        return None

    def row_object(self, source_row: int) -> Row | None:
        if 0 <= source_row < len(self.dataset.rows):
            return self.dataset.rows[source_row]
        return None
