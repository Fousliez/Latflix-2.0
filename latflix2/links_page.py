from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import QLabel, QTableView, QVBoxLayout, QWidget

from .database import LinkRecord, Repository


class LinksModel(QAbstractTableModel):
    HEADERS = ("Herečka", "Zdroj", "URL")

    def __init__(self, repository: Repository, parent=None):
        super().__init__(parent)
        self.repository = repository
        self.rows: list[LinkRecord] = []

    def load(self, girl_id: int | None = None) -> None:
        self.beginResetModel()
        self.rows = list(self.repository.all_links(girl_id))
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 3

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = self.rows[index.row()]
        if role == Qt.DisplayRole:
            return (row.girl_name, row.source, row.url)[index.column()]
        if role == Qt.UserRole:
            return row.id
        return None

    def headerData(self, section: int, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.HEADERS[section]
        return None


class LinksPage(QWidget):
    def __init__(self, repository: Repository, parent=None):
        super().__init__(parent)
        self.repository = repository
        self.model = LinksModel(repository, self)
        self.filtered_girl_id: int | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.title = QLabel("Odkazy", self)
        self.title.setObjectName("pageTitle")
        root.addWidget(self.title)

        self.table = QTableView(self)
        self.table.setModel(self.model)
        self.table.setSortingEnabled(False)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setStretchLastSection(True)
        root.addWidget(self.table, 1)

    def load(self, girl_id: int | None = None) -> None:
        self.filtered_girl_id = girl_id
        self.model.load(girl_id)
        if girl_id is None:
            self.title.setText("Odkazy")
        else:
            girl = self.repository.girl(girl_id)
            label = girl.name if girl and girl.name else f"#{girl_id}"
            self.title.setText(f"Odkazy – {label}")
