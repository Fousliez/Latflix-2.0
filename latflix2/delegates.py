from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QEvent, QModelIndex, QPersistentModelIndex, Qt, Signal, QStringListModel
from PySide6.QtGui import QKeyEvent, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemDelegate,
    QComboBox,
    QCompleter,
    QLineEdit,
    QStyle,
    QStyleOptionViewItem,
    QStyledItemDelegate,
)

from .model import GirlTableModel
from .schema import ColumnSpec


class TableDelegate(QStyledItemDelegate):
    request_next_text_cell = Signal(QModelIndex)

    def __init__(
        self,
        *,
        options_provider: Callable[[ColumnSpec], list[str]],
        suggestions_provider: Callable[[str], list[str]],
        parent=None,
    ):
        super().__init__(parent)
        self.options_provider = options_provider
        self.suggestions_provider = suggestions_provider
        self._editor_indexes: dict[int, QPersistentModelIndex] = {}

    @staticmethod
    def _source_index(index: QModelIndex) -> QModelIndex:
        model = index.model()
        mapper = getattr(model, "mapToSource", None)
        return mapper(index) if callable(mapper) else index

    def _source_model(self, index: QModelIndex) -> GirlTableModel | None:
        source = self._source_index(index)
        model = source.model()
        return model if isinstance(model, GirlTableModel) else None

    def spec_for(self, index: QModelIndex) -> ColumnSpec | None:
        source = self._source_index(index)
        model = self._source_model(index)
        return None if model is None else model.column_spec(source.column())

    def createEditor(self, parent, option, index):
        spec = self.spec_for(index)
        if spec is None or spec.read_only:
            return None

        if spec.kind == "choice":
            editor = QComboBox(parent)
            editor.addItems(self.options_provider(spec))
            editor.activated.connect(lambda _value, e=editor: self._finish_combo(e))
        elif spec.kind in {"text", "age"}:
            editor = QLineEdit(parent)
            if spec.key == "name":
                string_model = QStringListModel(self.suggestions_provider(""), editor)
                completer = QCompleter(string_model, editor)
                completer.setCaseSensitivity(Qt.CaseInsensitive)
                completer.setFilterMode(Qt.MatchContains)
                completer.popup().setStyleSheet(
                    "QListView { font-size: 15px; } "
                    "QListView::item { min-height: 30px; padding: 2px 5px; } "
                    "QListView::item:hover, QListView::item:selected { background: #2f78bd; color: white; }"
                )
                editor.setCompleter(completer)

                def refresh(text: str, model=string_model):
                    model.setStringList(self.suggestions_provider(text))

                editor.textEdited.connect(refresh)
        else:
            return None

        self._editor_indexes[id(editor)] = QPersistentModelIndex(index)
        editor.destroyed.connect(lambda _obj=None, key=id(editor): self._editor_indexes.pop(key, None))
        editor.installEventFilter(self)
        return editor

    def setEditorData(self, editor, index):
        value = str(index.data(Qt.EditRole) or "")
        if isinstance(editor, QLineEdit):
            editor.setText(value)
            editor.setCursorPosition(len(value))
        elif isinstance(editor, QComboBox):
            pos = editor.findText(value)
            editor.setCurrentIndex(pos if pos >= 0 else -1)

    def setModelData(self, editor, model, index):
        if isinstance(editor, QLineEdit):
            model.setData(index, editor.text(), Qt.EditRole)
        elif isinstance(editor, QComboBox):
            model.setData(index, editor.currentText(), Qt.EditRole)

    def _finish_combo(self, editor: QComboBox) -> None:
        self.commitData.emit(editor)
        self.closeEditor.emit(editor, QAbstractItemDelegate.NoHint)

    def eventFilter(self, editor, event):
        if isinstance(event, QKeyEvent):
            if event.key() == Qt.Key_Escape:
                event.accept()
                return True
            if isinstance(editor, QLineEdit) and event.key() in (Qt.Key_Return, Qt.Key_Enter):
                stored = self._editor_indexes.get(id(editor))
                index = QModelIndex(stored) if stored is not None and stored.isValid() else QModelIndex()
                self.commitData.emit(editor)
                self.closeEditor.emit(editor, QStyledItemDelegate.NoHint)
                if index.isValid():
                    self.request_next_text_cell.emit(index)
                event.accept()
                return True
        return super().eventFilter(editor, event)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        selected = bool(option.state & QStyle.State_Selected)
        clean = QStyleOptionViewItem(option)
        clean.state &= ~QStyle.State_Selected
        super().paint(painter, clean, index)

        if selected and index.column() != 0:
            painter.save()
            painter.setPen(QPen(Qt.GlobalColor.darkCyan, 1))
            rect = option.rect.adjusted(0, 0, -1, -1)
            painter.drawLine(rect.topLeft(), rect.topRight())
            painter.drawLine(rect.bottomLeft(), rect.bottomRight())
            if index.column() == 1:
                painter.drawLine(rect.topLeft(), rect.bottomLeft())
            if index.column() == index.model().columnCount() - 1:
                painter.drawLine(rect.topRight(), rect.bottomRight())
            painter.restore()
