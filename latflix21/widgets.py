from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QEvent, QModelIndex, QTimer, Qt, Signal, QStringListModel
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QCompleter, QDialog, QDialogButtonBox, QHBoxLayout,
    QLineEdit, QMenu, QPushButton, QStyledItemDelegate, QTableView, QTextEdit,
    QVBoxLayout, QWidget,
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

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setSectionsMovable(True)
        self.horizontalHeader().setSortIndicatorShown(False)
        self.setWordWrap(False)
        self.setStyleSheet(
            "QTableView{alternate-background-color:#f3f3f3;background:white;"
            "gridline-color:#d9d9d9;outline:0;}"
            "QTableView::item:selected{background:#b8d7f5;color:#111;outline:0;}"
            "QHeaderView::section{background:#f5f5f5;border:0;"
            "border-right:1px solid #d6d6d6;border-bottom:1px solid #c8c8c8;padding:4px;}"
        )
        self.clicked.connect(self._single_click)
        self.doubleClicked.connect(self._double_click)

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
        if col and col.kind == "note" and (model.flags(source) & Qt.ItemIsEditable):
            self.noteRequested.emit(index)


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
