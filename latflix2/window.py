from __future__ import annotations

from time import perf_counter

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QInputDialog,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTableView,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from . import __version__
from .config import APP_NAME
from .database import Dataset, Repository
from .detail import PersonDetail
from .model import TableModel
from .overview import OverviewPanel
from .proxy import TableFilterProxy
from .sidebar import Sidebar


FILTER_COLUMNS = {
    "Girls": ("Národnost", "Typ", "Stav", "Hodnocení"),
    "Oblíbené": ("Národnost", "Typ", "Stav", "Hodnocení"),
    "Videa": ("Typ", "Studio", "Stav", "Kvalita"),
    "SUPER": ("Typ", "Studio", "Stav", "Kvalita"),
    "Odkazy": ("Typ", "Název"),
    "Studia": ("Země", "Typ"),
}


class MainWindow(QMainWindow):
    def __init__(self, repository: Repository):
        super().__init__()
        self.repository = repository
        self.current_category = ""
        self.current_dataset = Dataset("", (), ())
        self.row_height_level = 1
        self.filter_boxes: list[QComboBox] = []

        self.model = TableModel(repository, self)
        self.proxy = TableFilterProxy(self)
        self.proxy.setSourceModel(self.model)

        self.setWindowTitle(APP_NAME)
        self.resize(1300, 750)
        self.setMinimumSize(900, 560)
        self._build_ui()
        self._build_menus()
        self._apply_style()
        self._populate_initial_category()

    def _build_ui(self) -> None:
        central = QWidget(self)
        body = QHBoxLayout(central)
        body.setContentsMargins(8, 8, 8, 8)
        body.setSpacing(8)

        self.sidebar = Sidebar(central)
        self.sidebar.category_changed.connect(self.load_category)
        self.sidebar.quick_tag_selected.connect(self.apply_quick_tag)
        body.addWidget(self.sidebar)

        content = QWidget(central)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        self.detail = PersonDetail(content)
        self.detail.favorite_changed.connect(self.set_favorite)
        self.detail.rating_changed.connect(self.set_rating)
        content_layout.addWidget(self.detail)

        self.pages = QStackedWidget(content)
        content_layout.addWidget(self.pages, 1)

        table_page = QWidget(self.pages)
        table_layout = QVBoxLayout(table_page)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(5)

        controls = QHBoxLayout()
        controls.setSpacing(5)
        self.add_button = QPushButton("+ Přidat", table_page)
        self.delete_button = QPushButton("− Smazat", table_page)
        self.bulk_button = QToolButton(table_page)
        self.bulk_button.setText("Hromadné akce ▾")
        self.bulk_button.setPopupMode(QToolButton.InstantPopup)
        bulk_menu = QMenu(self.bulk_button)
        bulk_rating = bulk_menu.addAction("★ Hodnotit vybrané…")
        bulk_favorite = bulk_menu.addAction("☆ Přidat vybrané do oblíbených")
        bulk_unfavorite = bulk_menu.addAction("Odebrat vybrané z oblíbených")
        bulk_rating.triggered.connect(self.bulk_set_rating)
        bulk_favorite.triggered.connect(lambda: self.bulk_set_favorite(True))
        bulk_unfavorite.triggered.connect(lambda: self.bulk_set_favorite(False))
        self.bulk_button.setMenu(bulk_menu)

        self.search = QLineEdit(table_page)
        self.search.setPlaceholderText("Hledat v sekci…")
        self.search.setClearButtonEnabled(True)
        self.search.setMaximumWidth(220)
        self.search.textChanged.connect(self._search_changed)

        self.clear_filters_button = QToolButton(table_page)
        self.clear_filters_button.setText("Vyčistit")
        self.clear_filters_button.clicked.connect(self.clear_filters)

        controls.addWidget(self.add_button)
        controls.addWidget(self.delete_button)
        controls.addWidget(self.bulk_button)
        controls.addWidget(self.search)
        self.filters_host = QHBoxLayout()
        self.filters_host.setSpacing(5)
        controls.addLayout(self.filters_host, 1)
        controls.addWidget(self.clear_filters_button)
        table_layout.addLayout(controls)

        self.table = QTableView(table_page)
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
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.verticalHeader().setDefaultSectionSize(24)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.selectionModel().selectionChanged.connect(self.refresh_detail_from_selection)
        table_layout.addWidget(self.table, 1)

        self.overview = OverviewPanel(self.repository, self.pages)
        self.overview.category_requested.connect(self.load_category)

        self.pages.addWidget(table_page)
        self.pages.addWidget(self.overview)
        self.table_page = table_page
        body.addWidget(content, 1)
        self.setCentralWidget(central)

        self.add_button.clicked.connect(self.add_record)
        self.delete_button.clicked.connect(self.delete_selected)

        self.record_count_label = QLabel("Záznamů: 0", self)
        self.selection_label = QLabel("Vybráno: 0", self)
        self.average_age_label = QLabel("Průměrný věk: —", self)
        self.load_time_label = QLabel("Načtení: — ms", self)
        self.build_label = QLabel(f"Latflix 2.0  v{__version__}", self)
        self.build_label.setObjectName("buildLabel")

        self.statusBar().addWidget(self.record_count_label)
        self.statusBar().addWidget(self.selection_label)
        self.statusBar().addWidget(self.average_age_label, 1)
        self.statusBar().addPermanentWidget(self.load_time_label)
        self.statusBar().addPermanentWidget(QLabel("Velikost řádků:", self))

        self.row_minus = QPushButton("−", self)
        self.row_plus = QPushButton("+", self)
        self.row_level = QLabel("1/5", self)
        self.row_minus.setFixedSize(28, 24)
        self.row_plus.setFixedSize(28, 24)
        self.row_level.setMinimumWidth(34)
        self.row_minus.clicked.connect(lambda: self.change_row_height(-1))
        self.row_plus.clicked.connect(lambda: self.change_row_height(1))
        self.statusBar().addPermanentWidget(self.row_minus)
        self.statusBar().addPermanentWidget(self.row_level)
        self.statusBar().addPermanentWidget(self.row_plus)
        self.statusBar().addPermanentWidget(self.build_label)

    def _build_menus(self) -> None:
        file_menu = self.menuBar().addMenu("Soubor")
        file_menu.addAction("Import…")
        file_menu.addAction("Export…")
        file_menu.addSeparator()
        file_menu.addAction("Zálohovat…")
        file_menu.addAction("Obnovit ze zálohy…")
        file_menu.addSeparator()
        exit_action = QAction("Konec", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        edit_menu = self.menuBar().addMenu("Úpravy")
        add_action = QAction("Přidat záznam", self)
        add_action.setShortcut("Ctrl+N")
        add_action.triggered.connect(self.add_record)
        edit_menu.addAction(add_action)
        edit_menu.addAction("Přidat hromadně")
        edit_menu.addSeparator()
        edit_menu.addAction("Upravit vybraný záznam")
        delete_action = QAction("Smazat vybrané záznamy", self)
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(self.delete_selected)
        edit_menu.addAction(delete_action)
        edit_menu.addSeparator()
        edit_menu.addAction("Správa sloupců…")

        view_menu = self.menuBar().addMenu("Zobrazení")
        toggle_detail = QAction("Zobrazit / skrýt horní detail", self)
        toggle_detail.setShortcut("Ctrl+D")
        toggle_detail.triggered.connect(self.toggle_detail)
        view_menu.addAction(toggle_detail)
        refresh_action = QAction("Obnovit", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(lambda: self.load_category(self.current_category))
        view_menu.addAction(refresh_action)

        settings_menu = self.menuBar().addMenu("Nastavení")
        settings_menu.addAction("Otevřít nastavení…")

        help_menu = self.menuBar().addMenu("Nápověda")
        about = QAction("O aplikaci", self)
        about.triggered.connect(
            lambda: QMessageBox.information(
                self,
                "O aplikaci",
                "Latflix 2.0\n\nNový rychlý základ v model/view architektuře.",
            )
        )
        help_menu.addAction(about)

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background: #f0f0f0; color: #202020; }
            QWidget#sidebarPanel {
                background: #ededed;
                border-right: 1px solid #9b9b9b;
            }
            QPushButton#categoryButton {
                text-align: left; padding-left: 9px; font-size: 13px;
                color: #202020; border: 1px solid #a7a7a7; border-radius: 2px;
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fafafa,stop:1 #dddddd);
            }
            QPushButton#categoryButton:hover {
                border-color: #7f94aa;
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #f8fbff,stop:1 #dce8f4);
            }
            QPushButton#categoryButton:checked {
                font-weight: 700; border-color: #70869c;
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #e7f0f9,stop:1 #c8d9ea);
            }
            QLabel#quickTagsLabel { font-weight: 700; padding-left: 6px; }
            QPushButton#quickTagButton {
                text-align: left; padding-left: 12px; border: 1px solid transparent;
                border-radius: 2px; background: transparent;
            }
            QPushButton#quickTagButton:hover { background: #e1e9f2; border-color: #b4c0cc; }
            QFrame#detailBox {
                background: #ffffff; border: 1px solid #b8b8b8; border-radius: 2px;
            }
            QLabel#profilePhoto {
                background: #e5e5e5; border: 1px solid #b0b0b0; color: #777;
            }
            QLabel#detailName { font-size: 20px; font-weight: 800; }
            QLabel#detailMeta { color: #404040; }
            QLabel#detailSummary { color: #4e4e4e; }
            QPushButton#ratingStar {
                border: none; background: transparent; font-size: 19px; padding: 0;
            }
            QPushButton#ratingStar:hover { background: #eaf1f8; }
            QPushButton#favoriteButton {
                padding: 4px 9px; font-weight: 600;
            }
            QPushButton#favoriteButton:checked {
                color: #9a7200; background: #fff4bf; border: 1px solid #e1bd32;
            }
            QLabel#buildLabel {
                padding: 2px 7px; border: 1px solid #a8a8a8;
                background: #e7e7e7; font-weight: 700;
            }
            QLineEdit, QComboBox {
                background: white; border: 1px solid #a5a5a5; border-radius: 2px;
                padding: 4px 6px; min-height: 20px;
            }
            QTableView {
                background: white; alternate-background-color: #f7f7f7;
                gridline-color: #d8d8d8; border: 1px solid #aaa;
                selection-background-color: #d8e7f6; selection-color: #111;
            }
            QHeaderView::section {
                background: #ededed; border: 0; border-right: 1px solid #c8c8c8;
                border-bottom: 1px solid #aaa; padding: 4px 5px;
            }
            QFrame#overviewCard {
                background: white; border: 1px solid #b8b8b8; border-radius: 3px;
                min-width: 190px; min-height: 120px;
            }
            QLabel#overviewTitle { font-size: 21px; font-weight: 800; margin-bottom: 8px; }
            QLabel#overviewCardTitle { font-size: 15px; font-weight: 700; }
            QLabel#overviewCount { font-size: 30px; font-weight: 800; }
            """
        )

    def _populate_initial_category(self) -> None:
        self.sidebar.set_active("Girls")
        self.load_category("Girls")

    def load_category(self, category: str) -> None:
        category = str(category or "").strip()
        if not category:
            return
        self.sidebar.set_active(category)
        self.current_category = category
        self.setWindowTitle(f"{APP_NAME} - {category}")

        if category == "Přehled":
            self.pages.setCurrentWidget(self.overview)
            self.detail.show_category(category)
            self.overview.refresh()
            self.record_count_label.setText("Grafický přehled databáze")
            self.selection_label.setText("")
            self.average_age_label.setText("")
            self.load_time_label.setText("Načtení: — ms")
            self.row_minus.hide()
            self.row_plus.hide()
            self.row_level.hide()
            return

        self.pages.setCurrentWidget(self.table_page)
        self.row_minus.show()
        self.row_plus.show()
        self.row_level.show()

        started = perf_counter()
        dataset = self.repository.load(category)
        self.current_dataset = dataset
        self.model.set_dataset(dataset)
        self.proxy.clear_column_filters()
        self.search.blockSignals(True)
        self.search.clear()
        self.search.blockSignals(False)
        self.proxy.set_search("")

        for column, meta in enumerate(dataset.columns):
            self.table.setColumnHidden(column, not meta.visible)
        self.rebuild_filters(dataset)
        self.detail.show_category(category)

        if self.proxy.rowCount() > 0:
            self.table.selectRow(0)
            self.refresh_detail_from_selection()
        else:
            self.detail.show_category(category)

        self.update_visible_count()
        self.update_selection_status()
        self.update_average_age()
        elapsed_ms = (perf_counter() - started) * 1000.0
        self.load_time_label.setText(f"Načtení: {elapsed_ms:.1f} ms")
        self.statusBar().showMessage(
            f"{category}: {len(dataset.rows)} záznamů | načteno za {elapsed_ms:.1f} ms",
            5000,
        )
        people_view = category in {"Girls", "Oblíbené"}
        self.bulk_button.setVisible(people_view)
        self.add_button.setEnabled(bool(dataset.columns) and category != "SUPER")
        self.delete_button.setEnabled(bool(dataset.columns))

    def _search_changed(self, text: str) -> None:
        self.proxy.set_search(text)
        self.update_visible_count()

    def rebuild_filters(self, dataset: Dataset) -> None:
        while self.filters_host.count():
            item = self.filters_host.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.filter_boxes.clear()

        names = [column.name for column in dataset.columns]
        for filter_name in FILTER_COLUMNS.get(dataset.category, ()):
            if filter_name not in names:
                continue
            column = names.index(filter_name)
            values = sorted(
                {
                    str(row.values[column]).strip()
                    for row in dataset.rows
                    if column < len(row.values) and str(row.values[column]).strip()
                },
                key=str.casefold,
            )
            combo = QComboBox(self)
            combo.addItem(filter_name)
            combo.setItemData(0, "Vše")
            combo.addItem("Vše")
            for value in values[:100]:
                combo.addItem(value)
            combo.currentTextChanged.connect(
                lambda value, c=column, box=combo: self._filter_combo_changed(c, box, value)
            )
            self.filters_host.addWidget(combo)
            self.filter_boxes.append(combo)

    def _filter_combo_changed(self, column: int, combo: QComboBox, value: str) -> None:
        if combo.currentIndex() == 0:
            self.proxy.set_column_filter(column, "Vše")
        else:
            self.proxy.set_column_filter(column, value)
        self.update_visible_count()

    def clear_filters(self) -> None:
        self.search.clear()
        self.proxy.clear_column_filters()
        for combo in self.filter_boxes:
            combo.blockSignals(True)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)
        self.update_visible_count()

    def apply_quick_tag(self, tag: str) -> None:
        if self.current_category not in {"Girls", "Oblíbené"}:
            self.load_category("Girls")
        names = [column.name for column in self.current_dataset.columns]
        if "Tagy" not in names:
            return
        self.proxy.set_column_filter(names.index("Tagy"), tag)
        self.update_visible_count()

    def refresh_detail_from_selection(self, *_args) -> None:
        selection = self.table.selectionModel()
        if selection is None:
            return
        selected = selection.selectedRows()
        if not selected:
            self.detail.show_category(self.current_category)
            return
        source_index = self.proxy.mapToSource(selected[0])
        row = self.model.row_object(source_index.row())
        if row is not None:
            self.detail.show_record(self.current_dataset, row)

    def selected_record_ids(self) -> list[int]:
        selection = self.table.selectionModel()
        if selection is None:
            return []
        ids: list[int] = []
        seen: set[int] = set()
        for proxy_index in selection.selectedRows():
            source_index = self.proxy.mapToSource(proxy_index)
            record_id = self.model.record_id(source_index.row())
            if record_id is not None and record_id not in seen:
                seen.add(record_id)
                ids.append(record_id)
        return ids

    def add_record(self) -> None:
        if self.current_category == "Přehled":
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

    def set_favorite(self, record_id: int, favorite: bool) -> None:
        self.repository.set_favorite(record_id, favorite)
        self.load_category(self.current_category)
        self.statusBar().showMessage(
            "Přidáno do oblíbených." if favorite else "Odebráno z oblíbených.",
            2500,
        )

    def set_rating(self, record_id: int, rating: int) -> None:
        value = "" if rating <= 0 else str(rating)
        if self.repository.update_named_cell(record_id, self.current_category, "Hodnocení", value):
            self.load_category(self.current_category)

    def bulk_set_favorite(self, favorite: bool) -> None:
        ids = self.selected_record_ids()
        if not ids:
            return
        for record_id in ids:
            self.repository.set_favorite(record_id, favorite)
        self.load_category(self.current_category)
        action = "přidáno do" if favorite else "odebráno z"
        self.statusBar().showMessage(
            f"{len(ids)} záznamů bylo {action} oblíbených.",
            2500,
        )

    def bulk_set_rating(self) -> None:
        ids = self.selected_record_ids()
        if not ids:
            return
        labels = (
            "Bez hodnocení",
            "★☆☆☆☆  1",
            "★★☆☆☆  2",
            "★★★☆☆  3",
            "★★★★☆  4",
            "★★★★★  5",
        )
        selected, ok = QInputDialog.getItem(
            self,
            "Hromadné hodnocení",
            f"Nastavit hodnocení pro {len(ids)} vybraných řádků:",
            labels,
            0,
            False,
        )
        if not ok:
            return
        rating = 0 if selected == labels[0] else labels.index(selected)
        value = "" if rating <= 0 else str(rating)
        changed = 0
        for record_id in ids:
            if self.repository.update_named_cell(
                record_id,
                self.current_category,
                "Hodnocení",
                value,
            ):
                changed += 1
        self.load_category(self.current_category)
        self.statusBar().showMessage(
            f"Hodnocení změněno u {changed} záznamů.",
            2500,
        )

    def toggle_detail(self) -> None:
        self.detail.setVisible(not self.detail.isVisible())

    def update_selection_status(self, *_args) -> None:
        selection = self.table.selectionModel()
        selected = len(selection.selectedRows()) if selection is not None else 0
        self.selection_label.setText(f"Vybráno: {selected}")

    def update_average_age(self) -> None:
        if self.current_category not in {"Girls", "Oblíbené"}:
            self.average_age_label.setText("")
            return
        names = [column.name for column in self.current_dataset.columns]
        if "Věk" not in names:
            self.average_age_label.setText("Průměrný věk: —")
            return
        column = names.index("Věk")
        ages = []
        for row in self.current_dataset.rows:
            try:
                age = int(str(row.values[column]).strip())
            except (ValueError, TypeError, IndexError):
                continue
            if 10 <= age <= 100:
                ages.append(age)
        if not ages:
            self.average_age_label.setText("Průměrný věk: —")
            return
        self.average_age_label.setText(
            f"Průměrný věk: {sum(ages) / len(ages):.1f}"
        )

    def update_visible_count(self) -> None:
        visible = self.proxy.rowCount()
        total = self.model.rowCount()
        self.record_count_label.setText(
            f"Záznamů: {total}" if visible == total else f"Záznamů: {visible} / {total}"
        )

    def change_row_height(self, delta: int) -> None:
        self.row_height_level = max(1, min(5, self.row_height_level + delta))
        heights = {1: 24, 2: 28, 3: 32, 4: 38, 5: 46}
        self.table.verticalHeader().setDefaultSectionSize(heights[self.row_height_level])
        self.row_level.setText(f"{self.row_height_level}/5")
