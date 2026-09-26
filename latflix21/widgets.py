from __future__ import annotations

from collections.abc import Callable
from math import ceil

from PySide6.QtCore import (
    QEvent, QModelIndex, QPoint, QPersistentModelIndex, QRect, QTimer, Qt, Signal,
    QStringListModel,
)
from PySide6.QtGui import (
    QColor, QGuiApplication, QKeyEvent, QMouseEvent, QPainter, QPen, QPixmap,
)
from PySide6.QtWidgets import (
    QApplication, QAbstractItemDelegate, QAbstractItemView, QComboBox, QCompleter,
    QDialog, QDialogButtonBox, QGridLayout, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMenu, QPushButton, QRubberBand,
    QSizePolicy, QStyledItemDelegate, QTableView, QTextEdit, QToolTip, QVBoxLayout,
    QWidget,
)

from .models import ROLE_LOCKED, ROLE_RECORD_ID, BaseModel, SmartProxy


BUTTON_H = 30


class LockedHeader(QHeaderView):
    lockClicked = Signal()
    layoutTouched = Signal()

    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)
        self.locked = True
        self.setSortIndicatorShown(False)
        self.setSectionsMovable(False)
        self.setSectionResizeMode(QHeaderView.Fixed)
        self.sectionClicked.connect(self._clicked)
        self.sectionMoved.connect(lambda *_: self.layoutTouched.emit())
        self.sectionResized.connect(lambda *_: self.layoutTouched.emit())

    def _clicked(self, logical: int) -> None:
        if logical == 0:
            self.lockClicked.emit()

    def set_locked(self, locked: bool) -> None:
        self.locked = bool(locked)
        self.setSectionsMovable(not self.locked)
        self.setSectionResizeMode(QHeaderView.Fixed if self.locked else QHeaderView.Interactive)
        self.viewport().update()

    def paintSection(self, painter, rect, logicalIndex):
        super().paintSection(painter, rect, logicalIndex)
        if logicalIndex == 0:
            painter.save()
            painter.setPen(QColor("#222"))
            font = painter.font()
            font.setPointSize(max(font.pointSize() + 4, 14))
            painter.setFont(font)
            painter.drawText(rect, int(Qt.AlignCenter), "🔒" if self.locked else "🔓")
            painter.restore()


class _TextDelegateBase(QStyledItemDelegate):
    def __init__(self, view: "DataTableView", parent=None):
        super().__init__(parent or view)
        self.view = view
        self._indexes: dict[int, QPersistentModelIndex] = {}

    def _remember(self, editor, index):
        self._indexes[id(editor)] = QPersistentModelIndex(index)
        editor.destroyed.connect(
            lambda _obj=None, key=id(editor): self._indexes.pop(key, None)
        )
        editor.installEventFilter(self)

    def _index(self, editor) -> QModelIndex:
        persistent = self._indexes.get(id(editor))
        if persistent is None or not persistent.isValid():
            return QModelIndex()
        return QModelIndex(persistent)

    def _finish_and_next(self, editor) -> None:
        index = self._index(editor)
        self.commitData.emit(editor)
        self.closeEditor.emit(editor, QAbstractItemDelegate.NoHint)
        if index.isValid():
            QTimer.singleShot(0, lambda idx=index: self.view.edit_next_text_cell(idx))

    def eventFilter(self, editor, event):
        if event.type() == QEvent.KeyPress and isinstance(event, QKeyEvent):
            if event.key() == Qt.Key_Escape:
                # Esc has no special table action.
                event.accept()
                return True
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                self._finish_and_next(editor)
                event.accept()
                return True
        return super().eventFilter(editor, event)


class TextDelegate(_TextDelegateBase):
    def createEditor(self, parent, option, index):
        edit = QLineEdit(parent)
        self._remember(edit, index)
        return edit

    def setEditorData(self, editor, index):
        editor.setText(str(index.data(Qt.EditRole) or ""))
        editor.setCursorPosition(len(editor.text()))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.text(), Qt.EditRole)


class NoteLineEdit(QLineEdit):
    doubleActivated = Signal()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.doubleActivated.emit()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)


class NoteDelegate(_TextDelegateBase):
    def createEditor(self, parent, option, index):
        edit = NoteLineEdit(parent)
        self._remember(edit, index)

        def open_large():
            idx = self._index(edit)
            if not idx.isValid():
                return
            self.commitData.emit(edit)
            self.closeEditor.emit(edit, QAbstractItemDelegate.NoHint)
            QTimer.singleShot(0, lambda target=idx: self.view.noteRequested.emit(target))

        edit.doubleActivated.connect(open_large)
        return edit

    def setEditorData(self, editor, index):
        editor.setText(str(index.data(Qt.EditRole) or ""))
        editor.setCursorPosition(len(editor.text()))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.text(), Qt.EditRole)


