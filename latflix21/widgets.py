from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QEvent, QModelIndex, QPoint, QSettings, QTimer, Qt, Signal, QStringListModel
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QCompleter, QDialog, QDialogButtonBox, QHBoxLayout,
    QInputDialog, QLineEdit, QMenu, QMessageBox, QPushButton, QStyledItemDelegate,
    QTableView, QTextEdit, QToolTip, QVBoxLayout, QWidget, QHeaderView,
)

from .models import SmartProxy


class TextDelegate(QStyledItemDelegate):
    def __init__(self, view, parent=None):
        super().__init__(parent or view)
        self.view = view

    def createEditor(self, parent, option, index):
        edit = QLineEdit(parent)
        edit.setProperty("row", index.row())
        edit.setProperty("col", index.column())
        edit.installEventFilter(self)
        return edit

    def setEditorData(self, editor, index):
        editor.setText(str(index.data(Qt.EditRole) or ""))
        editor.selectAll()

    def setModelData(self, editor, model, index):
        model.setData(index, editor.text(), Qt.EditRole)

    def eventFilter(self, editor, event):
        if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter):
            row = int(editor.property("row"))
            col = int(editor.property("col"))
            self.commitData.emit(editor)
            self.closeEditor.emit(editor)

            def move():
                model = self.view.model()
                next_row = row + 1
                if next_row < model.rowCount():
                    idx = model.index(next_row, col)
                    self.view.setCurrentIndex(idx)
                    self.view.edit(idx)

            QTimer.singleShot(0, move)
            return True
        return super().eventFilter(editor, event)


class ChoiceDelegate(QStyledItemDelegate):
    def __init__(self, choices: Callable[[QModelIndex], list[str]], parent=None):
        super().__init__(parent)
        self.choices = choices

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.setEditable(False)
        combo.setFrame(False)
        combo.setStyleSheet(
            "QComboBox::drop-down{width:0;border:0;}"
            "QComboBox::down-arrow{width:0;height:0;image:none;}"
        )
        combo.addItems(self.choices(index))
        combo.activated.connect(
            lambda *_: (self.commitData.emit(combo), self.closeEditor.emit(combo))
        )
        QTimer.singleShot(0, combo.showPopup)
        return combo

    def setEditorData(self, editor, index):
        text = str(index.data(Qt.EditRole) or "")
        found = editor.findText(text)
        editor.setCurrentIndex(found if found >= 0 else 0)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)


class AutoCompleteDelegate(QStyledItemDelegate):
    def __init__(self, suggestions: Callable[[str], list[str]], parent=None):
        super().__init__(parent)
        self.suggestions = suggestions

    def createEditor(self, parent, option, index):
        edit = QLineEdit(parent)
        completer = QCompleter(edit)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        model = QStringListModel(self.suggestions(""), completer)
        completer.setModel(model)
        edit.setCompleter(completer)
        edit.textEdited.connect(lambda text: model.setStringList(self.suggestions(text)))
        return edit

    def setEditorData(self, editor, index):
        editor.setText(str(index.data(Qt.EditRole) or ""))
        editor.selectAll()

    def setModelData(self, editor, model, index):
        model.setData(index, editor.text().strip(), Qt.EditRole)


class NoteDialog(QDialog):
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Poznámka")
        self.resize(640, 360)
        layout = QVBoxLayout(self)
        self.editor = QTextEdit(self)
        self.editor.setPlainText(text)
        layout.addWidget(self.editor)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def text(self):
        return self.editor.toPlainText()


