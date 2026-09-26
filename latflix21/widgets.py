from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QEvent, QModelIndex, QPoint, QRect, QSettings, QTimer, Qt, Signal, QStringListModel
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QComboBox, QCompleter, QDialog, QDialogButtonBox, QHBoxLayout,
    QInputDialog, QLineEdit, QMenu, QMessageBox, QPushButton, QStyledItemDelegate,
    QTableView, QTextEdit, QToolButton, QToolTip, QVBoxLayout, QWidget, QHeaderView,
)

from .models import SmartProxy


class PhotoLabel(QWidget):
    clicked = Signal()
    doubleClicked = Signal()
    contextRequested = Signal(QPoint)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = QPixmap()
        self._text = "Bez foto"
        self._single_click_pending = False
        self.setCursor(Qt.PointingHandCursor)

    def setPixmap(self, pixmap: QPixmap):
        self._pixmap = QPixmap(pixmap)
        self.update()

    def setText(self, text: str):
        self._text = str(text)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._single_click_pending = True
            delay = QApplication.doubleClickInterval() + 30
            QTimer.singleShot(delay, self._emit_single_if_pending)
        elif event.button() == Qt.RightButton:
            self.contextRequested.emit(event.position().toPoint())
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._single_click_pending = False
            self.doubleClicked.emit()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def _emit_single_if_pending(self):
        if self._single_click_pending:
            self._single_click_pending = False
            self.clicked.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#fafafa"))
        painter.setPen(QPen(QColor("#b8b8b8")))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        if not self._pixmap.isNull():
            scaled = self._pixmap.scaled(
                self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            x = (scaled.width() - self.width()) // 2
            y = (scaled.height() - self.height()) // 2
            painter.drawPixmap(self.rect(), scaled, QRect(x, y, self.width(), self.height()))
        elif self._text:
            painter.setPen(QColor("#666"))
            painter.drawText(self.rect(), Qt.AlignCenter, self._text)
        painter.end()


class ScreenSnipDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setCursor(Qt.CrossCursor)
        self._start = QPoint()
        self._current = QPoint()
        self._dragging = False
        self._selection = QRect()
        self._snapshot = QPixmap()

        screens = QApplication.screens()
        if not screens:
            return
        virtual = screens[0].geometry()
        for screen in screens[1:]:
            virtual = virtual.united(screen.geometry())
        self._virtual = virtual

        self._snapshot = QPixmap(virtual.size())
        self._snapshot.fill(Qt.black)
        painter = QPainter(self._snapshot)
        for screen in screens:
            geometry = screen.geometry()
            shot = screen.grabWindow(0)
            target = QRect(
                geometry.x() - virtual.x(),
                geometry.y() - virtual.y(),
                geometry.width(),
                geometry.height(),
            )
            painter.drawPixmap(target, shot)
        painter.end()
        self.setGeometry(virtual)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self._snapshot)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 70))
        if not self._selection.isNull():
            painter.drawPixmap(self._selection, self._snapshot, self._selection)
            pen = QPen(QColor("#ffffff"))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(self._selection.adjusted(0, 0, -1, -1))
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._start = event.position().toPoint()
            self._current = self._start
            self._dragging = True
            self._selection = QRect(self._start, self._current).normalized()
            self.update()
            return
        if event.button() == Qt.RightButton:
            self.reject()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging:
            self._current = event.position().toPoint()
            self._selection = QRect(self._start, self._current).normalized()
            self.update()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._dragging:
            self._dragging = False
            self._current = event.position().toPoint()
            self._selection = QRect(self._start, self._current).normalized()
            if self._selection.width() >= 4 and self._selection.height() >= 4:
                self.accept()
            else:
                self.reject()
            return
        super().mouseReleaseEvent(event)

    def selected_pixmap(self) -> QPixmap:
        if self.result() != QDialog.Accepted or self._selection.isNull():
            return QPixmap()
        return self._snapshot.copy(self._selection)


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
    def __init__(self, choices: Callable[[QModelIndex], list[str]], view, parent=None):
        super().__init__(parent or view)
        self.choices = choices
        self.view = view
        self.active_combo = None

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        self.active_combo = combo
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
        app = QApplication.instance()
        if app is not None:
            app.removeEventFilter(self)
            app.installEventFilter(self)
            combo.destroyed.connect(lambda *_: app.removeEventFilter(self))
        QTimer.singleShot(0, combo.showPopup)
        return combo

    def setEditorData(self, editor, index):
        text = str(index.data(Qt.EditRole) or "")
        found = editor.findText(text)
        editor.setCurrentIndex(found if found >= 0 else 0)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)

    def eventFilter(self, watched, event):
        combo = self.active_combo
        if (
            combo is not None
            and event.type() == QEvent.MouseButtonPress
            and combo.isVisible()
        ):
            global_pos = event.globalPosition().toPoint()
            target = QApplication.widgetAt(global_pos)
            popup = combo.view()
            if (
                target is combo
                or target is popup
                or (target is not None and popup.isAncestorOf(target))
            ):
                return False

            viewport = self.view.viewport()
            local = viewport.mapFromGlobal(global_pos)
            if viewport.rect().contains(local):
                index = self.view.indexAt(local)
                if index.isValid():
                    combo.hidePopup()
                    self.closeEditor.emit(combo)
                    self.active_combo = None

                    def activate(idx=QModelIndex(index)):
                        if not idx.isValid():
                            return
                        self.view.setCurrentIndex(idx)
                        self.view._single_click(idx)

                    QTimer.singleShot(0, activate)
                    return True
        return super().eventFilter(watched, event)