class HandoffComboBox(QComboBox):
    def __init__(self, table: "DataTableView", index: QModelIndex, parent=None):
        super().__init__(parent)
        self.table = table
        self.source_index = QPersistentModelIndex(index)
        self._filter_installed = False
        self.setFrame(False)
        self.setStyleSheet(
            "QComboBox{background:transparent;border:0;padding:0 3px;}"
            "QComboBox::drop-down{width:0;border:0;}"
            "QComboBox::down-arrow{width:0;height:0;image:none;}"
        )

    def showPopup(self):
        if not self._filter_installed:
            QApplication.instance().installEventFilter(self)
            self._filter_installed = True
        super().showPopup()

    def hidePopup(self):
        super().hidePopup()
        if self._filter_installed:
            QApplication.instance().removeEventFilter(self)
            self._filter_installed = False

    def eventFilter(self, watched, event):
        if (
            self.view().isVisible()
            and event.type() == QEvent.MouseButtonPress
            and isinstance(event, QMouseEvent)
        ):
            obj = watched
            if isinstance(obj, QWidget) and (obj is self.view() or self.view().isAncestorOf(obj)):
                return False
            gp = event.globalPosition().toPoint()
            viewport = self.table.viewport()
            local = viewport.mapFromGlobal(gp)
            if viewport.rect().contains(local):
                target = self.table.indexAt(local)
                if target.isValid():
                    self.hidePopup()
                    QTimer.singleShot(0, lambda idx=target: self.table.activate_index(idx))
                    return True
        return super().eventFilter(watched, event)


class ChoiceDelegate(QStyledItemDelegate):
    def __init__(
        self,
        view: "DataTableView",
        choices: Callable[[QModelIndex], list[str]],
        parent=None,
    ):
        super().__init__(parent or view)
        self.view = view
        self.choices = choices

    def createEditor(self, parent, option, index):
        combo = HandoffComboBox(self.view, index, parent)
        combo.addItems(self.choices(index))
        combo.activated.connect(
            lambda *_: (
                self.commitData.emit(combo),
                self.closeEditor.emit(combo, QAbstractItemDelegate.NoHint),
            )
        )
        QTimer.singleShot(0, combo.showPopup)
        return combo

    def setEditorData(self, editor, index):
        value = str(index.data(Qt.EditRole) or "")
        found = editor.findText(value)
        editor.setCurrentIndex(found if found >= 0 else -1)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)

    def eventFilter(self, editor, event):
        if event.type() == QEvent.KeyPress and isinstance(event, QKeyEvent):
            if event.key() == Qt.Key_Escape:
                event.accept()
                return True
        return super().eventFilter(editor, event)


class AutoCompleteDelegate(_TextDelegateBase):
    def __init__(
        self,
        view: "DataTableView",
        suggestions: Callable[[str], list[str]],
        parent=None,
    ):
        super().__init__(view, parent)
        self.suggestions = suggestions

    def createEditor(self, parent, option, index):
        edit = QLineEdit(parent)
        self._remember(edit, index)

        string_model = QStringListModel(self.suggestions(""), edit)
        completer = QCompleter(string_model, edit)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.popup().setStyleSheet(
            "QListView{font-size:15px;min-width:230px;}"
            "QListView::item{min-height:30px;padding:2px 6px;}"
            "QListView::item:hover,QListView::item:selected{background:#2f78bd;color:white;}"
        )
        edit.setCompleter(completer)
        edit.textEdited.connect(
            lambda text, model=string_model: model.setStringList(self.suggestions(text))
        )

        def chosen(text):
            edit.setText(text)
            self._finish_and_next(edit)

        completer.activated[str].connect(chosen)
        return edit

    def setEditorData(self, editor, index):
        editor.setText(str(index.data(Qt.EditRole) or ""))
        editor.setCursorPosition(len(editor.text()))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.text().strip(), Qt.EditRole)

    def eventFilter(self, editor, event):
        if (
            event.type() == QEvent.KeyPress
            and isinstance(event, QKeyEvent)
            and event.key() in (Qt.Key_Return, Qt.Key_Enter)
            and editor.completer()
            and editor.completer().popup().isVisible()
            and editor.completer().popup().currentIndex().isValid()
        ):
            return False
        return super().eventFilter(editor, event)