class DataTableView(QTableView):
    noteRequested = Signal(QModelIndex)
    webRequested = Signal(QModelIndex)
    tagRequested = Signal(QModelIndex)
    headerLayoutChanged = Signal()

    def __init__(self, section_name: str = "", parent=None):
        super().__init__(parent)
        self.section_name = section_name or "table"
        self.header_locked = True
        self._settings = QSettings("Latflix", "Latflix 2.1")
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setSortIndicatorShown(False)
        self.setWordWrap(False)
        self.setMouseTracking(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)
        self.horizontalHeader().sectionClicked.connect(self._header_clicked)
        self.horizontalHeader().sectionMoved.connect(lambda *_: self._save_layout())
        self.horizontalHeader().sectionResized.connect(lambda *_: self._save_layout())
        self.setStyleSheet(
            "QTableView{alternate-background-color:#f3f3f3;background:white;"
            "gridline-color:#d9d9d9;outline:0;}"
            "QTableView::item:selected{background:transparent;color:#111;outline:0;}"
            "QHeaderView::section{background:#f5f5f5;border:0;"
            "border-right:1px solid #d6d6d6;border-bottom:1px solid #c8c8c8;padding:4px;}"
        )
        self.clicked.connect(self._single_click)
        self.doubleClicked.connect(self._double_click)
        self.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.horizontalHeader().customContextMenuRequested.connect(self.headerContextMenu)
        self._apply_header_lock()

    def setModel(self, model):
        super().setModel(model)
        QTimer.singleShot(0, self.restore_layout)

    def _settings_prefix(self):
        return f"tables/{self.section_name}"

    def _apply_header_lock(self):
        header = self.horizontalHeader()
        header.setSectionsMovable(not self.header_locked)
        header.setSectionResizeMode(
            QHeaderView.Fixed if self.header_locked else QHeaderView.Interactive
        )

    def _header_clicked(self, section):
        if section == 0:
            self.header_locked = not self.header_locked
            self._apply_header_lock()
            return

    def _context_menu(self, pos):
        index = self.indexAt(pos)
        if not index.isValid():
            return
        # Context menu for data cells is intentionally empty for now.
        # Header menu is handled by headerContextMenu().
        return

    def headerContextMenu(self, pos: QPoint):
        if self.header_locked:
            return
        header = self.horizontalHeader()
        logical = header.logicalIndexAt(pos)
        if logical < 2:
            return
        menu = QMenu(self)
        rename = menu.addAction("Přejmenovat sloupec")
        hide = menu.addAction("Skrýt sloupec")
        action = menu.exec(header.mapToGlobal(pos))
        if action == rename:
            model = self.model()
            source_model = model.sourceModel() if isinstance(model, SmartProxy) else model
            current = str(source_model.headerData(logical, Qt.Horizontal, Qt.DisplayRole) or "")
            text, ok = QInputDialog.getText(self, "Přejmenovat sloupec", "Název:", text=current)
            if ok and text.strip():
                key = source_model.col(logical).key
                self._settings.setValue(f"{self._settings_prefix()}/title/{key}", text.strip())
                if hasattr(source_model, "title_overrides"):
                    source_model.title_overrides[key] = text.strip()
                    source_model.headerDataChanged.emit(Qt.Horizontal, logical, logical)
        elif action == hide:
            self.setColumnHidden(logical, True)
            self._save_layout()

    def restore_hidden_columns_menu(self, parent_menu):
        model = self.model()
        source_model = model.sourceModel() if isinstance(model, SmartProxy) else model
        submenu = parent_menu.addMenu(f"Sloupce – {self.section_name}")
        for logical in range(2, source_model.columnCount()):
            title = str(source_model.headerData(logical, Qt.Horizontal, Qt.DisplayRole) or "")
            action = submenu.addAction(title)
            action.setCheckable(True)
            action.setChecked(not self.isColumnHidden(logical))
            action.toggled.connect(
                lambda visible, col=logical: (
                    self.setColumnHidden(col, not visible),
                    self._save_layout(),
                )
            )

    def _save_layout(self):
        if self.model() is None:
            return
        header = self.horizontalHeader()
        prefix = self._settings_prefix()
        self._settings.setValue(f"{prefix}/state", header.saveState())
        hidden = [
            str(i)
            for i in range(self.model().columnCount())
            if self.isColumnHidden(i)
        ]
        self._settings.setValue(f"{prefix}/hidden", ",".join(hidden))
        self.headerLayoutChanged.emit()

    def restore_layout(self):
        if self.model() is None:
            return
        prefix = self._settings_prefix()
        state = self._settings.value(f"{prefix}/state")
        if state:
            self.horizontalHeader().restoreState(state)
        hidden_raw = str(self._settings.value(f"{prefix}/hidden", "") or "")
        hidden = {int(x) for x in hidden_raw.split(",") if x.isdigit()}
        for column in range(self.model().columnCount()):
            self.setColumnHidden(column, column in hidden)
        source_model = self.model().sourceModel() if isinstance(self.model(), SmartProxy) else self.model()
        if hasattr(source_model, "title_overrides"):
            for logical in range(2, source_model.columnCount()):
                key = source_model.col(logical).key
                title = self._settings.value(f"{prefix}/title/{key}")
                if title:
                    source_model.title_overrides[key] = str(title)
        source_model.headerDataChanged.emit(Qt.Horizontal, 0, source_model.columnCount() - 1)
        self._apply_header_lock()

    def mousePressEvent(self, event):
        if not self.indexAt(event.position().toPoint()).isValid():
            self.clearSelection()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.selectionModel() or not self.model():
            return
        rows = sorted({index.row() for index in self.selectionModel().selectedRows()})
        if not rows:
            return
        groups = []
        start = previous = rows[0]
        for row in rows[1:]:
            if row == previous + 1:
                previous = row
                continue
            groups.append((start, previous))
            start = previous = row
        groups.append((start, previous))

        visible_columns = [
            c for c in range(1, self.model().columnCount())
            if not self.isColumnHidden(c)
        ]
        if not visible_columns:
            return
        left_col = visible_columns[0]
        right_col = visible_columns[-1]
        painter = QPainter(self.viewport())
        pen = QPen(QColor("#4f80b4"))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        for first_row, last_row in groups:
            left_top = self.visualRect(self.model().index(first_row, left_col))
            right_bottom = self.visualRect(self.model().index(last_row, right_col))
            if not left_top.isValid() or not right_bottom.isValid():
                continue
            rect = left_top.united(right_bottom).adjusted(1, 1, -1, -1)
            painter.drawRect(rect)
        painter.end()

    def source_col(self, index):
        model = self.model()
        source = index
        if isinstance(model, SmartProxy):
            source = model.mapToSource(index)
            model = model.sourceModel()
        return model, source, model.col(source.column()) if source.isValid() else None

    def _single_click(self, index):
        model, source, col = self.source_col(index)
        if not col:
            return
        if col.kind == "button":
            self.webRequested.emit(index)
            return
        if col.kind == "tags":
            self.tagRequested.emit(index)
            return
        if col.kind == "lock":
            model.setData(source, "", Qt.EditRole)
            return
        if (model.flags(source) & Qt.ItemIsEditable) and col.kind not in {
            "row", "computed"
        }:
            self.edit(index)

    def _double_click(self, index):
        model, source, col = self.source_col(index)
        if not col:
            return
        if col.kind == "note" and (model.flags(source) & Qt.ItemIsEditable):
            self.noteRequested.emit(index)
            return
        if getattr(col, "primary", False) and model.locked(source.row()):
            text = str(model.data(source, Qt.DisplayRole) or "")
            if text:
                QApplication.clipboard().setText(text)
                QToolTip.showText(self.viewport().mapToGlobal(self.visualRect(index).center()), "Zkopírováno", self)


