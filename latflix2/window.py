from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from PySide6.QtCore import QItemSelection, QItemSelectionModel, QSettings, QStringListModel, Qt
from PySide6.QtWidgets import (
    QApplication,
    QCompleter,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from . import __version__
from .catalog import CatalogPage
from .config import APP_NAME, data_root
from .database import GirlRecord, Repository
from .delegates import TableDelegate
from .detail import PersonDetail
from .dialogs import BulkLinksDialog, GirlDetailDialog, LinksDialog, ScreenCropDialog, TagsDialog
from .links_page import LinksPage
from .model import GirlTableModel
from .proxy import GirlFilterProxy
from .schema import GIRL_CATEGORIES, GIRL_COLUMNS, GIRL_FILTERS, ColumnSpec, display_age
from .sidebar import Sidebar
from .table import DataTable
from .toolbar import TableToolbar


class MainWindow(QMainWindow):
    def __init__(self, repository: Repository):
        super().__init__()
        self.repository = repository
        self.settings = QSettings("Latflix", "Latflix2")
        self.current_category = ""
        self.current_record_id: int | None = None
        self.links_filter_girl: int | None = None
        self.row_height_level = int(self.settings.value("table/row_height_level", 1))
        self._restoring_header = False

        self.model = GirlTableModel(repository, self)
        self.proxy = GirlFilterProxy(self)
        self.proxy.setSourceModel(self.model)
        self.delegate = TableDelegate(
            options_provider=self._editor_options,
            suggestions_provider=lambda text: self.repository.name_suggestions(
                text, self.current_category == "Oblíbené"
            ),
            parent=self,
        )

        self.setWindowTitle(APP_NAME)
        self.resize(1450, 820)
        self.setMinimumSize(950, 580)
        self._build_ui()
        self._build_menus()
        self._apply_style()
        self.load_category("Girls")

    # ---------- UI ----------

    def _build_ui(self) -> None:
        central = QWidget(self)
        body = QHBoxLayout(central)
        body.setContentsMargins(5, 5, 5, 5)
        body.setSpacing(6)

        self.sidebar = Sidebar(central)
        self.sidebar.category_changed.connect(self.load_category)
        self.sidebar.quick_tag_selected.connect(self.apply_quick_tag)
        body.addWidget(self.sidebar)

        self.pages = QStackedWidget(central)
        body.addWidget(self.pages, 1)
        self.setCentralWidget(central)

        self.girls_page = QWidget(self.pages)
        girls_layout = QVBoxLayout(self.girls_page)
        girls_layout.setContentsMargins(0, 0, 0, 0)
        girls_layout.setSpacing(5)

        self.detail = PersonDetail(self.girls_page)
        self.detail.favorite_changed.connect(self.set_favorite)
        self.detail.links_requested.connect(self.open_links_dialog)
        self.detail.detail_requested.connect(self.open_detail_dialog)
        self.detail.show_links_requested.connect(self.show_person_links)
        self.detail.photo_choose_requested.connect(self.choose_profile_photo)
        self.detail.photo_crop_requested.connect(self.crop_profile_photo)
        self.detail.photo_delete_requested.connect(self.delete_profile_photo)
        girls_layout.addWidget(self.detail)

        self.toolbar = TableToolbar(self.girls_page)
        self.toolbar.add_one.connect(lambda: self.add_girls(1))
        self.toolbar.add_many.connect(self.add_girls)
        self.toolbar.delete_requested.connect(self.delete_selected)
        self.toolbar.bulk_favorite.connect(self.bulk_set_favorite)
        self.toolbar.bulk_links.connect(self.bulk_add_links)
        self.toolbar.search_changed.connect(self.search_changed)
        self.toolbar.clear_search.connect(self.update_status)
        self.toolbar.clear_all.connect(self.clear_all_filters)
        self.toolbar.filter_requested.connect(self.open_filter_menu)
        girls_layout.addWidget(self.toolbar)

        self.table = DataTable(self.girls_page)
        self.table.setModel(self.proxy)
        self.table.bind_delegate(self.delegate)
        self.table.set_row_height_level(self.row_height_level)
        self.table.lock_requested.connect(self.set_locked)
        self.table.tags_requested.connect(self.edit_tags)
        self.table.note_requested.connect(self.edit_note)
        self.table.locked_primary_copy_requested.connect(self.copy_locked_primary)
        self.table.header_layout_changed.connect(self._save_header_state)
        self.table.header_lock_changed.connect(self._header_lock_changed)
        self.table.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.horizontalHeader().customContextMenuRequested.connect(self._header_context_menu)
        self.table.selectionModel().selectionChanged.connect(self.selection_changed)
        girls_layout.addWidget(self.table, 1)

        self.pages.addWidget(self.girls_page)

        self.links_page = LinksPage(self.repository, self.pages)
        self.pages.addWidget(self.links_page)

        self.catalog_pages = {
            "Typy": CatalogPage(self.repository, "types", False, self.pages),
            "Národnosti": CatalogPage(self.repository, "nationalities", False, self.pages),
            "Tagy": CatalogPage(self.repository, "tags", True, self.pages),
        }
        for page in self.catalog_pages.values():
            page.changed.connect(self.catalog_changed)
            self.pages.addWidget(page)

        self.placeholder = QLabel("", self.pages)
        self.placeholder.setObjectName("placeholderPage")
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.pages.addWidget(self.placeholder)

        self.overview = QWidget(self.pages)
        overview_layout = QVBoxLayout(self.overview)
        self.overview_title = QLabel("Přehled", self.overview)
        self.overview_title.setObjectName("pageTitle")
        self.overview_counts = QLabel("", self.overview)
        overview_layout.addWidget(self.overview_title)
        overview_layout.addWidget(self.overview_counts)
        overview_layout.addStretch(1)
        self.pages.addWidget(self.overview)

        self.record_count_label = QLabel("", self)
        self.average_age_label = QLabel("", self)
        self.row_level_label = QLabel("", self)
        self.statusBar().addWidget(self.record_count_label)
        self.statusBar().addWidget(self.average_age_label, 1)
        self.statusBar().addPermanentWidget(QLabel("Velikost řádků:", self))
        minus = QPushButton("−", self)
        plus = QPushButton("+", self)
        minus.setFixedSize(28, 24)
        plus.setFixedSize(28, 24)
        minus.clicked.connect(lambda: self.change_row_height(-1))
        plus.clicked.connect(lambda: self.change_row_height(1))
        self.statusBar().addPermanentWidget(minus)
        self.statusBar().addPermanentWidget(self.row_level_label)
        self.statusBar().addPermanentWidget(plus)
        self.build_label = QLabel(f"Latflix 2.0  v{__version__}", self)
        self.build_label.setObjectName("buildLabel")
        self.statusBar().addPermanentWidget(self.build_label)
        self._update_row_level_label()

        self._search_model = QStringListModel(self)
        self._search_completer = QCompleter(self._search_model, self.toolbar.search)
        self._search_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._search_completer.setFilterMode(Qt.MatchContains)
        self._search_completer.popup().setStyleSheet(
            "QListView { font-size: 15px; } "
            "QListView::item { min-height: 30px; padding: 2px 5px; } "
            "QListView::item:hover, QListView::item:selected { background: #2f78bd; color: white; }"
        )
        self.toolbar.search.setCompleter(self._search_completer)

    def _build_menus(self) -> None:
        file_menu = self.menuBar().addMenu("Soubor")
        file_menu.addAction("Import…")
        file_menu.addAction("Export…")
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Konec")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)

        edit_menu = self.menuBar().addMenu("Úpravy")
        edit_menu.addAction("Přidat záznam", lambda: self.add_girls(1))
        edit_menu.addAction("Smazat vybrané", self.delete_selected)

        self.menuBar().addMenu("Nástroje")

        view_menu = self.menuBar().addMenu("Zobrazení")
        self.toggle_detail_action = view_menu.addAction("Horní pracovní panel")
        self.toggle_detail_action.setCheckable(True)
        self.toggle_detail_action.setChecked(True)
        self.toggle_detail_action.triggered.connect(self.detail.setVisible)
        self.columns_menu = view_menu.addMenu("Sloupce")
        self.columns_menu.aboutToShow.connect(self._rebuild_columns_menu)

        self.menuBar().addMenu("Nastavení")

        help_menu = self.menuBar().addMenu("Nápověda")
        help_menu.addAction(
            "O aplikaci",
            lambda: QMessageBox.information(
                self,
                "Latflix 2.0",
                "Latflix 2.0\n\nČistá model/view verze podle nové specifikace.",
            ),
        )

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background: #efefef; color: #202020; font-size: 13px; }
            QWidget#sidebarPanel { background: #e9e9e9; border-right: 1px solid #aaa; }
            QPushButton#categoryButton {
                text-align: left; padding: 0 8px; border: 1px solid #aaa;
                border-radius: 3px; background: #f8f8f8;
            }
            QPushButton#categoryButton:hover { background: #edf3f8; }
            QPushButton#categoryButton:checked {
                background: #dce8f2; border-color: #7f9db8; font-weight: 700;
            }
            QPushButton#quickFilterButton {
                text-align: left; padding: 0 9px; border: 1px solid transparent; background: transparent;
            }
            QPushButton#quickFilterButton:hover { background: #e0e8ef; border-color: #b7c4cf; }
            QFrame#detailPanel { background: white; border: 1px solid #c5c5c5; border-radius: 5px; }
            QLabel#detailName { font-size: 21px; font-weight: 700; background: transparent; }
            QPushButton#favoriteButton:checked {
                background: #fff1a8; color: #806000; border-color: #d0aa21;
            }
            QPushButton#profilePhoto { background: #e5e5e5; border: 1px solid #aaa; font-weight: 700; }
            QPushButton#linkChip {
                background: #e9f2fb; color: #24527c; border: 1px solid #aac4de;
                border-radius: 3px; padding: 0 7px;
            }
            QPushButton, QToolButton {
                padding: 0 8px; border: 1px solid #aaa; border-radius: 3px; background: #fafafa;
            }
            QPushButton:hover, QToolButton:hover { background: #e7f0f8; }
            QPushButton:disabled, QToolButton:disabled { background: #e2e2e2; color: #929292; }
            QLineEdit, QComboBox, QTextEdit {
                background: white; border: 1px solid #aaa; border-radius: 2px; padding: 3px 6px;
            }
            QTableView {
                background: white; gridline-color: #d5d5d5; border: 1px solid #aaa;
                selection-background-color: transparent; selection-color: #202020;
            }
            QHeaderView::section {
                background: #ececec; border: 0; border-right: 1px solid #c8c8c8;
                border-bottom: 1px solid #aaa; padding: 4px 5px;
            }
            QLabel#pageTitle { font-size: 20px; font-weight: 700; }
            QLabel#placeholderPage { font-size: 18px; color: #666; }
            QLabel#buildLabel { padding: 2px 7px; border: 1px solid #aaa; background: #e5e5e5; font-weight: 700; }
            """
        )

    # ---------- categories ----------

    def load_category(self, category: str) -> None:
        category = str(category or "").strip()
        if not category:
            return

        if self.current_category in GIRL_CATEGORIES and category != self.current_category:
            self.repository.cleanup_blank_new_rows()
            self._save_header_state()

        self.current_category = category
        self.current_record_id = None
        self.sidebar.set_active(category)
        self.setWindowTitle(f"{APP_NAME} – {category}")

        if category in GIRL_CATEGORIES:
            self.pages.setCurrentWidget(self.girls_page)
            self.toolbar.set_favorites_mode(category == "Oblíbené")
            self.reload_girls()
            return

        self.detail.clear()
        if category == "Odkazy":
            self.pages.setCurrentWidget(self.links_page)
            self.links_page.load(self.links_filter_girl)
            self.record_count_label.setText(f"Záznamů: {self.links_page.model.rowCount()}")
            self.average_age_label.setText("")
            return

        if category in self.catalog_pages:
            page = self.catalog_pages[category]
            page.reload()
            self.pages.setCurrentWidget(page)
            self.record_count_label.setText(f"Záznamů: {page.model.rowCount()}")
            self.average_age_label.setText("")
            return

        if category == "Přehled":
            counts = self.repository.overview_counts()
            self.overview_counts.setText(
                f"Girls: {counts.get('Girls', 0)}\n"
                f"Oblíbené: {counts.get('Oblíbené', 0)}\n"
                f"Odkazy: {counts.get('Odkazy', 0)}"
            )
            self.pages.setCurrentWidget(self.overview)
            self.record_count_label.setText("")
            self.average_age_label.setText("")
            return

        self.placeholder.setText(
            f"{category}\n\nSekce je připravená pro další konfiguraci společného tabulkového systému."
        )
        self.pages.setCurrentWidget(self.placeholder)
        self.record_count_label.setText("")
        self.average_age_label.setText("")

    def reload_girls(self, preserve_id: int | None = None) -> None:
        favorite_mode = self.current_category == "Oblíbené"
        records = self.repository.list_girls(favorite_mode)
        preserve_id = preserve_id or self.current_record_id

        self.model.set_records(records, self.current_category)
        self.proxy.invalidate()
        self._load_title_overrides()
        self._restore_header_state()
        self._refresh_search_suggestions(self.toolbar.search.text())
        self.update_status()

        target = None
        if preserve_id is not None:
            source = self.model.index_for_record(preserve_id, 2)
            if source.isValid():
                proxy_index = self.proxy.mapFromSource(source)
                if proxy_index.isValid():
                    target = proxy_index

        if target is None and self.proxy.rowCount() > 0:
            target = self.proxy.index(0, 2)

        if target is not None and target.isValid():
            self.table.selectRow(target.row())
            self.table.scrollTo(target)
            self.current_record_id = int(target.data(Qt.UserRole + 1))
            self.refresh_detail()
        else:
            self.current_record_id = None
            self.detail.clear()

    # ---------- table / editors ----------

    def _editor_options(self, spec: ColumnSpec) -> list[str]:
        if spec.choices:
            return list(spec.choices)
        if spec.source:
            return list(self.repository.catalog_names(spec.source))
        return []

    def selection_changed(self, _selected=None, _deselected=None) -> None:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            self.current_record_id = None
            self.detail.clear()
            return
        index = selected[0]
        record_id = index.data(Qt.UserRole + 1)
        self.current_record_id = int(record_id) if record_id is not None else None
        self.refresh_detail()

    def selected_records(self) -> list[GirlRecord]:
        selection = self.table.selectionModel()
        if selection is None:
            return []
        result: list[GirlRecord] = []
        seen: set[int] = set()
        for proxy_index in selection.selectedRows():
            source_index = self.proxy.mapToSource(proxy_index)
            record = self.model.record_at(source_index.row())
            if record is not None and record.id not in seen:
                seen.add(record.id)
                result.append(record)
        return result

    def set_locked(self, record_id: int, locked: bool) -> None:
        self.repository.set_locked(record_id, locked)
        self.model.refresh_record(record_id)
        self.refresh_detail()

    def copy_locked_primary(self, text: str) -> None:
        QApplication.clipboard().setText(text)
        self.statusBar().showMessage("Zkopírováno", 1200)

    def edit_tags(self, record_id: int) -> None:
        record = self.repository.girl(record_id)
        if record is None or record.locked:
            return
        dialog = TagsDialog(self.repository, record.tags, self)
        if dialog.exec() == QDialog.Accepted:
            self.repository.set_tags(record_id, dialog.selected_tags())
            self.reload_girls(record_id)

    def edit_note(self, record_id: int) -> None:
        record = self.repository.girl(record_id)
        if record is None or record.locked:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Poznámka")
        layout = QVBoxLayout(dialog)
        editor = QTextEdit(dialog)
        editor.setPlainText(record.note)
        layout.addWidget(editor)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, dialog)
        buttons.button(QDialogButtonBox.Save).setText("Uložit")
        buttons.button(QDialogButtonBox.Cancel).setText("Zrušit")
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() == QDialog.Accepted:
            self.repository.update_field(record_id, "note", editor.toPlainText())
            self.reload_girls(record_id)

    # ---------- add/delete/bulk ----------

    def add_girls(self, count: int) -> None:
        if self.current_category != "Girls":
            return
        self.proxy.sort(-1)
        self.table._sort_column = -1
        ids = self.repository.add_girls(count)
        first = ids[0] if ids else None
        self.reload_girls(first)
        if first is None:
            return
        source = self.model.index_for_record(first, 2)
        proxy_index = self.proxy.mapFromSource(source)
        if proxy_index.isValid():
            self.table.start_text_edit(proxy_index)

    def delete_selected(self) -> None:
        if self.current_category != "Girls":
            return
        records = self.selected_records()
        unlocked = [record for record in records if not record.locked]
        if not unlocked:
            if records:
                self.statusBar().showMessage("Vybrané řádky jsou zamčené.", 2200)
            return
        result = QMessageBox.question(
            self,
            "Smazat",
            f"Smazat {len(unlocked)} vybraných odemčených záznamů?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if result == QMessageBox.Yes:
            self.repository.delete_unlocked(record.id for record in unlocked)
            self.reload_girls()

    def bulk_set_favorite(self, favorite: bool) -> None:
        records = self.selected_records()
        if not records:
            return
        if not favorite:
            result = QMessageBox.question(
                self,
                "Oblíbené",
                "Odebrat vybrané herečky z oblíbených?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if result != QMessageBox.Yes:
                return
        for record in records:
            self.repository.set_favorite(record.id, favorite)
        self.reload_girls()

    def bulk_add_links(self) -> None:
        records = self.selected_records()
        if not records:
            return
        dialog = BulkLinksDialog(self.repository, records, self)
        if dialog.exec() == QDialog.Accepted:
            self.reload_girls(self.current_record_id)

    # ---------- search / filters ----------

    def search_changed(self, text: str) -> None:
        self.proxy.set_search(text)
        self._refresh_search_suggestions(text)
        self.update_status()

    def _refresh_search_suggestions(self, text: str) -> None:
        self._search_model.setStringList(
            self.repository.name_suggestions(text, self.current_category == "Oblíbené")
        )

    def open_filter_menu(self, key: str, button: QPushButton) -> None:
        spec = next((item for item in GIRL_FILTERS if item.key == key), None)
        if spec is None:
            return
        menu = QMenu(button)
        menu.addAction("Vše", lambda: self.set_filter(spec, ""))

        values: list[str]
        if spec.choices:
            values = list(spec.choices)
        elif spec.source:
            values = list(self.repository.catalog_names(spec.source))
        else:
            values = []

        if spec.special == "nationality_ranked":
            ranked = list(self.repository.nationality_rank())
            ordered = ranked + [value for value in values if value not in ranked]
            for value in ordered[:10]:
                menu.addAction(value, lambda _checked=False, v=value: self.set_filter(spec, v))
            if len(ordered) > 10:
                menu.addSeparator()
                more = menu.addMenu("Další")
                for value in ordered[10:]:
                    more.addAction(value, lambda _checked=False, v=value: self.set_filter(spec, v))
        else:
            for value in values:
                menu.addAction(value, lambda _checked=False, v=value: self.set_filter(spec, v))

        menu.exec(button.mapToGlobal(button.rect().bottomLeft()))

    def set_filter(self, spec, value: str) -> None:
        self.proxy.set_filter(spec.key, value)
        self.toolbar.update_filter_label(spec.key, spec.title, value)
        self.update_status()

    def clear_all_filters(self) -> None:
        self.toolbar.search.blockSignals(True)
        self.toolbar.search.clear()
        self.toolbar.search.blockSignals(False)
        self.proxy.set_search("")
        self.proxy.clear_filters()
        self.toolbar.clear_filter_labels()
        self._refresh_search_suggestions("")
        self.update_status()

    def apply_quick_tag(self, tag: str) -> None:
        if self.current_category not in GIRL_CATEGORIES:
            self.load_category("Girls")
        self.proxy.set_filter("tags", tag)
        self.update_status()

    # ---------- detail panel ----------

    def refresh_detail(self) -> None:
        if self.current_record_id is None:
            self.detail.clear()
            return
        record = self.repository.girl(self.current_record_id)
        if record is None:
            self.detail.clear()
            return
        self.detail.show_record(
            record,
            self.repository.links(record.id),
            self.repository.source_rank(),
            display_age(record.age_source, date.today().year),
        )

    def set_favorite(self, record_id: int, favorite: bool) -> None:
        self.repository.set_favorite(record_id, favorite)
        self.reload_girls(record_id)

    def open_links_dialog(self, record_id: int) -> None:
        dialog = LinksDialog(self.repository, record_id, self)
        if dialog.exec() == QDialog.Accepted:
            self.reload_girls(record_id)

    def open_detail_dialog(self, record_id: int) -> None:
        record = self.repository.girl(record_id)
        if record is None:
            return
        dialog = GirlDetailDialog(self.repository, record, self)
        if dialog.exec() == QDialog.Accepted:
            dialog.save()
            self.reload_girls(record_id)

    def show_person_links(self, record_id: int) -> None:
        self.links_filter_girl = record_id
        self.load_category("Odkazy")

    def choose_profile_photo(self, record_id: int) -> None:
        path, _selected = QFileDialog.getOpenFileName(
            self,
            "Vybrat profilovku",
            str(Path.home() / "Plocha"),
            "Obrázky (*.png *.jpg *.jpeg *.webp *.bmp)",
        )
        if path:
            self.repository.update_field(record_id, "profile_path", path)
            self.reload_girls(record_id)

    def crop_profile_photo(self, record_id: int) -> None:
        dialog = ScreenCropDialog(self)
        if dialog.exec() != QDialog.Accepted or dialog.result_pixmap.isNull():
            return
        directory = data_root() / "profiles"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"girl-{record_id}.png"
        if dialog.result_pixmap.save(str(path), "PNG"):
            self.repository.update_field(record_id, "profile_path", str(path))
            self.reload_girls(record_id)

    def delete_profile_photo(self, record_id: int) -> None:
        result = QMessageBox.question(
            self,
            "Smazat profilovku",
            "Chcete profilovku smazat?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if result == QMessageBox.Yes:
            self.repository.update_field(record_id, "profile_path", "")
            self.reload_girls(record_id)

    # ---------- status ----------

    def update_status(self) -> None:
        if self.current_category not in GIRL_CATEGORIES:
            return
        visible = self.proxy.rowCount()
        total = self.model.rowCount()
        self.record_count_label.setText(
            f"Záznamů: {total}" if visible == total else f"Záznamů: {visible} / {total}"
        )

        ages: list[int] = []
        for source_row in self.proxy.source_rows_matching_filters():
            record = self.model.record_at(source_row)
            if record is None:
                continue
            value = display_age(record.age_source, date.today().year)
            try:
                number = int(value)
            except ValueError:
                continue
            if 1 <= number <= 100:
                ages.append(number)
        self.average_age_label.setText(
            f"Průměrný věk: {sum(ages) / len(ages):.1f}" if ages else "Průměrný věk: —"
        )

    def change_row_height(self, delta: int) -> None:
        self.row_height_level = max(1, min(5, self.row_height_level + int(delta)))
        self.table.set_row_height_level(self.row_height_level)
        self.settings.setValue("table/row_height_level", self.row_height_level)
        self._update_row_level_label()

    def _update_row_level_label(self) -> None:
        self.row_level_label.setText(f"{self.row_height_level}/5")

    # ---------- headers ----------

    def _settings_prefix(self) -> str:
        return f"sections/{self.current_category}"

    def _save_header_state(self) -> None:
        if self._restoring_header or self.current_category not in GIRL_CATEGORIES:
            return
        self.settings.setValue(
            f"{self._settings_prefix()}/header_state",
            self.table.horizontalHeader().saveState(),
        )

    def _restore_header_state(self) -> None:
        if self.current_category not in GIRL_CATEGORIES:
            return
        self._restoring_header = True
        try:
            header = self.table.horizontalHeader()
            for section in range(self.model.columnCount()):
                if section == 0:
                    self.table.setColumnWidth(section, 42)
                elif section == 1:
                    self.table.setColumnWidth(section, 42)
                else:
                    spec = self.model.column_spec(section)
                    if spec:
                        self.table.setColumnWidth(section, spec.default_width)
            state = self.settings.value(f"{self._settings_prefix()}/header_state")
            if state is not None:
                header.restoreState(state)
            self.table.set_header_locked(True)
        finally:
            self._restoring_header = False

    def _header_lock_changed(self, locked: bool) -> None:
        self.model.header_locked = bool(locked)
        self.model.headerDataChanged.emit(Qt.Horizontal, 0, 0)

    def _load_title_overrides(self) -> None:
        raw = str(self.settings.value(f"{self._settings_prefix()}/title_overrides", "{}") or "{}")
        try:
            values = json.loads(raw)
        except json.JSONDecodeError:
            values = {}
        self.model.set_title_overrides(values if isinstance(values, dict) else {})

    def _save_title_overrides(self) -> None:
        self.settings.setValue(
            f"{self._settings_prefix()}/title_overrides",
            json.dumps(self.model.title_overrides, ensure_ascii=False),
        )

    def _header_context_menu(self, point) -> None:
        if self.table.header_locked or self.current_category not in GIRL_CATEGORIES:
            return
        header = self.table.horizontalHeader()
        section = header.logicalIndexAt(point)
        if section < 2:
            return
        spec = self.model.column_spec(section)
        if spec is None:
            return
        menu = QMenu(header)
        rename = menu.addAction("Přejmenovat sloupec")
        hide = menu.addAction("Skrýt sloupec")
        chosen = menu.exec(header.mapToGlobal(point))
        if chosen == rename:
            current = self.model.title_overrides.get(spec.key, spec.title)
            text, ok = QInputDialog.getText(self, "Přejmenovat sloupec", "Název:", text=current)
            if ok and text.strip():
                self.model.title_overrides[spec.key] = text.strip()
                self._save_title_overrides()
                self.model.headerDataChanged.emit(Qt.Horizontal, section, section)
        elif chosen == hide:
            self.table.setColumnHidden(section, True)
            self._save_header_state()

    def _rebuild_columns_menu(self) -> None:
        self.columns_menu.clear()
        if self.current_category not in GIRL_CATEGORIES:
            action = self.columns_menu.addAction("Pro tuto sekci zatím nejsou sloupce.")
            action.setEnabled(False)
            return
        for section in range(2, self.model.columnCount()):
            spec = self.model.column_spec(section)
            if spec is None:
                continue
            label = self.model.title_overrides.get(spec.key, spec.title)
            action = self.columns_menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(not self.table.isColumnHidden(section))
            action.toggled.connect(
                lambda checked, s=section: self._toggle_column(s, checked)
            )

    def _toggle_column(self, section: int, visible: bool) -> None:
        self.table.setColumnHidden(section, not visible)
        self._save_header_state()

    # ---------- misc ----------

    def catalog_changed(self) -> None:
        if self.current_category in GIRL_CATEGORIES:
            self.reload_girls(self.current_record_id)

    def closeEvent(self, event) -> None:
        if self.current_category in GIRL_CATEGORIES:
            self.repository.cleanup_blank_new_rows()
            self._save_header_state()
        super().closeEvent(event)