class NoteDialog(QDialog):
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Poznámka")
        self.resize(680, 390)
        layout = QVBoxLayout(self)
        self.editor = QTextEdit(self)
        self.editor.setPlainText(text)
        layout.addWidget(self.editor)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, self)
        buttons.button(QDialogButtonBox.Save).setText("Uložit")
        buttons.button(QDialogButtonBox.Cancel).setText("Zrušit")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def text(self):
        return self.editor.toPlainText()


class DataTableView(QTableView):
    noteRequested = Signal(QModelIndex)
    webRequested = Signal(QModelIndex)
    imageRequested = Signal(QModelIndex)
    tagRequested = Signal(QModelIndex)
    headerLockChanged = Signal(bool)
    headerLayoutChanged = Signal()
    headerContextRequested = Signal(int, QPoint)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.header = LockedHeader(self)
        self.setHorizontalHeader(self.header)
        self.header.lockClicked.connect(self.toggle_header_lock)
        self.header.layoutTouched.connect(self._header_layout_touched)
        self.header.setContextMenuPolicy(Qt.CustomContextMenu)
        self.header.customContextMenuRequested.connect(self._header_context)
        self.header_locked = True
        self._moving_back = False

        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.verticalHeader().setVisible(False)
        self.setWordWrap(False)
        self.setStyleSheet(
            "QTableView{background:white;alternate-background-color:#f3f3f3;"
            "gridline-color:#d8d8d8;border:1px solid #aaa;outline:0;"
            "selection-background-color:transparent;selection-color:#202020;}"
            "QTableView::item:selected{background:transparent;color:#202020;}"
            "QTableView::item:focus{border:0;outline:0;}"
            "QHeaderView::section{background:#ececec;border:0;border-right:1px solid #c8c8c8;"
            "border-bottom:1px solid #aaa;padding:4px 5px;}"
        )

        self.clicked.connect(self._single_click)
        self.doubleClicked.connect(self._double_click)

    def setModel(self, model):
        super().setModel(model)
        if self.selectionModel():
            self.selectionModel().selectionChanged.connect(lambda *_: self.viewport().update())

    def toggle_header_lock(self):
        self.set_header_locked(not self.header_locked)

    def set_header_locked(self, locked: bool):
        self.header_locked = bool(locked)
        self.header.set_locked(self.header_locked)
        self.headerLockChanged.emit(self.header_locked)

    def _header_layout_touched(self):
        if self._moving_back:
            return
        # First two system columns are permanent.
        if self.header.visualIndex(0) != 0 or self.header.visualIndex(1) != 1:
            self._moving_back = True
            if self.header.visualIndex(0) != 0:
                self.header.moveSection(self.header.visualIndex(0), 0)
            if self.header.visualIndex(1) != 1:
                self.header.moveSection(self.header.visualIndex(1), 1)
            self._moving_back = False
        self.setColumnWidth(0, 36)
        self.setColumnWidth(1, 44)
        self.headerLayoutChanged.emit()

    def _header_context(self, pos: QPoint):
        logical = self.header.logicalIndexAt(pos)
        if logical >= 2:
            self.headerContextRequested.emit(logical, self.header.mapToGlobal(pos))

    def source_parts(self, index):
        model = self.model()
        source = index
        if isinstance(model, SmartProxy):
            source = model.mapToSource(index)
            model = model.sourceModel()
        return model, source, model.col(source.column()) if source.isValid() else None

    def activate_index(self, index):
        if not index.isValid():
            return
        model, source, col = self.source_parts(index)
        if col is None:
            return
        self.setCurrentIndex(index)
        if col.kind == "lock":
            model.setData(source, "", Qt.EditRole)
            self.viewport().update()
            return
        if col.kind == "button":
            self.webRequested.emit(index)
            return
        if col.kind == "image_button":
            self.imageRequested.emit(index)
            return
        if col.kind == "tags":
            if model.flags(source) & Qt.ItemIsEditable:
                self.tagRequested.emit(index)
            return
        if model.flags(source) & Qt.ItemIsEditable:
            self.edit(index)

    def _single_click(self, index):
        self.activate_index(index)

    def _double_click(self, index):
        if not index.isValid():
            return
        model, source, col = self.source_parts(index)
        if col is None:
            return
        locked = bool(source.data(ROLE_LOCKED))
        if locked and col.primary_text:
            text = str(source.data(Qt.DisplayRole) or "")
            QApplication.clipboard().setText(text)
            QToolTip.showText(QGuiApplication.cursor().pos(), "Zkopírováno", self)
            return
        if col.kind == "note" and not locked:
            # Normally handled by NoteLineEdit; this covers cases where no editor got focus.
            self.noteRequested.emit(index)

    def edit_next_text_cell(self, previous: QModelIndex) -> None:
        next_row = previous.row() + 1
        if next_row >= self.model().rowCount():
            return
        target = self.model().index(next_row, previous.column())
        model, source, col = self.source_parts(target)
        if col is None or col.kind not in {"text", "note", "autocomplete"}:
            return
        if not (model.flags(source) & Qt.ItemIsEditable):
            return
        self.selectRow(next_row)
        self.setCurrentIndex(target)
        self.scrollTo(target)
        QTimer.singleShot(0, lambda idx=target: self.edit(idx))

    def start_edit_for_record(self, record_id: int, preferred_column: int = 2):
        model = self.model()
        source_model = model.sourceModel() if isinstance(model, SmartProxy) else model
        for row, record in enumerate(source_model.rows):
            if int(record.id) == int(record_id):
                source = source_model.index(row, preferred_column)
                target = model.mapFromSource(source) if isinstance(model, SmartProxy) else source
                if target.isValid():
                    self.selectRow(target.row())
                    self.scrollTo(target)
                    QTimer.singleShot(0, lambda idx=target: self.edit(idx))
                return

    def mousePressEvent(self, event):
        if not self.indexAt(event.position().toPoint()).isValid():
            self.clearSelection()
            self.setCurrentIndex(QModelIndex())
        super().mousePressEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        selection = self.selectionModel()
        model = self.model()
        if selection is None or model is None:
            return
        rows = sorted({idx.row() for idx in selection.selectedRows()})
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
            column
            for column in range(1, model.columnCount())
            if not self.isColumnHidden(column)
        ]
        if not visible_columns:
            return
        left_col = min(visible_columns, key=lambda c: self.horizontalHeader().visualIndex(c))
        right_col = max(visible_columns, key=lambda c: self.horizontalHeader().visualIndex(c))

        painter = QPainter(self.viewport())
        painter.setPen(QPen(QColor("#1674a5"), 1))
        for first, last in groups:
            top = self.visualRect(model.index(first, left_col))
            bottom = self.visualRect(model.index(last, right_col))
            if not top.isValid() or not bottom.isValid():
                continue
            rect = QRect(
                min(top.left(), bottom.left()),
                top.top(),
                max(top.right(), bottom.right()) - min(top.left(), bottom.left()),
                bottom.bottom() - top.top(),
            ).adjusted(0, 0, -1, -1)
            painter.drawRect(rect)
        painter.end()

    def set_row_height_level(self, level: int):
        heights = {1: 24, 2: 28, 3: 32, 4: 38, 5: 46}
        self.verticalHeader().setDefaultSectionSize(heights[max(1, min(5, int(level)))])


