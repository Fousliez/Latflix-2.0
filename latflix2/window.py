from __future__ import annotations

from time import perf_counter

from PySide6.QtCore import QSortFilterProxyModel, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPushButton,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from .config import APP_NAME
from .database import Repository
from .model import TableModel


PREFERRED_SECTIONS = (
    "Přehled",
    "Girls",
    "Oblíbené",
    "Odkazy",
    "Videa",
    "SUPER",
    "Studia",
    "Stavy",
    "Tagy",
    "Typy",
    "Kvality",
)


class MainWindow(QMainWindow):
    def __init__(self, repository: Repository):
        super().__init__()
        self.repository = repository
        self.current_category = ""
        self.setWindowTitle(APP_NAME)
        self.resize(1380, 820)
        self.setMinimumSize(900, 560)

        self.model = TableModel(repository, self)
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy.setFilterKeyColumn(-1)
        self.proxy.setDynamicSortFilter(True)

        self._build_ui()
        self._apply_style()
        self._populate_sections()

    def _build_ui(self) -> None:
        central = QWidget(self)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = QListWidget(central)
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(190)
        self.sidebar.currentTextChanged.connect(self.load_category)
        root.addWidget(self.sidebar)

        main = QWidget(central)
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(12, 10, 12, 8)
        main_layout.setSpacing(8)

        header = QHBoxLayout()
        self.section_title = QLabel("Latflix 2.0", main)
        self.section_title.setObjectName("sectionTitle")
        header.addWidget(self.section_title)
        header.addStretch(1)
        self.search = QLineEdit(main)
        self.search.setPlaceholderText("Hledat v aktuální sekci…")
        self.search.setClearButtonEnabled(True)
        self.search.setMaximumWidth(420)
        self.search.textChanged.connect(self.proxy.setFilterFixedString)
        header.addWidget(self.search)
        main_layout.addLayout(header)

        self.splitter = QSplitter(Qt.Horizontal, main)
        self.table = QTableView(self.splitter)
        self.table.setModel(self.proxy)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(
            QAbstractItemView.DoubleClicked
            | QAbstractItemView.EditKeyPressed
            | QAbstractItemView.SelectedClicked
        )
        self.table.verticalHeader().setDefaultSectionSize(24)
        self.table.horizontalHeader().setStretchLastSection(True)

        detail = QFrame(self.splitter)
        detail.setObjectName("detailPanel")
        detail.setMinimumWidth(250)
        detail_layout = QVBoxLayout(detail)
        detail_layout.setContentsMargins(14, 14, 14, 14)
        self.detail_title = QLabel("Detail", detail)
        self.detail_title.setObjectName("detailTitle")
        self.detail_text = QLabel(
            "Detail vybraného záznamu doplníme v další vrstvě.\n\n"
            "Teď je hlavní cíl ověřit rychlost tabulky a přepínání sekcí.",
            detail,
        )
        self.detail_text.setWordWrap(True)
        detail_layout.addWidget(self.detail_title)
        detail_layout.addWidget(self.detail_text)
        detail_layout.addStretch(1)

        self.splitter.addWidget(self.table)
        self.splitter.addWidget(detail)
        self.splitter.setSizes([1000, 320])
        main_layout.addWidget(self.splitter, 1)

        actions = QHBoxLayout()
        self.add_button = QPushButton("+ Přidat", main)
        self.delete_button = QPushButton("− Smazat", main)
        self.add_button.clicked.connect(self.add_record)
        self.delete_button.clicked.connect(self.delete_selected)
        actions.addWidget(self.add_button)
        actions.addWidget(self.delete_button)
        actions.addStretch(1)
        main_layout.addLayout(actions)

        root.addWidget(main, 1)
        self.setCentralWidget(central)
        self.statusBar().showMessage("Latflix 2.0 připraven")

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background: #f4f4f4; color: #202020; }
            QListWidget#sidebar {
                background: #262626; color: #f2f2f2; border: 0;
                padding: 8px 0; font-size: 14px;
            }
            QListWidget#sidebar::item { padding: 9px 14px; }
            QListWidget#sidebar::item:selected {
                background: #3d5872; color: white; font-weight: 700;
            }
            QLabel#sectionTitle { font-size: 21px; font-weight: 800; }
            QLineEdit {
                background: white; border: 1px solid #a5a5a5;
                border-radius: 4px; padding: 6px 8px;
            }
            QTableView {
                background: white; alternate-background-color: #f8f8f8;
                gridline-color: #dedede; border: 1px solid #b7b7b7;
            }
            QHeaderView::section {
                background: #e8e8e8; border: 0;
                border-right: 1px solid #c8c8c8;
                border-bottom: 1px solid #aaaaaa;
                padding: 5px; font-weight: 400;
            }
            QFrame#detailPanel {
                background: #ffffff; border: 1px solid #c1c1c1;
            }
            QLabel#detailTitle { font-size: 17px; font-weight: 700; }
            QPushButton {
                background: #f2f2f2; border: 1px solid #8b8b8b;
                border-radius: 3px; padding: 5px 12px;
            }
            QPushButton:hover { background: #e6e6e6; }
            """
        )

    def _populate_sections(self) -> None:
        available = self.repository.categories()
        display = []
        for name in PREFERRED_SECTIONS:
            if name == "Videa" and ("Videa" in available or "Scény / filmy" in available):
                display.append("Videa")
            elif name in available:
                display.append(name)
        for name in available:
            shown = "Videa" if name == "Scény / filmy" else name
            if shown not in display:
                display.append(shown)
        self.sidebar.addItems(display)
        if display:
            self.sidebar.setCurrentRow(0)

    def load_category(self, category: str) -> None:
        category = str(category or "").strip()
        if not category:
            return
        started = perf_counter()
        dataset = self.repository.load(category)
        self.model.set_dataset(dataset)
        self.current_category = category
        self.section_title.setText(category)
        self.search.clear()

        for column, meta in enumerate(dataset.columns):
            self.table.setColumnHidden(column, not meta.visible)
        elapsed_ms = (perf_counter() - started) * 1000.0
        self.statusBar().showMessage(
            f"{category}: {len(dataset.rows)} záznamů | načteno za {elapsed_ms:.1f} ms"
        )

    def selected_record_ids(self) -> list[int]:
        ids = []
        seen = set()
        for proxy_index in self.table.selectionModel().selectedRows():
            source_index = self.proxy.mapToSource(proxy_index)
            record_id = self.model.record_id(source_index.row())
            if record_id is not None and record_id not in seen:
                seen.add(record_id)
                ids.append(record_id)
        return ids

    def add_record(self) -> None:
        if not self.current_category:
            return
        record_id = self.repository.add_record(self.current_category)
        self.load_category(self.current_category)
        for source_row in range(self.model.rowCount()):
            if self.model.record_id(source_row) == record_id:
                proxy_index = self.proxy.mapFromSource(self.model.index(source_row, 0))
                if proxy_index.isValid():
                    self.table.selectRow(proxy_index.row())
                    self.table.scrollTo(proxy_index)
                break

    def delete_selected(self) -> None:
        ids = self.selected_record_ids()
        if not ids:
            return
        self.repository.soft_delete(ids)
        self.load_category(self.current_category)