class AutoCompleteDelegate(QStyledItemDelegate):
    def __init__(self, suggestions: Callable[[str], list[str]], view, parent=None):
        super().__init__(parent or view)
        self.suggestions = suggestions
        self.view = view

    def createEditor(self, parent, option, index):
        edit = QLineEdit(parent)
        edit.setProperty("row", index.row())
        edit.setProperty("col", index.column())
        edit.setProperty("_latflix_finishing", False)
        completer = QCompleter(edit)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        model = QStringListModel(self.suggestions(""), completer)
        completer.setModel(model)
        popup = completer.popup()
        popup.setMinimumWidth(280)
        popup.setStyleSheet(
            "QListView{font-size:14px;outline:0;}"
            "QListView::item{min-height:28px;padding:3px 7px;}"
            "QListView::item:selected{background:#2f77c8;color:white;}"
            "QListView::item:hover{background:#2f77c8;color:white;}"
        )
        edit.setCompleter(completer)
        edit.textEdited.connect(lambda text: model.setStringList(self.suggestions(text)))
        completer.activated.connect(lambda *_: self._schedule_finish(edit))
        edit.returnPressed.connect(
            lambda: None if popup.isVisible() else self._schedule_finish(edit)
        )
        return edit

    def _schedule_finish(self, editor):
        if bool(editor.property("_latflix_finishing")):
            return
        editor.setProperty("_latflix_finishing", True)
        QTimer.singleShot(0, lambda e=editor: self._finish_and_move(e))

    def _finish_and_move(self, editor):
        if editor is None:
            return
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


class LockHeaderView(QHeaderView):
    def __init__(self, orientation, table, parent=None):
        super().__init__(orientation, parent)
        self.table = table

    def paintSection(self, painter, rect, logicalIndex):
        super().paintSection(painter, rect, logicalIndex)
        if logicalIndex != 0:
            return
        painter.save()
        font = painter.font()
        size = font.pointSize()
        if size > 0:
            font.setPointSize(size + 4)
        else:
            font.setPixelSize(18)
        painter.setFont(font)
        painter.setPen(QColor("#333333"))
        painter.drawText(
            rect,
            Qt.AlignCenter,
            "🔒" if self.table.header_locked else "🔓",
        )
        painter.restore()


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
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setSortIndicatorShown(False)
        self.setWordWrap(False)
        self.setHorizontalHeader(LockHeaderView(Qt.Horizontal, self, self))
        self.setMouseTracking(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)
        self.horizontalHeader().sectionClicked.connect(self._header_clicked)
        self.horizontalHeader().sectionMoved.connect(self._section_moved)
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
        if header.count() >= 2:
            header.setSectionResizeMode(0, QHeaderView.Fixed)
            header.setSectionResizeMode(1, QHeaderView.Fixed)

    def _section_moved(self, logical, old_visual, new_visual):
        header = self.horizontalHeader()
        if logical < 2 or new_visual < 2:
            header.blockSignals(True)
            try:
                current = header.visualIndex(logical)
                target = 0 if logical == 0 else 1 if logical == 1 else max(2, old_visual)
                header.moveSection(current, target)
            finally:
                header.blockSignals(False)
        self._save_layout()

    def _header_clicked(self, section):
        if section == 0:
            self.header_locked = not self.header_locked
            self._apply_header_lock()
            model = self.model()
            source_model = model.sourceModel() if isinstance(model, SmartProxy) else model
            if hasattr(source_model, "header_unlocked"):
                source_model.header_unlocked = not self.header_locked
                source_model.headerDataChanged.emit(Qt.Horizontal, 0, 0)
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
        header = self.horizontalHeader()
        visible_columns.sort(key=header.visualIndex)
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


class MenuFilter(QToolButton):
    valueChanged = Signal(str)

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self._value = ""
        self.setText(title)
        self.setPopupMode(QToolButton.InstantPopup)
        self.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.setStyleSheet("QToolButton::menu-indicator{image:none;width:0;}")
        self._menu = QMenu(self)
        self.setMenu(self._menu)

    def set_values(self, values: list[str], split_after: int | None = None):
        self._menu.clear()
        clear = self._menu.addAction(self.title)
        clear.triggered.connect(lambda: self.set_value(""))
        ordered = list(values)
        if split_after and len(ordered) > split_after:
            for value in ordered[:split_after]:
                action = self._menu.addAction(value)
                action.triggered.connect(lambda checked=False, v=value: self.set_value(v))
            self._menu.addSeparator()
            more = self._menu.addMenu("Další")
            for value in ordered[split_after:]:
                action = more.addAction(value)
                action.triggered.connect(lambda checked=False, v=value: self.set_value(v))
        else:
            for value in ordered:
                action = self._menu.addAction(value)
                action.triggered.connect(lambda checked=False, v=value: self.set_value(v))

    def set_value(self, value: str):
        self._value = str(value or "")
        self.setText(self._value or self.title)
        self.valueChanged.emit(self._value)

    def currentText(self):
        return self._value or self.title

    def currentIndex(self):
        return 0 if not self._value else 1

    def setCurrentIndex(self, index: int):
        if int(index) == 0:
            self.set_value("")


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
        self.clear_btn = QPushButton("⌫", self)
        self.clear_btn.setFixedWidth(30)
        self.clear_btn.setToolTip("Vymazat pouze Hledání")
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