class SplitAddButton(QWidget):
    addRequested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.main = QPushButton("Přidat", self)
        self.arrow = QPushButton("▾", self)
        self.main.setFixedHeight(BUTTON_H)
        self.arrow.setFixedSize(28, BUTTON_H)
        layout.addWidget(self.main)
        layout.addWidget(self.arrow)
        self.main.clicked.connect(lambda: self.addRequested.emit(1))

        self.menu = QMenu(self)
        self.menu.addAction("Přidat 5 řádků", lambda: self.addRequested.emit(5))
        self.menu.addAction("Přidat 10 řádků", lambda: self.addRequested.emit(10))
        self.arrow.clicked.connect(
            lambda: self.menu.exec(self.arrow.mapToGlobal(self.arrow.rect().bottomLeft()))
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
        self.edit.setMinimumWidth(190)
        self.edit.setMaximumWidth(250)
        self.edit.setFixedHeight(BUTTON_H)
        self.clear_btn = QPushButton("🗑", self)
        self.clear_btn.setFixedSize(BUTTON_H, BUTTON_H)
        self.clear_btn.setToolTip("Vymazat pouze hledání")
        layout.addWidget(self.edit)
        layout.addWidget(self.clear_btn)
        self.edit.textChanged.connect(self.textChanged)
        self.clear_btn.clicked.connect(self.clear)

    def clear(self):
        self.edit.clear()
        self.cleared.emit()

    def text(self):
        return self.edit.text()


class FilterButton(QPushButton):
    valueChanged = Signal(str)

    def __init__(
        self,
        title: str,
        provider: Callable[[], list[str]],
        parent=None,
        overflow_after: int | None = None,
    ):
        super().__init__(title, parent)
        self.title = title
        self.provider = provider
        self.overflow_after = overflow_after
        self.value = ""
        self.setFixedHeight(BUTTON_H)
        self.clicked.connect(self.open_menu)

    def set_value(self, value: str, emit=True):
        self.value = value
        self.setText(f"{self.title}: {value}" if value else self.title)
        if emit:
            self.valueChanged.emit(value)

    def open_menu(self):
        values = list(self.provider())
        menu = QMenu(self)
        clear = menu.addAction(self.title)
        clear.triggered.connect(lambda: self.set_value(""))
        if values:
            menu.addSeparator()
        if self.overflow_after and len(values) > self.overflow_after:
            for value in values[: self.overflow_after]:
                menu.addAction(value, lambda checked=False, v=value: self.set_value(v))
            menu.addSeparator()
            rest = menu.addMenu("Další")
            for value in values[self.overflow_after :]:
                rest.addAction(value, lambda checked=False, v=value: self.set_value(v))
        else:
            for value in values:
                menu.addAction(value, lambda checked=False, v=value: self.set_value(v))
        menu.exec(self.mapToGlobal(self.rect().bottomLeft()))


class ScrollFilterPopup(QDialog):
    def __init__(self, title: str, values: list[str], parent=None):
        super().__init__(parent, Qt.Popup)
        self.value = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        self.list = QListWidget(self)
        self.list.addItem(title)
        self.list.addItems(values)
        self.list.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOn if len(values) > 15 else Qt.ScrollBarAsNeeded
        )
        row_height = 27
        self.list.setFixedHeight(min(16, len(values) + 1) * row_height + 5)
        self.list.setMinimumWidth(220)
        self.list.itemClicked.connect(self._chosen)
        layout.addWidget(self.list)

    def _chosen(self, item):
        self.value = "" if self.list.row(item) == 0 else item.text()
        self.accept()


