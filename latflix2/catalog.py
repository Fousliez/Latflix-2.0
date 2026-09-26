from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from .database import CatalogEntry, Repository


class CatalogModel(QAbstractTableModel):
    def __init__(self, repository: Repository, kind: str, with_color: bool, parent=None):
        super().__init__(parent)
        self.repository = repository
        self.kind = kind
        self.with_color = with_color
        self.rows: list[CatalogEntry] = []
        self.reload()

    def reload(self) -> None:
        self.beginResetModel()
        self.rows = list(self.repository.catalog(self.kind))
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 2 if self.with_color else 1

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        entry = self.rows[index.row()]
        if role in (Qt.DisplayRole, Qt.EditRole):
            return entry.name if index.column() == 0 else entry.color
        if role == Qt.UserRole:
            return entry.id
        return None

    def headerData(self, section: int, orientation, role=Qt.DisplayRole):
        if orientation != Qt.Horizontal or role != Qt.DisplayRole:
            return None
        return ("Název", "Barva")[section]

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def setData(self, index: QModelIndex, value, role=Qt.EditRole) -> bool:
        if role != Qt.EditRole or not index.isValid():
            return False
        entry = self.rows[index.row()]
        if index.column() == 0:
            self.repository.update_catalog_entry(entry.id, name=str(value or ""))
        else:
            self.repository.update_catalog_entry(entry.id, color=str(value or ""))
        self.reload()
        return True


class CatalogPage(QWidget):
    changed = Signal()

    def __init__(self, repository: Repository, kind: str, with_color: bool = False, parent=None):
        super().__init__(parent)
        self.repository = repository
        self.kind = kind
        self.model = CatalogModel(repository, kind, with_color, self)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        toolbar = QHBoxLayout()
        add = QPushButton("Přidat", self)
        delete = QPushButton("Smazat", self)
        add.clicked.connect(self.add)
        delete.clicked.connect(self.delete)
        toolbar.addWidget(add)
        toolbar.addWidget(delete)
        toolbar.addStretch(1)
        root.addLayout(toolbar)

        self.table = QTableView(self)
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().hide()
        root.addWidget(self.table, 1)

    def reload(self) -> None:
        self.model.reload()

    def add(self) -> None:
        entry_id = self.repository.add_catalog_entry(self.kind)
        self.model.reload()
        for row, entry in enumerate(self.model.rows):
            if entry.id == entry_id:
                self.table.selectRow(row)
                self.table.edit(self.model.index(row, 0))
                break
        self.changed.emit()

    def delete(self) -> None:
        selection = self.table.selectionModel()
        if selection is None:
            return
        ids = [
            self.model.rows[index.row()].id
            for index in selection.selectedRows()
            if 0 <= index.row() < len(self.model.rows)
        ]
        self.repository.delete_catalog_entries(ids)
        self.model.reload()
        self.changed.emit()
