from __future__ import annotations

from PySide6.QtCore import QModelIndex, QPoint, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QComboBox,
    QHeaderView,
    QTableView,
)

from .delegates import TableDelegate
from .model import ROLE_LOCKED, ROLE_RECORD_ID
from .proxy import GirlFilterProxy


class DataTable(QTableView):
    lock_requested = Signal(int, bool)
    tags_requested = Signal(int)
    note_requested = Signal(int)
    locked_primary_copy_requested = Signal(str)
    header_lock_changed = Signal(bool)
    header_layout_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.header_locked = True
        self._sort_column = -1
        self._sort_order = Qt.AscendingOrder

        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setAlternatingRowColors(False)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.verticalHeader().hide()
        self.horizontalHeader().setSortIndicatorShown(False)
        self.horizontalHeader().setSectionsMovable(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.horizontalHeader().sectionClicked.connect(self._header_clicked)
        self.horizontalHeader().sectionMoved.connect(lambda *_: self.header_layout_changed.emit())
        self.horizontalHeader().sectionResized.connect(lambda *_: self.header_layout_changed.emit())

        self.clicked.connect(self._clicked)
        self.doubleClicked.connect(self._double_clicked)

    def bind_delegate(self, delegate: TableDelegate) -> None:
        self.setItemDelegate(delegate)
        delegate.request_next_text_cell.connect(self._edit_next_text_cell)

    def set_header_locked(self, locked: bool) -> None:
        self.header_locked = bool(locked)
        header = self.horizontalHeader()
        header.setSectionsMovable(not self.header_locked)
        header.setSectionResizeMode(QHeaderView.Fixed if self.header_locked else QHeaderView.Interactive)
        self.header_lock_changed.emit(self.header_locked)
        header.viewport().update()

    def _header_clicked(self, section: int) -> None:
        if section == 0:
            self.set_header_locked(not self.header_locked)
            return
        if section < 2:
            return
        model = self.model()
        if model is None:
            return
        if section == self._sort_column:
            self._sort_order = (
                Qt.DescendingOrder if self._sort_order == Qt.AscendingOrder else Qt.AscendingOrder
            )
        else:
            self._sort_column = section
            self._sort_order = Qt.AscendingOrder
        sorter = getattr(model, "sort", None)
        if callable(sorter):
            sorter(section, self._sort_order)
        self.horizontalHeader().setSortIndicatorShown(False)

    def _clicked(self, index: QModelIndex) -> None:
        if not index.isValid():
            return
        if index.column() == 0:
            record_id = index.data(ROLE_RECORD_ID)
            locked = bool(index.data(ROLE_LOCKED))
            if record_id is not None:
                self.lock_requested.emit(int(record_id), not locked)
            return

        delegate = self.itemDelegate(index)
        if not isinstance(delegate, TableDelegate):
            return
        spec = delegate.spec_for(index)
        if spec is None:
            return
        if spec.kind == "choice" and bool(index.flags() & Qt.ItemIsEditable):
            self.edit(index)
            QTimer.singleShot(0, self._show_current_combo)

    @staticmethod
    def _show_current_combo() -> None:
        widget = QApplication.focusWidget()
        if isinstance(widget, QComboBox):
            widget.showPopup()

    def _double_clicked(self, index: QModelIndex) -> None:
        if not index.isValid() or index.column() < 2:
            return
        delegate = self.itemDelegate(index)
        if not isinstance(delegate, TableDelegate):
            return
        spec = delegate.spec_for(index)
        if spec is None:
            return

        locked = bool(index.data(ROLE_LOCKED))
        if locked:
            if spec.primary_text:
                self.locked_primary_copy_requested.emit(str(index.data(Qt.DisplayRole) or ""))
            return

        if spec.kind in {"text", "age"} and bool(index.flags() & Qt.ItemIsEditable):
            self.edit(index)
        elif spec.kind == "tags":
            record_id = index.data(ROLE_RECORD_ID)
            if record_id is not None:
                self.tags_requested.emit(int(record_id))
        elif spec.kind == "note":
            record_id = index.data(ROLE_RECORD_ID)
            if record_id is not None:
                self.note_requested.emit(int(record_id))

    def _edit_next_text_cell(self, previous: QModelIndex) -> None:
        row = previous.row() + 1
        column = previous.column()
        model = self.model()
        if model is None or row >= model.rowCount():
            return
        target = model.index(row, column)
        delegate = self.itemDelegate(target)
        if not isinstance(delegate, TableDelegate):
            return
        spec = delegate.spec_for(target)
        if spec is None or spec.kind not in {"text", "age"}:
            return
        self.selectRow(row)
        if bool(target.flags() & Qt.ItemIsEditable):
            QTimer.singleShot(0, lambda idx=target: self.edit(idx))

    def start_text_edit(self, index: QModelIndex) -> None:
        if index.isValid() and bool(index.flags() & Qt.ItemIsEditable):
            self.selectRow(index.row())
            self.scrollTo(index)
            QTimer.singleShot(0, lambda idx=index: self.edit(idx))

    def mousePressEvent(self, event) -> None:
        if not self.indexAt(event.position().toPoint()).isValid():
            self.clearSelection()
            self.setCurrentIndex(QModelIndex())
        super().mousePressEvent(event)

    def set_row_height_level(self, level: int) -> None:
        heights = {1: 24, 2: 28, 3: 32, 4: 38, 5: 46}
        self.verticalHeader().setDefaultSectionSize(heights[max(1, min(5, int(level)))])