class SplitAddButton(QWidget):
    addRequested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.main = QPushButton("Přidat", self)
        self.arrow = QPushButton("▾", self)
        self.arrow.setFixedWidth(28)
        layout.addWidget(self.main)
        layout.addWidget(self.arrow)
        self.main.clicked.connect(lambda: self.addRequested.emit(1))
        menu = QMenu(self)
        add5 = menu.addAction("Přidat 5 řádků")
        add10 = menu.addAction("Přidat 10 řádků")
        add5.triggered.connect(lambda: self.addRequested.emit(5))
        add10.triggered.connect(lambda: self.addRequested.emit(10))
        self.arrow.clicked.connect(
            lambda: menu.exec(self.arrow.mapToGlobal(self.arrow.rect().bottomLeft()))
        )


class SearchBox(QWidget):
    textChanged = Signal(str)
    cleared = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.edit = QLineEdit(self)
        self.edit.setPlaceholderText("Hledání")
        self.edit.setFixedWidth(260)
        self.clear_btn = QPushButton("🗑", self)
        self.clear_btn.setFixedWidth(30)
        layout.addWidget(self.edit)
        layout.addWidget(self.clear_btn)
        self.edit.textChanged.connect(self.textChanged)
        self.clear_btn.clicked.connect(self.clear)

    def clear(self):
        self.edit.clear()
        self.cleared.emit()


class ChipButton(QPushButton):
    def __init__(self, text: str, value: str, parent=None):
        super().__init__(text, parent)
        self.value = value
        self.setCheckable(True)
        self.setStyleSheet(
            "QPushButton{border:1px solid #9dbce3;background:#f5f9ff;"
            "color:#154d8c;padding:3px 8px;border-radius:2px;}"
            "QPushButton:checked{background:#2f77c8;color:white;border-color:#1f5eaa;}"
        )


class FlowWidget(QWidget):
    def __init__(self, parent=None, max_rows=3, row_height=29):
        super().__init__(parent)
        self.max_rows = max_rows
        self.row_height = row_height
        self.items = []
        self.setMinimumHeight(row_height)
        self.setMaximumHeight(row_height * max_rows)

    def set_items(self, widgets: list[QWidget]):
        for widget in self.items:
            widget.setParent(None)
            widget.deleteLater()
        self.items = widgets
        for widget in widgets:
            widget.setParent(self)
            widget.show()
        self.reflow()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.reflow()

    def reflow(self):
        x = 0
        y = 0
        gap = 6
        rows = 1
        width = max(10, self.width())
        for widget in self.items:
            widget.adjustSize()
            size = widget.sizeHint()
            if x and x + size.width() > width:
                rows += 1
                x = 0
                y += self.row_height
            if rows > self.max_rows:
                widget.hide()
                continue
            widget.show()
            widget.setGeometry(x, y, size.width(), min(size.height(), self.row_height - 3))
            x += size.width() + gap


def open_note_for_table(table: DataTableView, index: QModelIndex):
    proxy = table.model()
    source = index
    model = proxy
    if isinstance(proxy, SmartProxy):
        source = proxy.mapToSource(index)
        model = proxy.sourceModel()
    dialog = NoteDialog(str(source.data(Qt.EditRole) or ""), table)
    if dialog.exec() == QDialog.Accepted:
        model.setData(source, dialog.text(), Qt.EditRole)


def selected_source_ids(table: QTableView) -> list[int]:
    proxy = table.model()
    result = []
    for index in table.selectionModel().selectedRows():
        source = proxy.mapToSource(index) if isinstance(proxy, SmartProxy) else index
        model = proxy.sourceModel() if isinstance(proxy, SmartProxy) else proxy
        result.append(model.record_id(source.row()))
    return list(dict.fromkeys(result))