class ScrollFilterButton(FilterButton):
    def open_menu(self):
        popup = ScrollFilterPopup(self.title, list(self.provider()), self)
        popup.move(self.mapToGlobal(self.rect().bottomLeft()))
        if popup.exec() == QDialog.Accepted and popup.value is not None:
            self.set_value(popup.value)


class ChipButton(QPushButton):
    def __init__(self, text: str, value: str, parent=None):
        super().__init__(text, parent)
        self.value = value
        self.setCheckable(True)
        self.setFixedHeight(24)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setStyleSheet(
            "QPushButton{border:1px solid #9dbce3;background:#edf5ff;"
            "color:#154d8c;padding:2px 8px;border-radius:3px;}"
            "QPushButton:checked{background:#2f77c8;color:white;border-color:#1f5eaa;}"
        )


class FlowWidget(QWidget):
    def __init__(self, parent=None, max_rows=3, row_height=29):
        super().__init__(parent)
        self.max_rows = max_rows
        self.row_height = row_height
        self.items: list[QWidget] = []
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
        gap = 5
        row = 1
        width = max(10, self.width())
        for widget in self.items:
            widget.adjustSize()
            size = widget.sizeHint()
            if x and x + size.width() > width:
                row += 1
                x = 0
                y += self.row_height
            if row > self.max_rows:
                widget.hide()
                continue
            widget.show()
            widget.setGeometry(x, y, size.width(), min(size.height(), self.row_height - 2))
            x += size.width() + gap


class ProfileButton(QPushButton):
    chooseRequested = Signal()
    cropRequested = Signal()
    deleteRequested = Signal()

    def __init__(self, parent=None):
        super().__init__("FOTKA", parent)
        self._single_timer = QTimer(self)
        self._single_timer.setSingleShot(True)
        self._single_timer.timeout.connect(self.chooseRequested.emit)
        self._double = False
        self.setFixedSize(70, 116)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self._single_timer.stop()
            self.deleteRequested.emit()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._double = True
            self._single_timer.stop()
            self.cropRequested.emit()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton:
            if self._double:
                self._double = False
            else:
                self._single_timer.start(QApplication.doubleClickInterval() + 20)


class ScreenCropDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setCursor(Qt.CrossCursor)
        self._rubber = QRubberBand(QRubberBand.Rectangle, self)
        self._start = QPoint()
        self.result_pixmap = QPixmap()

        geometry = QRect()
        for screen in QApplication.screens():
            geometry = geometry.united(screen.geometry())
        self._virtual_geometry = geometry
        self._screenshot = QPixmap(geometry.size())
        self._screenshot.fill(Qt.black)

        painter = QPainter(self._screenshot)
        for screen in QApplication.screens():
            pixmap = screen.grabWindow(0)
            screen_geometry = screen.geometry()
            target = QRect(
                screen_geometry.topLeft() - geometry.topLeft(),
                screen_geometry.size(),
            )
            painter.drawPixmap(target, pixmap)
        painter.end()
        self.setGeometry(geometry)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self._screenshot)

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        self._start = event.position().toPoint()
        self._rubber.setGeometry(QRect(self._start, self._start))
        self._rubber.show()

    def mouseMoveEvent(self, event):
        if self._rubber.isVisible():
            self._rubber.setGeometry(
                QRect(self._start, event.position().toPoint()).normalized()
            )

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton or not self._rubber.isVisible():
            return
        rect = self._rubber.geometry().normalized()
        if rect.width() >= 5 and rect.height() >= 5:
            self.result_pixmap = self._screenshot.copy(rect)
            self.accept()
        else:
            self._rubber.hide()


class TagPopup(QDialog):
    def __init__(
        self,
        tags: list[tuple[str, str, int]],
        selected: set[str],
        parent=None,
        anchor: QPoint | None = None,
    ):
        super().__init__(parent, Qt.Dialog | Qt.FramelessWindowHint)
        self.setModal(True)
        self.buttons: dict[str, QPushButton] = {}
        self.setStyleSheet(
            "QDialog{background:#f5f5f5;border:1px solid #777;}"
            "QPushButton#tagChip{padding:5px 9px;border-radius:4px;border:1px solid #888;}"
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        grid = QGridLayout()
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)
        root.addLayout(grid)

        columns = max(1, min(6, int(ceil(len(tags) ** 0.5)) if tags else 1))
        for index, (name, color, usage) in enumerate(tags):
            button = QPushButton(name + (f" ({usage})" if usage else ""), self)
            button.setObjectName("tagChip")
            button.setCheckable(True)
            button.setChecked(name in selected)
            button.setProperty("tagName", name)
            button.setStyleSheet(
                f"QPushButton#tagChip{{background:{color};padding:5px 9px;border-radius:4px;"
                "border:1px solid #888;}"
                "QPushButton#tagChip:checked{border:2px solid #155b95;font-weight:700;}"
            )
            self.buttons[name] = button
            grid.addWidget(button, index // columns, index % columns)

        action_row = QHBoxLayout()
        action_row.addStretch()
        self.cancel_btn = QPushButton("Zrušit")
        self.save_btn = QPushButton("Uložit")
        self.save_btn.setDefault(True)
        action_row.addWidget(self.cancel_btn)
        action_row.addWidget(self.save_btn)
        root.addLayout(action_row)
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn.clicked.connect(self.accept)

        self.adjustSize()
        screen = QApplication.screenAt(anchor) if anchor else QApplication.primaryScreen()
        if screen:
            available = screen.availableGeometry()
            self.resize(
                min(self.width(), max(280, available.width() - 30)),
                min(self.height(), max(150, available.height() - 30)),
            )
            if anchor:
                x = min(max(available.left(), anchor.x()), available.right() - self.width())
                y = min(max(available.top(), anchor.y()), available.bottom() - self.height())
                self.move(x, y)

    def selected_tags(self) -> list[str]:
        return [name for name, button in self.buttons.items() if button.isChecked()]

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            event.accept()
            return
        if event.key() in (Qt.Key_Left, Qt.Key_Right):
            if self.save_btn.hasFocus():
                self.cancel_btn.setFocus()
                self.cancel_btn.setDefault(True)
                self.save_btn.setDefault(False)
            else:
                self.save_btn.setFocus()
                self.save_btn.setDefault(True)
                self.cancel_btn.setDefault(False)
            event.accept()
            return
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.cancel_btn.hasFocus():
                self.reject()
            else:
                self.accept()
            event.accept()
            return
        super().keyPressEvent(event)


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
    selection = table.selectionModel()
    if selection is None:
        return []
    for index in selection.selectedRows():
        source = proxy.mapToSource(index) if isinstance(proxy, SmartProxy) else index
        model = proxy.sourceModel() if isinstance(proxy, SmartProxy) else proxy
        result.append(model.record_id(source.row()))
    return list(dict.fromkeys(result))
