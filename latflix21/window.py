from __future__ import annotations

import json
import shutil
from collections import Counter
from pathlib import Path

from PySide6.QtCore import QByteArray, QModelIndex, QSettings, Qt, QUrl, Signal
from PySide6.QtGui import QAction, QDesktopServices, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QDialog, QFileDialog, QFormLayout, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QMainWindow, QMenu, QMessageBox, QPushButton, QSizePolicy, QStackedWidget,
    QStatusBar, QVBoxLayout, QWidget, QInputDialog,
)

from . import __version__
from .config import APP_NAME, data_root
from .db import Repository
from .dialogs import (
    BulkGirlLinksDialog, BulkLinksDialog, ExportLinksDialog, GirlDetailDialog,
    GirlLinksDialog, LinkCatalogDialog, VideoDetailDialog, VisibleLinkFiltersDialog,
)
from .models import (
    CatalogModel, GirlsModel, LinksModel, SmartProxy, StudiosModel, VideosModel,
    age_display,
)
from .widgets import (
    AutoCompleteDelegate, BUTTON_H, ChoiceDelegate, ChipButton, DataTableView,
    FilterButton, FlowWidget, NoteDelegate, ProfileButton, ScreenCropDialog,
    ScrollFilterButton, SearchBox, SplitAddButton, TagPopup, TextDelegate,
    open_note_for_table, selected_source_ids,
)


TOP_PANEL_H = 136


class Sidebar(QWidget):
    sectionRequested = Signal(str)
    quickTagRequested = Signal(str)
    collapsedChanged = Signal(bool)

    MAIN = ("Přehled", "Girls", "Oblíbené", "Odkazy", "Videa", "Super", "Studia")
    HELPERS = ("Stavy", "Kvality", "Tagy", "Typy", "Národnosti")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.expanded_width = 156
        self.collapsed_width = 31
        self.collapsed = False
        self.buttons: dict[str, QPushButton] = {}
        self.quick_buttons: list[QPushButton] = []
        self.setObjectName("sidebarPanel")
        self.setFixedWidth(self.expanded_width)

        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(4)

        self.collapse_btn = QPushButton("◀", self)
        self.collapse_btn.setFixedHeight(27)
        self.collapse_btn.clicked.connect(self.toggle)
        root.addWidget(self.collapse_btn)

        for name in self.MAIN:
            root.addWidget(self._button(name))

        root.addStretch()

        for name in self.HELPERS:
            root.addWidget(self._button(name))

        self.quick_label = QPushButton("Rychlé filtry ▾", self)
        self.quick_label.setFlat(True)
        self.quick_label.setStyleSheet("text-align:left;font-weight:700")
        self.quick_label.clicked.connect(self.toggle_quick)
        root.addWidget(self.quick_label)

        self.quick_host = QWidget(self)
        self.quick_layout = QVBoxLayout(self.quick_host)
        self.quick_layout.setContentsMargins(0, 0, 0, 0)
        self.quick_layout.setSpacing(3)
        root.addWidget(self.quick_host)

    def _button(self, name):
        button = QPushButton(name, self)
        button.setObjectName("categoryButton")
        button.setCheckable(True)
        button.setFixedHeight(29)
        button.clicked.connect(
            lambda checked=False, section=name: self.sectionRequested.emit(section)
        )
        self.buttons[name] = button
        return button

    def set_collapsed(self, collapsed: bool):
        collapsed = bool(collapsed)
        if self.collapsed == collapsed:
            return
        self.collapsed = collapsed
        for widget in [*self.buttons.values(), self.quick_label, self.quick_host]:
            widget.setVisible(not self.collapsed)
        self.setFixedWidth(self.collapsed_width if self.collapsed else self.expanded_width)
        self.collapse_btn.setText("▶" if self.collapsed else "◀")
        self.collapsedChanged.emit(self.collapsed)

    def toggle(self):
        self.set_collapsed(not self.collapsed)

    def expand(self):
        self.set_collapsed(False)

    def toggle_quick(self):
        visible = not self.quick_host.isVisible()
        self.quick_host.setVisible(visible)
        self.quick_label.setText("Rychlé filtry ▾" if visible else "Rychlé filtry ▸")

    def set_quick_tags(self, tags: list[str]):
        while self.quick_layout.count():
            item = self.quick_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.quick_buttons.clear()
        for tag in tags:
            button = QPushButton(tag, self.quick_host)
            button.setObjectName("quickFilterButton")
            button.setFixedHeight(27)
            button.clicked.connect(
                lambda checked=False, value=tag: self.quickTagRequested.emit(value)
            )
            self.quick_layout.addWidget(button)
            self.quick_buttons.append(button)

    def set_active(self, name):
        for section, button in self.buttons.items():
            button.blockSignals(True)
            button.setChecked(section == name)
            button.blockSignals(False)


class BasePage(QWidget):
    def __init__(self, repo: Repository, title: str, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.title = title
        self.outer = QVBoxLayout(self)
        self.outer.setContentsMargins(7, 5, 7, 5)
        self.outer.setSpacing(5)
        self.top: QWidget | None = None

    def set_top_visible(self, visible: bool):
        if self.top is not None:
            self.top.setVisible(bool(visible))

    def refresh(self):
        pass

    def record_count(self) -> int | None:
        return None

    def status_extra(self) -> str:
        return ""


class OverviewCard(QFrame):
    clicked = Signal(str)

    def __init__(self, title, count, subtitle, parent=None):
        super().__init__(parent)
        self.title = title
        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(120)
        self.setStyleSheet(
            "QFrame{background:#f8f8f8;border:1px solid #c8c8c8;border-radius:7px;}"
            "QFrame:hover{background:#f0f5fa;border-color:#91abc4;}"
            "QLabel{background:transparent;border:0;}"
        )
        layout = QVBoxLayout(self)
        count_label = QLabel(str(count))
        count_label.setStyleSheet("font-size:31px;font-weight:700;color:#245b8d")
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size:16px;font-weight:700")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet("color:#7b7b7b")
        layout.addWidget(count_label)
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        layout.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.title)
        super().mousePressEvent(event)


class OverviewPage(BasePage):
    def __init__(self, repo, navigate, parent=None):
        super().__init__(repo, "Přehled", parent)
        self.navigate = navigate
        heading = QLabel("Přehled databáze")
        heading.setStyleSheet("font-size:21px;font-weight:700")
        self.outer.addWidget(heading)
        self.outer.addWidget(
            QLabel("Aktuální stav databáze. Kliknutím na kartu zobrazíš podrobnosti.")
        )
        self.grid = QGridLayout()
        self.grid.setSpacing(10)
        self.outer.addLayout(self.grid)
        self.outer.addStretch()
        self.refresh()

    def refresh(self):
        data = self.repo.overview()
        specs = [
            ("Girls", data["girls"], "Dívky v databázi"),
            ("Oblíbené", data["favorites"], "Oblíbené dívky"),
            ("Videa", data["videos"], "Filmy a videa"),
            ("SUPER", data["super"], "Vybrané filmy a videa"),
            ("Studia", data["studios"], "Studia a platformy"),
            ("Odkazy", data["links"], "Sítě, zdroje a rozcestníky"),
            ("Tagy", data["tags"], "Tagy a štítky"),
        ]
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for index, (name, count, subtitle) in enumerate(specs):
            card = OverviewCard(name, count, subtitle, self)
            card.clicked.connect(self.open_detail)
            self.grid.addWidget(card, index // 3, index % 3)

    @staticmethod
    def _average_age(girls):
        values = []
        for girl in girls:
            try:
                age = int(age_display(girl.age_source))
            except Exception:
                continue
            if 1 <= age <= 100:
                values.append(age)
        return "—" if not values else f"{sum(values) / len(values):.1f}".replace(".", ",")

    @staticmethod
    def _rank(values):
        counts = Counter(value for value in values if value)
        return sorted(counts.items(), key=lambda item: (-item[1], item[0].casefold()))

    @staticmethod
    def _rank_text(items, maximum=3):
        return "\n".join(
            f"{index + 1}. {name} ({count}×)"
            for index, (name, count) in enumerate(items[:maximum])
        ) or "—"

    def open_detail(self, name):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Přehled · {name}")
        dialog.resize(430, 320)
        root = QVBoxLayout(dialog)
        title = QLabel(name)
        title.setStyleSheet("font-size:20px;font-weight:700")
        root.addWidget(title)
        form = QFormLayout()
        root.addLayout(form)

        girls = self.repo.girls(False)
        favorites = [g for g in girls if g.favorite]
        videos = self.repo.videos(False)
        super_videos = [v for v in videos if v.in_super]
        valid_videos = [v for v in videos if self.repo.video_is_valid(v)]
        valid_super_videos = [v for v in super_videos if self.repo.video_is_valid(v)]
        studios = self.repo.studios()
        links = self.repo.links()

        if name == "Girls":
            form.addRow("Počet dívek:", QLabel(str(len(girls))))
            form.addRow("Průměrný věk:", QLabel(self._average_age(girls)))
            form.addRow(
                "Nejčastější národnosti:",
                QLabel(self._rank_text(self._rank(g.nationality for g in girls))),
            )
            form.addRow("Oblíbené:", QLabel(str(len(favorites))))
        elif name == "Oblíbené":
            form.addRow("Počet dívek:", QLabel(str(len(favorites))))
            form.addRow("Průměrný věk:", QLabel(self._average_age(favorites)))
            form.addRow(
                "Nejčastější národnosti:",
                QLabel(self._rank_text(self._rank(g.nationality for g in favorites))),
            )
            form.addRow(
                "Ohodnoceno:",
                QLabel(str(sum(1 for g in favorites if g.rating.strip()))),
            )
        elif name == "Videa":
            form.addRow("Počet videí:", QLabel(str(len(videos))))
            form.addRow(
                "Nejčastější herečky:",
                QLabel(self._rank_text(self._rank(
                    participant[1]
                    for video in valid_videos
                    for participant in video.participants
                ))),
            )
            form.addRow(
                "Ohodnoceno:",
                QLabel(str(sum(1 for video in videos if video.rating.strip()))),
            )
        elif name == "SUPER":
            form.addRow("Počet videí:", QLabel(str(len(super_videos))))
            form.addRow(
                "Nejčastější studia:",
                QLabel(self._rank_text(self._rank(v.studio_name for v in valid_super_videos))),
            )
            form.addRow(
                "Nejčastější herečky:",
                QLabel(self._rank_text(self._rank(
                    participant[1]
                    for video in valid_super_videos
                    for participant in video.participants
                ))),
            )
            form.addRow(
                "Ohodnoceno:",
                QLabel(str(sum(1 for video in super_videos if video.rating.strip()))),
            )
        elif name == "Studia":
            used = [studio for studio in studios if studio.occurrences > 0]
            ranked = sorted(
                studios,
                key=lambda studio: (-studio.occurrences, studio.name.casefold()),
            )
            form.addRow("Počet studií:", QLabel(str(len(studios))))
            form.addRow("Použitých ve videích:", QLabel(str(len(used))))
            form.addRow(
                "Nejčastější studia:",
                QLabel("\n".join(
                    f"{index + 1}. {studio.name} ({studio.occurrences}×)"
                    for index, studio in enumerate(ranked[:3])
                    if studio.name
                ) or "—"),
            )
        elif name == "Odkazy":
            counts = Counter(link.category for link in links)
            form.addRow("Celkem odkazů:", QLabel(str(len(links))))
            form.addRow("Sítě:", QLabel(str(counts["Síť"])))
            form.addRow("Zdroje:", QLabel(str(counts["Zdroj"])))
            form.addRow("Rozcestníky:", QLabel(str(counts["Rozcestník"])))
        elif name == "Tagy":
            usage = self.repo.tag_usage()
            ranked = sorted(usage.items(), key=lambda item: (-item[1], item[0].casefold()))
            form.addRow("Počet tagů:", QLabel(str(len(usage))))
            form.addRow("Použitých tagů:", QLabel(str(sum(1 for n in usage.values() if n))))
            form.addRow(
                "Nejpoužívanější tag:",
                QLabel(f"{ranked[0][0]} ({ranked[0][1]}×)" if ranked else "—"),
            )

        buttons = QHBoxLayout()
        go = QPushButton(f"Přejít do sekce {name}")
        close = QPushButton("Zavřít")
        buttons.addStretch()
        buttons.addWidget(go)
        buttons.addWidget(close)
        root.addLayout(buttons)
        go.clicked.connect(
            lambda: (
                dialog.accept(),
                self.navigate("Super" if name == "SUPER" else name),
            )
        )
        close.clicked.connect(dialog.reject)
        dialog.exec()


class TablePage(BasePage):
    def __init__(self, repo, title, model, settings: QSettings, parent=None):
        super().__init__(repo, title, parent)
        self.settings = settings
        self.model = model
        self.proxy = SmartProxy(self)
        self.proxy.setSourceModel(model)
        self._restoring = False
        self._sort_column = -1
        self._sort_order = Qt.AscendingOrder

        self.top = QWidget(self)
        self.top.setFixedHeight(TOP_PANEL_H)
        self.outer.addWidget(self.top)

        self.toolbar = QWidget(self)
        self.toolbar_lay = QHBoxLayout(self.toolbar)
        self.toolbar_lay.setContentsMargins(0, 0, 0, 0)
        self.toolbar_lay.setSpacing(5)
        self.outer.addWidget(self.toolbar)

        self.table = DataTableView(self)
        self.table.setModel(self.proxy)
        self.outer.addWidget(self.table, 1)
        self.table.noteRequested.connect(lambda idx: self._note(idx))
        self.table.webRequested.connect(self._web_clicked)
        self.table.imageRequested.connect(self._image_clicked)
        self.table.tagRequested.connect(self._tag_clicked)
        self.table.headerLayoutChanged.connect(self.save_header_state)
        self.table.headerContextRequested.connect(self.header_context_menu)
        self.table.header.sectionClicked.connect(self._header_clicked)

        self._install_delegates()
        self._load_title_overrides()
        self.restore_header_state()
        self._apply_widths_if_fresh()

        self.clear = QPushButton("Vyčistit")
        self.clear.setFixedHeight(BUTTON_H)

    def _header_clicked(self, section):
        if section < 2:
            return
        if section == self._sort_column:
            self._sort_order = (
                Qt.DescendingOrder
                if self._sort_order == Qt.AscendingOrder
                else Qt.AscendingOrder
            )
        else:
            self._sort_column = section
            self._sort_order = Qt.AscendingOrder
        self.proxy.sort(section, self._sort_order)
        self.table.header.setSortIndicatorShown(False)
        self.update_status()

    def reset_sort(self):
        self._sort_column = -1
        self.proxy.sort(-1)
        self.table.header.setSortIndicatorShown(False)

    def _choices(self, source):
        if source == "face":
            return ["", "Ano", "Asi ano", "Asi ne", "Ne", "Zjistit"]
        if source == "yes":
            return ["", "Ano", "Ne", "Asi ne", "Asi ano", "Zjistit"]
        if source == "yesno":
            return ["", "Ano", "Ne"]
        if source == "girl_status":
            return ["", "Aktivní", "Neaktivní", "Smazaná"]
        if source in {"types", "nationalities", "states", "qualities"}:
            return [""] + self.repo.catalog(source)
        if source == "link_types":
            return [""] + [str(item["name"]) for item in self.repo.link_types()]
        if source == "active":
            return ["", "Akt.", "Neakt."]
        return [""]

    def _suggestions(self, source, text):
        if source == "girls":
            return [item[0] for item in self.repo.girl_suggestions(text)]
        if source == "studios":
            return [item[0] for item in self.repo.studio_suggestions(text)]
        return []

    def _install_delegates(self):
        for column_index, col in enumerate(self.model.columns, start=2):
            if col.kind == "choice":
                self.table.setItemDelegateForColumn(
                    column_index,
                    ChoiceDelegate(
                        self.table,
                        lambda index, source=col.source: self._choices(source),
                        self.table,
                    ),
                )
            elif col.kind == "autocomplete":
                self.table.setItemDelegateForColumn(
                    column_index,
                    AutoCompleteDelegate(
                        self.table,
                        lambda text, source=col.source: self._suggestions(source, text),
                        self.table,
                    ),
                )
            elif col.kind == "note":
                self.table.setItemDelegateForColumn(
                    column_index,
                    NoteDelegate(self.table, self.table),
                )
            elif col.kind in {"text", "color"}:
                self.table.setItemDelegateForColumn(
                    column_index,
                    TextDelegate(self.table, self.table),
                )

    def _settings_key(self, suffix):
        return f"table/{self.title}/{suffix}"

    def _load_title_overrides(self):
        raw = str(self.settings.value(self._settings_key("titles"), "") or "")
        try:
            values = json.loads(raw) if raw else {}
        except Exception:
            values = {}
        if isinstance(values, dict):
            for key, title in values.items():
                self.model.set_title_override(str(key), str(title))

    def _apply_widths_if_fresh(self):
        if self.settings.value(self._settings_key("header_state")) is not None:
            return
        self.table.setColumnWidth(0, 36)
        self.table.setColumnWidth(1, 44)
        for index, col in enumerate(self.model.columns, start=2):
            self.table.setColumnWidth(index, col.width)

    def save_header_state(self):
        if self._restoring:
            return
        self.settings.setValue(
            self._settings_key("header_state"),
            self.table.header.saveState(),
        )
        hidden = [
            str(column)
            for column in range(2, self.model.columnCount())
            if self.table.isColumnHidden(column)
        ]
        self.settings.setValue(self._settings_key("hidden"), ",".join(hidden))

    def restore_header_state(self):
        self._restoring = True
        state = self.settings.value(self._settings_key("header_state"))
        if isinstance(state, QByteArray):
            self.table.header.restoreState(state)
        hidden_raw = str(self.settings.value(self._settings_key("hidden"), "") or "")
        hidden = {
            int(value)
            for value in hidden_raw.split(",")
            if value.strip().isdigit()
        }
        for column in range(2, self.model.columnCount()):
            self.table.setColumnHidden(column, column in hidden)
        self.table.setColumnHidden(0, False)
        self.table.setColumnHidden(1, False)
        self.table.setColumnWidth(0, 36)
        self.table.setColumnWidth(1, 44)
        self.table.set_header_locked(True)
        self._restoring = False

    def header_context_menu(self, logical, global_pos):
        if self.table.header_locked or logical < 2:
            return
        col = self.model.col(logical)
        menu = QMenu(self)
        rename = menu.addAction("Přejmenovat sloupec")
        hide = menu.addAction("Skrýt sloupec")
        selected = menu.exec(global_pos)
        if selected == rename:
            current = str(self.model.headerData(logical, Qt.Horizontal, Qt.DisplayRole) or col.title)
            text, ok = QInputDialog.getText(
                self, "Přejmenovat sloupec", "Název:", text=current
            )
            if ok and text.strip():
                self.model.set_title_override(col.key, text.strip())
                self.settings.setValue(
                    self._settings_key("titles"),
                    json.dumps(self.model.title_overrides, ensure_ascii=False),
                )
        elif selected == hide:
            self.table.setColumnHidden(logical, True)
            self.save_header_state()

    def column_actions(self, menu: QMenu):
        for logical in range(2, self.model.columnCount()):
            title = str(self.model.headerData(logical, Qt.Horizontal, Qt.DisplayRole) or "")
            action = menu.addAction(title)
            action.setCheckable(True)
            action.setChecked(not self.table.isColumnHidden(logical))
            action.toggled.connect(
                lambda checked, column=logical: self._column_visibility(column, checked)
            )

    def _column_visibility(self, column, visible):
        self.table.setColumnHidden(column, not visible)
        self.save_header_state()

    def _note(self, index):
        open_note_for_table(self.table, index)
        self.refresh()

    def _web_clicked(self, index):
        pass

    def _image_clicked(self, index):
        pass

    def _tag_clicked(self, index):
        pass

    def current_source_row(self):
        index = self.table.currentIndex()
        return self.proxy.mapToSource(index) if index.isValid() else QModelIndex()

    def refresh(self):
        self.model.reload()
        self.proxy.invalidate()
        self.update_status()

    def update_status(self):
        window = self.window()
        if hasattr(window, "update_status"):
            window.update_status()

    def record_count(self):
        return self.proxy.rowCount()

    def set_row_height_level(self, level):
        self.table.set_row_height_level(level)


class GirlsPage(TablePage):
    def __init__(self, repo, favorites, settings, parent=None):
        self.favorites = bool(favorites)
        self.quick_tag = ""
        title = "Oblíbené" if favorites else "Girls"
        super().__init__(repo, title, GirlsModel(repo, favorites), settings, parent)
        self._build_top()
        self._build_toolbar()
        self.table.selectionModel().selectionChanged.connect(
            lambda *_: self._selection_changed()
        )
        self._update_top()

    def _build_top(self):
        layout = QHBoxLayout(self.top)
        layout.setContentsMargins(8, 7, 8, 7)
        layout.setSpacing(10)

        self.photo = ProfileButton(self.top)
        self.photo.setObjectName("profilePhoto")
        layout.addWidget(self.photo, 0, Qt.AlignVCenter)

        center = QWidget(self.top)
        middle = QVBoxLayout(center)
        middle.setContentsMargins(0, 0, 0, 0)
        middle.setSpacing(3)

        headline = QHBoxLayout()
        headline.setContentsMargins(0, 0, 0, 0)
        self.name = QLabel("Vyber herečku")
        self.name.setObjectName("detailName")
        self.favorite_btn = QPushButton("☆ Oblíbené")
        self.favorite_btn.setObjectName("favoriteButton")
        self.favorite_btn.setCheckable(True)
        headline.addWidget(self.name)
        headline.addWidget(self.favorite_btn)
        headline.addStretch()
        middle.addLayout(headline)

        info = QHBoxLayout()
        self.age = QLabel("<b>Věk:</b> —")
        self.occ = QLabel("<b>Počet výskytů:</b> 0")
        info.addWidget(self.age)
        info.addSpacing(12)
        info.addWidget(self.occ)
        info.addStretch()
        middle.addLayout(info)

        self.chips = FlowWidget(max_rows=2, row_height=27)
        middle.addWidget(self.chips, 1)
        layout.addWidget(center, 1, Qt.AlignTop)

        right = QVBoxLayout()
        right.setSpacing(5)
        self.links_btn = QPushButton("Odkazy")
        self.detail_btn = QPushButton("Detail")
        self.show_links_btn = QPushButton("Zobrazit odkazy")
        for button in (self.links_btn, self.detail_btn, self.show_links_btn):
            button.setFixedHeight(29)
            right.addWidget(button)
        right.addStretch()
        layout.addLayout(right)

        self.favorite_btn.clicked.connect(self._favorite_changed)
        self.links_btn.clicked.connect(self._links)
        self.detail_btn.clicked.connect(self._detail)
        self.show_links_btn.clicked.connect(self._show_links)
        self.photo.chooseRequested.connect(self._choose_photo)
        self.photo.cropRequested.connect(self._crop_photo)
        self.photo.deleteRequested.connect(self._delete_photo)

    def _build_toolbar(self):
        self.add = SplitAddButton()
        self.delete = QPushButton("Smazat")
        self.bulk = QPushButton("Hromadné akce")
        self.search = SearchBox()
        for button in (self.delete, self.bulk):
            button.setFixedHeight(BUTTON_H)

        self.toolbar_lay.addWidget(self.add)
        self.toolbar_lay.addWidget(self.delete)
        self.toolbar_lay.addWidget(self.bulk)
        self.toolbar_lay.addWidget(self.search)

        self.filters: dict[str, FilterButton] = {}
        self.filters["nationality"] = FilterButton(
            "Národnost", self._nationalities_ranked, self, overflow_after=10
        )
        self.filters["type_name"] = FilterButton("Typ", lambda: self.repo.catalog("types"), self)
        self.filters["status"] = FilterButton(
            "Stav", lambda: ["Aktivní", "Neaktivní", "Smazaná"], self
        )
        self.filters["sex"] = FilterButton(
            "Sex", lambda: ["Ano", "Ne", "Asi ne", "Asi ano", "Zjistit"], self
        )
        self.filters["nudity"] = FilterButton(
            "Nahota", lambda: ["Ano", "Ne", "Asi ne", "Asi ano", "Zjistit"], self
        )
        self.filters["face"] = FilterButton(
            "Obličej", lambda: ["Ano", "Asi ano", "Asi ne", "Ne", "Zjistit"], self
        )
        self.filters["profile"] = FilterButton(
            "Profilovka", lambda: ["Ano", "Ne"], self
        )
        for button in self.filters.values():
            self.toolbar_lay.addWidget(button)
            button.valueChanged.connect(self._filters_changed)

        self.toolbar_lay.addStretch()
        self.toolbar_lay.addWidget(self.clear)

        self.add.addRequested.connect(self._add_rows)
        self.delete.clicked.connect(self._delete)
        self.bulk.clicked.connect(self._bulk_menu)
        self.search.textChanged.connect(self._search_changed)
        self.clear.clicked.connect(self._clear_all)

        if self.favorites:
            self.add.setEnabled(False)
            self.delete.setEnabled(False)

    def _nationalities_ranked(self):
        usage = Counter(g.nationality for g in self.repo.girls(False) if g.nationality)
        all_values = list(self.repo.catalog("nationalities"))
        return sorted(all_values, key=lambda name: (-usage.get(name, 0), name.casefold()))

    def _compose_predicate(self):
        profile = self.filters["profile"].value
        quick = self.quick_tag

        def predicate(girl):
            if profile == "Ano" and not girl.profile_path:
                return False
            if profile == "Ne" and girl.profile_path:
                return False
            if quick and quick not in girl.tags:
                return False
            return True

        self.proxy.predicate = predicate if profile or quick else None

    def _filters_changed(self, *_):
        for key, button in self.filters.items():
            if key == "profile":
                continue
            self.proxy.set_filter_values(
                key, {button.value} if button.value else set()
            )
        self._compose_predicate()
        self.proxy.invalidateFilter()
        self.update_status()

    def _search_changed(self, text):
        self.proxy.set_query(text)
        self.update_status()

    def apply_quick_tag(self, tag):
        self.quick_tag = tag
        self._compose_predicate()
        self.proxy.invalidateFilter()
        self.update_status()

    def _add_rows(self, count):
        self.reset_sort()
        ids = self.repo.add_girls(count)
        self.refresh()
        if ids:
            self.table.start_edit_for_record(ids[0], 2)

    def _delete(self):
        ids = selected_source_ids(self.table)
        if not ids:
            return
        deletable = [
            row_id for row_id in ids
            if (self.repo.girl(row_id) and not self.repo.girl(row_id).locked)
        ]
        if not deletable:
            return
        if QMessageBox.question(
            self,
            "Smazat",
            f"Smazat {len(deletable)} označených odemčených řádků?",
            QMessageBox.Yes | QMessageBox.No,
        ) == QMessageBox.Yes:
            self.repo.delete_girls(deletable)
            self.refresh()

    def _bulk_menu(self):
        menu = QMenu(self)
        add_fav = menu.addAction("Přidat do Oblíbených")
        remove_fav = menu.addAction("Odebrat z Oblíbených")
        menu.addSeparator()
        links = menu.addAction("Hromadně přidat odkazy")
        selected = menu.exec(self.bulk.mapToGlobal(self.bulk.rect().bottomLeft()))
        if not selected:
            return
        ids = selected_source_ids(self.table)
        girls = [self.repo.girl(row_id) for row_id in ids]
        girls = [girl for girl in girls if girl]
        if selected == add_fav:
            for girl in girls:
                self.repo.set_favorite(girl.id, True)
            self.refresh()
        elif selected == remove_fav:
            if girls and QMessageBox.question(
                self,
                "Oblíbené",
                "Odebrat označené herečky z Oblíbených?",
                QMessageBox.Yes | QMessageBox.No,
            ) == QMessageBox.Yes:
                for girl in girls:
                    self.repo.set_favorite(girl.id, False)
                self.refresh()
        elif selected == links and girls:
            if BulkGirlLinksDialog(self.repo, girls, self).exec():
                self.refresh()

    def _selected_girl(self):
        source = self.current_source_row()
        return self.model.rows[source.row()] if source.isValid() else None

    def _selection_changed(self):
        self._update_top()

    def _favorite_changed(self, checked):
        girl = self._selected_girl()
        if not girl:
            return
        self.repo.set_favorite(girl.id, bool(checked))
        self.refresh()

    def _links(self):
        girl = self._selected_girl()
        if not girl:
            return
        GirlLinksDialog(self.repo, girl.id, self).exec()
        # Uložené odkazy lze v dialogu editovat/smazat okamžitě, proto se
        # horní panel obnoví i při zavření dialogu přes Zrušit.
        self.refresh()

    def _detail(self):
        girl = self._selected_girl()
        if girl and GirlDetailDialog(self.repo, girl.id, self).exec():
            self.refresh()

    def _show_links(self):
        girl = self._selected_girl()
        if girl:
            self.window().navigate("Odkazy", girl_filter=girl.id)

    def _profile_dir(self):
        path = data_root() / "profiles"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _choose_photo(self):
        girl = self._selected_girl()
        if not girl:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Profilová fotografie",
            "/home/jirka/Plocha",
            "Obrázky (*.png *.jpg *.jpeg *.webp *.bmp)",
        )
        if not path:
            return
        source = Path(path)
        target = self._profile_dir() / f"girl_{girl.id}{source.suffix.lower() or '.png'}"
        try:
            shutil.copy2(source, target)
            self.repo.update_girl(girl.id, "profile_path", str(target))
        except Exception as exc:
            QMessageBox.warning(self, "Obrázek", f"Obrázek se nepodařilo uložit:\n{exc}")
        self.refresh()

    def _crop_photo(self):
        girl = self._selected_girl()
        if not girl:
            return
        dialog = ScreenCropDialog(self)
        if dialog.exec() != QDialog.Accepted or dialog.result_pixmap.isNull():
            return
        target = self._profile_dir() / f"girl_{girl.id}.png"
        if dialog.result_pixmap.save(str(target), "PNG"):
            self.repo.update_girl(girl.id, "profile_path", str(target))
            self.refresh()

    def _delete_photo(self):
        girl = self._selected_girl()
        if not girl or not girl.profile_path:
            return
        if QMessageBox.question(
            self,
            "Smazat fotografii",
            "Smazat profilovou fotografii?",
            QMessageBox.Yes | QMessageBox.No,
        ) != QMessageBox.Yes:
            return
        try:
            path = Path(girl.profile_path)
            if path.is_file() and self._profile_dir() in path.parents:
                path.unlink()
        except Exception:
            pass
        self.repo.update_girl(girl.id, "profile_path", "")
        self.refresh()

    def _tag_clicked(self, index):
        source = self.proxy.mapToSource(index)
        girl = self.model.rows[source.row()]
        usage = self.repo.tag_usage()
        tags = [
            (row.name, row.color, usage.get(row.name, 0))
            for row in self.repo.catalog_rows("tags")
            if row.name
        ]
        tags.sort(key=lambda item: (-item[2], item[0].casefold()))
        anchor = self.table.viewport().mapToGlobal(
            self.table.visualRect(index).bottomLeft()
        )
        popup = TagPopup(tags, set(girl.tags), self, anchor)
        if popup.exec() == QDialog.Accepted:
            self.repo.set_tags(girl.id, popup.selected_tags())
            self.refresh()

    def _update_top(self):
        girl = self._selected_girl()
        enabled = girl is not None
        for widget in (
            self.photo, self.favorite_btn, self.links_btn, self.detail_btn, self.show_links_btn
        ):
            widget.setEnabled(enabled)

        if not girl:
            self.name.setText("Vyber herečku")
            self.age.setText("<b>Věk:</b> —")
            self.occ.setText("<b>Počet výskytů:</b> 0")
            self.favorite_btn.setChecked(False)
            self.favorite_btn.setText("☆ Oblíbené")
            self.photo.setIcon(QIcon())
            self.photo.setText("FOTKA")
            self.chips.set_items([])
            return

        self.name.setText(girl.name or "(bez jména)")
        self.age.setText(f"<b>Věk:</b> {age_display(girl.age_source) or '—'}")
        self.occ.setText(f"<b>Počet výskytů:</b> {girl.occurrences}")

        self.favorite_btn.blockSignals(True)
        self.favorite_btn.setChecked(girl.favorite)
        self.favorite_btn.setText("★ V oblíbených" if girl.favorite else "☆ Oblíbené")
        self.favorite_btn.blockSignals(False)

        self.photo.setIcon(QIcon())
        self.photo.setText("FOTKA")
        if girl.profile_path and Path(girl.profile_path).is_file():
            pixmap = QPixmap(girl.profile_path)
            if not pixmap.isNull():
                self.photo.setText("")
                self.photo.setIcon(QIcon(pixmap))
                self.photo.setIconSize(self.photo.size())

        links = self.repo.links_for_girl(girl.id)
        per_type = Counter(link.type_name for link in links if link.type_name)
        global_use = {
            str(item["name"]): int(item["distinct_girls"])
            for item in self.repo.link_types()
        }
        widgets = []
        for type_name, count in sorted(
            per_type.items(),
            key=lambda item: (-global_use.get(item[0], 0), item[0].casefold()),
        ):
            label = type_name + (f" ({count})" if count > 1 else "")
            button = ChipButton(label, type_name)
            button.setCheckable(False)
            button.clicked.connect(
                lambda checked=False, gid=girl.id, name=type_name:
                    self._open_girl_link_type(gid, name)
            )
            widgets.append(button)
        self.chips.set_items(widgets)

    def _open_girl_link_type(self, girl_id, type_name):
        for link in self.repo.links_for_girl(girl_id):
            if link.type_name == type_name and link.url.strip():
                QDesktopServices.openUrl(QUrl.fromUserInput(link.url))

    def _clear_all(self):
        self.search.clear()
        for button in self.filters.values():
            button.set_value("", emit=False)
        self.quick_tag = ""
        self.proxy.clear_filters()
        self.update_status()

    def status_extra(self):
        ages = []
        for row, girl in enumerate(self.model.rows):
            if not self.proxy.accepts_without_query(row):
                continue
            try:
                age = int(age_display(girl.age_source))
            except Exception:
                continue
            if 1 <= age <= 100:
                ages.append(age)
        if not ages:
            return "Průměrný věk: —"
        value = f"{sum(ages) / len(ages):.1f}".replace(".", ",")
        return f"Průměrný věk: {value}"

    def refresh(self):
        current = self._selected_girl()
        current_id = current.id if current else None
        super().refresh()
        if current_id is not None:
            for row in range(self.proxy.rowCount()):
                source = self.proxy.mapToSource(self.proxy.index(row, 0))
                if self.model.record_id(source.row()) == current_id:
                    self.table.selectRow(row)
                    break
        self._update_top()


class VideosPage(TablePage):
    def __init__(self, repo, super_only, settings, parent=None):
        self.super_only = bool(super_only)
        title = "Super" if super_only else "Videa"
        model = VideosModel(repo, super_only)
        super().__init__(repo, title, model, settings, parent)
        model.unknown_girl = self._unknown_girl
        model.unknown_studio = self._unknown_studio
        self.chip_mode = "Studia"
        self._chip_selected: set[str] = set()
        self._build_top()
        self._build_toolbar()
        self._refresh_chips()

    def _unknown_girl(self, text):
        if QMessageBox.question(
            self,
            "Nová herečka",
            f"'{text}' není v Girls. Přidat jako nový záznam?",
            QMessageBox.Yes | QMessageBox.No,
        ) == QMessageBox.Yes:
            girl_id = self.repo.add_girl(text)
            window = self.window()
            if hasattr(window, "pages") and "Girls" in window.pages:
                window.pages["Girls"].reset_sort()
            return girl_id
        return None

    def _unknown_studio(self, text):
        if QMessageBox.question(
            self,
            "Nové studio",
            f"'{text}' není ve Studiích. Přidat jako nový záznam?",
            QMessageBox.Yes | QMessageBox.No,
        ) == QMessageBox.Yes:
            studio_id = self.repo.add_studio(text)
            window = self.window()
            if hasattr(window, "pages") and "Studia" in window.pages:
                window.pages["Studia"].reset_sort()
            return self.repo.studio_by_name(text)
        return None

    def _build_top(self):
        layout = QVBoxLayout(self.top)
        layout.setContentsMargins(7, 4, 7, 3)
        layout.setSpacing(3)

        head = QHBoxLayout()
        label = QLabel(self.title)
        label.setStyleSheet("font-size:20px;font-weight:700")
        head.addWidget(label)
        self.studio_mode = QPushButton("Studia")
        self.girl_mode = QPushButton("Herečky")
        self.studio_mode.setCheckable(True)
        self.girl_mode.setCheckable(True)
        self.studio_mode.setChecked(True)
        head.addWidget(self.studio_mode)
        head.addWidget(self.girl_mode)
        head.addStretch()
        self.detail_btn = QPushButton("Detail")
        head.addWidget(self.detail_btn)
        layout.addLayout(head)

        self.chips = FlowWidget(max_rows=3, row_height=27)
        layout.addWidget(self.chips, 1)

        self.studio_mode.clicked.connect(lambda: self._set_chip_mode("Studia"))
        self.girl_mode.clicked.connect(lambda: self._set_chip_mode("Herečky"))
        self.detail_btn.clicked.connect(self._detail)

    def _set_chip_mode(self, mode):
        self.chip_mode = mode
        self.studio_mode.setChecked(mode == "Studia")
        self.girl_mode.setChecked(mode == "Herečky")
        self._chip_selected.clear()
        self._refresh_chips()
        self._apply_chip_filter()

    def _refresh_chips(self):
        if self.chip_mode == "Studia":
            items = [
                (studio.name, studio.occurrences)
                for studio in sorted(
                    self.repo.studios(),
                    key=lambda value: (-value.occurrences, value.name.casefold()),
                )
                if studio.name
            ]
        else:
            items = [
                (girl.name, girl.occurrences)
                for girl in sorted(
                    self.repo.girls(False),
                    key=lambda value: (-value.occurrences, value.name.casefold()),
                )
                if girl.name
            ]
        widgets = []
        for name, count in items:
            button = ChipButton(f"{name} ({count})", name)
            button.setChecked(name in self._chip_selected)
            button.clicked.connect(
                lambda checked=False, value=name: self._chip_click(value, checked)
            )
            widgets.append(button)
        self.chips.set_items(widgets)

    def _chip_click(self, name, checked):
        multi = bool(
            QApplication.keyboardModifiers() & (Qt.ControlModifier | Qt.ShiftModifier)
        )
        if not multi:
            self._chip_selected = {name}
        elif checked:
            self._chip_selected.add(name)
        else:
            self._chip_selected.discard(name)
        self._refresh_chips()
        self._apply_chip_filter()

    def _apply_chip_filter(self):
        values = set(self._chip_selected)
        if not values:
            self.proxy.predicate = None
        elif self.chip_mode == "Studia":
            self.proxy.predicate = lambda video: video.studio_name in values
        else:
            self.proxy.predicate = lambda video: any(
                participant[1] in values for participant in video.participants
            )
        self.proxy.invalidateFilter()
        self.update_status()

    def _build_toolbar(self):
        self.add = SplitAddButton()
        self.delete = QPushButton("Smazat")
        self.super_btn = QPushButton(
            "Odebrat ze SUPER" if self.super_only else "Přidat do SUPER"
        )
        self.search = SearchBox()
        self.studio_filter = ScrollFilterButton(
            "Studio",
            lambda: [
                studio.name
                for studio in sorted(
                    self.repo.studios(),
                    key=lambda value: (-value.occurrences, value.name.casefold()),
                )
                if studio.name
            ],
            self,
        )
        self.state_filter = FilterButton("Stav", lambda: self.repo.catalog("states"), self)
        self.quality_filter = FilterButton(
            "Kvalita", lambda: self.repo.catalog("qualities"), self
        )

        for button in (self.delete, self.super_btn):
            button.setFixedHeight(BUTTON_H)

        self.toolbar_lay.addWidget(self.add)
        self.toolbar_lay.addWidget(self.delete)
        self.toolbar_lay.addWidget(self.super_btn)
        self.toolbar_lay.addWidget(self.search)
        self.toolbar_lay.addWidget(self.studio_filter)
        self.toolbar_lay.addWidget(self.state_filter)
        self.toolbar_lay.addWidget(self.quality_filter)
        self.toolbar_lay.addStretch()
        self.toolbar_lay.addWidget(self.clear)

        self.add.addRequested.connect(self._add_rows)
        self.delete.clicked.connect(self._delete)
        self.super_btn.clicked.connect(self._super_action)
        self.search.textChanged.connect(self._search_changed)
        self.studio_filter.valueChanged.connect(self._filters_changed)
        self.state_filter.valueChanged.connect(self._filters_changed)
        self.quality_filter.valueChanged.connect(self._filters_changed)
        self.clear.clicked.connect(self._clear_all)

    def _search_changed(self, text):
        self.proxy.set_query(text)
        self.update_status()

    def _filters_changed(self, *_):
        self.proxy.set_filter_values(
            "studio_name",
            {self.studio_filter.value} if self.studio_filter.value else set(),
        )
        self.proxy.set_filter_values(
            "state", {self.state_filter.value} if self.state_filter.value else set()
        )
        self.proxy.set_filter_values(
            "quality",
            {self.quality_filter.value} if self.quality_filter.value else set(),
        )
        self.update_status()

    def _add_rows(self, count):
        self.reset_sort()
        ids = [self.repo.add_video() for _ in range(int(count))]
        self.refresh()
        if ids:
            self.table.start_edit_for_record(ids[0], 2)

    def _delete(self):
        ids = selected_source_ids(self.table)
        if not ids:
            return
        deletable = [
            row_id for row_id in ids
            if (self.repo.video(row_id) and not self.repo.video(row_id).locked)
        ]
        if not deletable:
            return
        if QMessageBox.question(
            self,
            "Smazat",
            f"Smazat {len(deletable)} označených videí?",
            QMessageBox.Yes | QMessageBox.No,
        ) == QMessageBox.Yes:
            self.repo.delete_videos(deletable)
            self.refresh()

    def _super_action(self):
        ids = selected_source_ids(self.table)
        if not ids:
            return
        if self.super_only:
            if QMessageBox.question(
                self,
                "SUPER",
                "Odebrat označená videa ze SUPER?",
                QMessageBox.Yes | QMessageBox.No,
            ) != QMessageBox.Yes:
                return
            self.repo.set_video_super(ids, False)
        else:
            self.repo.set_video_super(ids, True)
        self.refresh()

    def _detail(self):
        source = self.current_source_row()
        if source.isValid():
            video_id = self.model.record_id(source.row())
            if VideoDetailDialog(self.repo, video_id, self).exec():
                self.refresh()

    def _clear_all(self):
        self.search.clear()
        self.studio_filter.set_value("", emit=False)
        self.state_filter.set_value("", emit=False)
        self.quality_filter.set_value("", emit=False)
        self._chip_selected.clear()
        self.proxy.clear_filters()
        self._refresh_chips()
        self.update_status()

    def refresh(self):
        super().refresh()
        self._refresh_chips()
        self._apply_chip_filter()


class StudiosPage(TablePage):
    def __init__(self, repo, settings, parent=None):
        super().__init__(repo, "Studia", StudiosModel(repo), settings, parent)
        top = QVBoxLayout(self.top)
        label = QLabel("Studia")
        label.setStyleSheet("font-size:20px;font-weight:700")
        top.addWidget(label)
        top.addStretch()
        self._build_toolbar()

    def _build_toolbar(self):
        self.add = SplitAddButton()
        self.delete = QPushButton("Smazat")
        self.delete.setFixedHeight(BUTTON_H)
        self.search = SearchBox()
        self.toolbar_lay.addWidget(self.add)
        self.toolbar_lay.addWidget(self.delete)
        self.toolbar_lay.addWidget(self.search)
        self.toolbar_lay.addStretch()
        self.toolbar_lay.addWidget(self.clear)

        self.add.addRequested.connect(self._add)
        self.delete.clicked.connect(self._delete)
        self.search.textChanged.connect(self._search_changed)
        self.clear.clicked.connect(self._clear_all)

    def _search_changed(self, text):
        self.proxy.set_query(text)
        self.update_status()

    def _add(self, count):
        self.reset_sort()
        ids = [self.repo.add_studio("") for _ in range(int(count))]
        self.refresh()
        if ids:
            self.table.start_edit_for_record(ids[0], 2)

    def _delete(self):
        ids = selected_source_ids(self.table)
        if not ids:
            return
        if QMessageBox.question(
            self,
            "Smazat",
            f"Smazat označená odemčená studia?",
            QMessageBox.Yes | QMessageBox.No,
        ) == QMessageBox.Yes:
            self.repo.delete_studios(ids)
            self.refresh()

    def _clear_all(self):
        self.search.clear()
        self.proxy.clear_filters()
        self.update_status()


class LinksPage(TablePage):
    CATEGORY_MAP = {
        "Vše": None,
        "Sítě": "Síť",
        "Zdroje": "Zdroj",
        "Rozcestníky": "Rozcestník",
    }
    CHIPS_PER_PAGE = 15

    def __init__(self, repo, settings, parent=None):
        model = LinksModel(repo)
        super().__init__(repo, "Odkazy", model, settings, parent)
        model.unknown_girl = self._unknown_girl
        self.category = "Vše"
        self._chip_selected: set[str] = set()
        self.external_girl_filter: int | None = None
        self.chip_page = 0
        self._build_top()
        self._build_toolbar()
        self._refresh_chips()
        self.table.selectionModel().selectionChanged.connect(
            lambda *_: self._update_show_button()
        )

    def _unknown_girl(self, text):
        if QMessageBox.question(
            self,
            "Nová herečka",
            f"'{text}' není v Girls. Přidat jako nový záznam?",
            QMessageBox.Yes | QMessageBox.No,
        ) == QMessageBox.Yes:
            girl_id = self.repo.add_girl(text)
            if hasattr(self.window(), "pages"):
                self.window().pages["Girls"].reset_sort()
            return girl_id
        return None

    def _build_top(self):
        layout = QHBoxLayout(self.top)
        layout.setContentsMargins(7, 4, 7, 4)
        layout.setSpacing(8)

        left = QVBoxLayout()
        left.setSpacing(3)
        head = QHBoxLayout()
        title = QLabel("Odkazy")
        title.setStyleSheet("font-size:20px;font-weight:700")
        head.addWidget(title)
        self.tabs: dict[str, QPushButton] = {}
        for name in ("Vše", "Sítě", "Zdroje", "Rozcestníky"):
            button = QPushButton(name)
            button.setCheckable(True)
            button.setChecked(name == "Vše")
            button.clicked.connect(
                lambda checked=False, value=name: self._set_category(value)
            )
            head.addWidget(button)
            self.tabs[name] = button

        self.prev_page = QPushButton("‹")
        self.next_page = QPushButton("›")
        self.page_label = QLabel("1/1")
        self.prev_page.setFixedWidth(28)
        self.next_page.setFixedWidth(28)
        head.addSpacing(8)
        head.addWidget(self.prev_page)
        head.addWidget(self.page_label)
        head.addWidget(self.next_page)
        head.addStretch()
        self.girl_filter_label = QLabel("")
        self.girl_filter_label.setStyleSheet("color:#245b8d;font-weight:700")
        head.addWidget(self.girl_filter_label)
        left.addLayout(head)

        self.chips = FlowWidget(max_rows=3, row_height=27)
        left.addWidget(self.chips, 1)
        layout.addLayout(left, 1)

        right = QVBoxLayout()
        right.setSpacing(4)
        self.bulk_add = QPushButton("Přidat odkazy")
        self.catalog = QPushButton("Seznam položek")
        self.visible = QPushButton("Viditelné filtry…")
        self.export = QPushButton("Exportovat odkazy")
        self.show = QPushButton("Zobrazit odkazy")
        for button in (self.bulk_add, self.catalog, self.visible, self.export):
            button.setFixedHeight(25)
            right.addWidget(button)
        right.addStretch()
        self.show.setFixedHeight(25)
        right.addWidget(self.show)
        layout.addLayout(right)

        self.prev_page.clicked.connect(lambda: self._change_page(-1))
        self.next_page.clicked.connect(lambda: self._change_page(1))
        self.bulk_add.clicked.connect(self._bulk_add)
        self.catalog.clicked.connect(self._catalog)
        self.visible.clicked.connect(self._visible)
        self.export.clicked.connect(self._export)
        self.show.clicked.connect(self._show_selected)
        self._update_show_button()

    def _build_toolbar(self):
        self.add = SplitAddButton()
        self.remove = QPushButton("Odebrat")
        self.bulk = QPushButton("Hromadné akce")
        self.search = SearchBox()
        self.image_filter = FilterButton(
            "Obrázek", lambda: ["Má obrázek", "Bez obrázku"], self
        )
        for button in (self.remove, self.bulk):
            button.setFixedHeight(BUTTON_H)

        self.toolbar_lay.addWidget(self.add)
        self.toolbar_lay.addWidget(self.remove)
        self.toolbar_lay.addWidget(self.bulk)
        self.toolbar_lay.addWidget(self.search)
        self.toolbar_lay.addWidget(self.image_filter)
        self.toolbar_lay.addStretch()
        self.toolbar_lay.addWidget(self.clear)

        self.add.addRequested.connect(self._add_rows)
        self.remove.clicked.connect(self._remove)
        self.bulk.clicked.connect(self._bulk_actions)
        self.search.textChanged.connect(self._search_changed)
        self.image_filter.valueChanged.connect(self._apply_filters)
        self.clear.clicked.connect(self._clear_all)

    def _set_category(self, name):
        self.category = name
        self.chip_page = 0
        for tab_name, button in self.tabs.items():
            button.setChecked(tab_name == name)
        self._chip_selected.clear()
        self._refresh_chips()
        self._apply_filters()

    def _available_link_types(self):
        category = self.CATEGORY_MAP[self.category]
        values = []
        for item in self.repo.link_types():
            if category and item["category"] != category:
                continue
            if self.category == "Vše" and not item["visible_all"]:
                continue
            if self.category != "Vše" and not item["visible_category"]:
                continue
            values.append(item)
        return values

    def _refresh_chips(self):
        values = self._available_link_types()
        pages = max(1, (len(values) + self.CHIPS_PER_PAGE - 1) // self.CHIPS_PER_PAGE)
        self.chip_page = max(0, min(self.chip_page, pages - 1))
        start = self.chip_page * self.CHIPS_PER_PAGE
        visible = values[start : start + self.CHIPS_PER_PAGE]

        widgets = []
        for item in visible:
            name = str(item["name"])
            button = ChipButton(f"{name} ({item['distinct_girls']})", name)
            button.setChecked(name in self._chip_selected)
            button.clicked.connect(
                lambda checked=False, value=name: self._chip_click(value, checked)
            )
            widgets.append(button)
        self.chips.set_items(widgets)
        self.page_label.setText(f"{self.chip_page + 1}/{pages}")
        self.prev_page.setEnabled(self.chip_page > 0)
        self.next_page.setEnabled(self.chip_page + 1 < pages)

    def _change_page(self, delta):
        self.chip_page += int(delta)
        self._refresh_chips()

    def _chip_click(self, name, checked):
        multi = bool(
            QApplication.keyboardModifiers() & (Qt.ControlModifier | Qt.ShiftModifier)
        )
        if not multi:
            self._chip_selected = {name}
        elif checked:
            self._chip_selected.add(name)
        else:
            self._chip_selected.discard(name)
        self._refresh_chips()
        self._apply_filters()

    def _search_changed(self, text):
        self.proxy.set_query(text)
        self.update_status()

    def _apply_filters(self, *_):
        category = self.CATEGORY_MAP[self.category]
        chips = set(self._chip_selected)
        girl_filter = self.external_girl_filter
        image_value = self.image_filter.value

        self.proxy.predicate = lambda link: (
            (not category or link.category == category)
            and (not chips or link.type_name in chips)
            and (girl_filter is None or link.girl_id == girl_filter)
            and (image_value != "Má obrázek" or bool(link.last_image))
            and (image_value != "Bez obrázku" or not bool(link.last_image))
        )
        self.proxy.invalidateFilter()
        self.update_status()

    def set_girl_filter(self, girl_id):
        self.external_girl_filter = int(girl_id) if girl_id is not None else None
        if self.external_girl_filter is not None:
            # "Zobrazit odkazy" z Girls má ukázat všechny odkazy dané herečky,
            # proto nesmí zůstat viset staré hledání, kategorie ani rychlé filtry.
            self.search.clear()
            self.image_filter.set_value("", emit=False)
            self.category = "Vše"
            self.chip_page = 0
            self._chip_selected.clear()
            for name, button in self.tabs.items():
                button.setChecked(name == "Vše")
            self.proxy.clear_filters()
            self._refresh_chips()
        girl = self.repo.girl(self.external_girl_filter) if self.external_girl_filter else None
        self.girl_filter_label.setText(
            f"Herečka: {girl.name}" if girl else ""
        )
        self._apply_filters()

    def _add_rows(self, count):
        self.reset_sort()
        ids = [self.repo.add_link(is_new=True) for _ in range(int(count))]
        self.refresh()
        if ids:
            self.table.start_edit_for_record(ids[0], 2)

    def _remove(self):
        ids = selected_source_ids(self.table)
        if not ids:
            return
        if QMessageBox.question(
            self,
            "Odebrat",
            f"Odebrat označené odemčené odkazy?",
            QMessageBox.Yes | QMessageBox.No,
        ) == QMessageBox.Yes:
            self.repo.delete_links(ids)
            self.refresh()

    def _bulk_actions(self):
        menu = QMenu(self)
        active = menu.addAction("Nastavit Akt.")
        inactive = menu.addAction("Nastavit Neakt.")
        clear_check = menu.addAction("Vymazat Kontrolu")
        clear_downloaded = menu.addAction("Vymazat Staženo")
        selected = menu.exec(self.bulk.mapToGlobal(self.bulk.rect().bottomLeft()))
        ids = selected_source_ids(self.table)
        if not selected or not ids:
            return
        for link_id in ids:
            if selected == active:
                self.repo.update_link(link_id, "active", "Akt.")
            elif selected == inactive:
                self.repo.update_link(link_id, "active", "Neakt.")
            elif selected == clear_check:
                self.repo.update_link(link_id, "check_value", "")
            elif selected == clear_downloaded:
                self.repo.update_link(link_id, "downloaded", "")
        self.refresh()

    def _bulk_add(self):
        if BulkLinksDialog(self.repo, self).exec():
            self.refresh()

    def _catalog(self):
        if LinkCatalogDialog(self.repo, self).exec():
            self.refresh()

    def _visible(self):
        if VisibleLinkFiltersDialog(self.repo, self.category, self).exec():
            self._refresh_chips()

    def visible_links(self):
        result = []
        for row in range(self.proxy.rowCount()):
            source = self.proxy.mapToSource(self.proxy.index(row, 0))
            result.append(self.model.rows[source.row()])
        return result

    def _export(self):
        ExportLinksDialog(self.repo, self.visible_links(), self).exec()

    def _update_show_button(self):
        self.show.setEnabled(bool(selected_source_ids(self.table)))

    def _show_selected(self):
        ids = set(selected_source_ids(self.table))
        for link in self.repo.links():
            if link.id in ids and link.url.strip():
                QDesktopServices.openUrl(QUrl.fromUserInput(link.url))

    def _web_clicked(self, index):
        source = self.proxy.mapToSource(index)
        link = self.model.rows[source.row()]
        if link.url.strip():
            QDesktopServices.openUrl(QUrl.fromUserInput(link.url))

    def _image_clicked(self, index):
        source = self.proxy.mapToSource(index)
        link = self.model.rows[source.row()]
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Poslední obrázek",
            "/home/jirka/Plocha",
            "Obrázky (*.png *.jpg *.jpeg *.webp *.bmp)",
        )
        if path:
            self.repo.update_link(link.id, "last_image", path)
            self.refresh()

    def _clear_all(self):
        self.search.clear()
        self.image_filter.set_value("", emit=False)
        self.category = "Vše"
        for name, button in self.tabs.items():
            button.setChecked(name == "Vše")
        self.chip_page = 0
        self._chip_selected.clear()
        self.external_girl_filter = None
        self.girl_filter_label.setText("")
        self.proxy.clear_filters()
        self._refresh_chips()
        self._apply_filters()

    def refresh(self):
        super().refresh()
        self._refresh_chips()
        self._apply_filters()


class HelperPage(TablePage):
    def __init__(self, repo, title, kind, settings, with_color=False, parent=None):
        self.kind = kind
        model = CatalogModel(repo, kind, with_color)
        super().__init__(repo, title, model, settings, parent)

        top = QVBoxLayout(self.top)
        label = QLabel(title)
        label.setStyleSheet("font-size:20px;font-weight:700")
        top.addWidget(label)
        top.addStretch()

        self.add = QPushButton("Přidat")
        self.add.setFixedHeight(BUTTON_H)
        self.delete = QPushButton("Smazat")
        self.delete.setFixedHeight(BUTTON_H)
        self.search = SearchBox()
        self.toolbar_lay.addWidget(self.add)
        self.toolbar_lay.addWidget(self.delete)
        self.toolbar_lay.addWidget(self.search)
        self.toolbar_lay.addStretch()
        self.toolbar_lay.addWidget(self.clear)

        self.add.clicked.connect(self._add)
        self.delete.clicked.connect(self._delete)
        self.search.textChanged.connect(self._search_changed)
        self.clear.clicked.connect(self._clear_all)

    def _search_changed(self, text):
        self.proxy.set_query(text)
        self.update_status()

    def _add(self):
        self.reset_sort()
        row_id = self.repo.add_catalog(self.kind, "")
        self.refresh()
        self.table.start_edit_for_record(row_id, 2)

    def _delete(self):
        ids = selected_source_ids(self.table)
        if not ids:
            return
        if QMessageBox.question(
            self,
            "Smazat",
            "Smazat označené odemčené položky?",
            QMessageBox.Yes | QMessageBox.No,
        ) != QMessageBox.Yes:
            return
        for row_id in ids:
            self.repo.delete_catalog(row_id)
        self.refresh()

    def _clear_all(self):
        self.search.clear()
        self.proxy.clear_filters()
        self.update_status()


class MainWindow(QMainWindow):
    def __init__(self, repo: Repository):
        super().__init__()
        self.repo = repo
        self.settings = QSettings("Latflix", "Latflix21")
        self.current_section = ""
        self.top_visible = bool(int(self.settings.value("view/top_visible", 1)))
        self.row_level = max(1, min(5, int(self.settings.value("table/row_level", 1))))

        self.setWindowTitle(APP_NAME)
        self.resize(1500, 880)
        self.setMinimumSize(950, 580)
        self._build_ui()
        self._build_menu()
        self._style()
        self._refresh_quick_tags()
        self.navigate("Přehled")

    def _build_ui(self):
        self.sidebar = Sidebar(self)
        self.stack = QStackedWidget(self)

        host = QWidget(self)
        layout = QHBoxLayout(host)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(host)

        self.pages = {
            "Přehled": OverviewPage(self.repo, self.navigate),
            "Girls": GirlsPage(self.repo, False, self.settings),
            "Oblíbené": GirlsPage(self.repo, True, self.settings),
            "Odkazy": LinksPage(self.repo, self.settings),
            "Videa": VideosPage(self.repo, False, self.settings),
            "Super": VideosPage(self.repo, True, self.settings),
            "Studia": StudiosPage(self.repo, self.settings),
            "Stavy": HelperPage(self.repo, "Stavy", "states", self.settings),
            "Kvality": HelperPage(self.repo, "Kvality", "qualities", self.settings),
            "Tagy": HelperPage(self.repo, "Tagy", "tags", self.settings, with_color=True),
            "Typy": HelperPage(self.repo, "Typy", "types", self.settings),
            "Národnosti": HelperPage(self.repo, "Národnosti", "nationalities", self.settings),
        }
        for page in self.pages.values():
            self.stack.addWidget(page)
            if isinstance(page, TablePage):
                page.set_row_height_level(self.row_level)
                page.set_top_visible(self.top_visible)

        self.sidebar.sectionRequested.connect(self.navigate)
        self.sidebar.quickTagRequested.connect(self._quick_tag)

        self._build_status()

    def _build_status(self):
        status = QStatusBar(self)
        self.setStatusBar(status)
        self.count_label = QLabel("")
        self.extra_label = QLabel("")
        self.row_level_label = QLabel(str(self.row_level))
        self.build_label = QLabel(f"Latflix 2.1  v{__version__}")
        self.build_label.setObjectName("buildLabel")

        status.addWidget(self.count_label)
        status.addWidget(self.extra_label, 1)
        status.addPermanentWidget(QLabel("Velikost řádků:"))
        minus = QPushButton("−")
        plus = QPushButton("+")
        minus.setFixedSize(28, 24)
        plus.setFixedSize(28, 24)
        minus.clicked.connect(lambda: self.change_row_level(-1))
        plus.clicked.connect(lambda: self.change_row_level(1))
        status.addPermanentWidget(minus)
        status.addPermanentWidget(self.row_level_label)
        status.addPermanentWidget(plus)
        status.addPermanentWidget(self.build_label)

    def _build_menu(self):
        file_menu = self.menuBar().addMenu("Soubor")
        import_action = file_menu.addAction("Importovat data z Latflix 2.0…")
        import_action.triggered.connect(self.import_lf2)
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Konec")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)

        edit_menu = self.menuBar().addMenu("Úpravy")
        edit_menu.addAction("Vyčistit filtry", self.clear_current_filters)

        tools_menu = self.menuBar().addMenu("Nástroje")
        tools_menu.addAction("Importovat data z Latflix 2.0…", self.import_lf2)

        self.view_menu = self.menuBar().addMenu("Zobrazení")
        self.sidebar_action = self.view_menu.addAction("Levé menu")
        self.sidebar_action.setCheckable(True)
        self.sidebar_action.setChecked(True)
        self.sidebar_action.triggered.connect(
            lambda checked: self.sidebar.set_collapsed(not checked)
        )
        self.sidebar.collapsedChanged.connect(self._sidebar_collapsed_changed)
        self.top_action = self.view_menu.addAction("Horní pracovní panel")
        self.top_action.setCheckable(True)
        self.top_action.setChecked(self.top_visible)
        self.top_action.triggered.connect(self.set_top_visible)
        self.columns_menu = self.view_menu.addMenu("Sloupce")
        self.columns_menu.aboutToShow.connect(self.rebuild_columns_menu)

        self.menuBar().addMenu("Nastavení")

        help_menu = self.menuBar().addMenu("Nápověda")
        help_menu.addAction(
            "O aplikaci",
            lambda: QMessageBox.information(
                self,
                "Latflix 2.1",
                "Latflix 2.1\n\nČistá model/view verze podle kompletní specifikace.",
            ),
        )

    def _style(self):
        self.setStyleSheet(
            """
            QMainWindow,QWidget{background:#efefef;color:#202020;font-size:13px;}
            QWidget#sidebarPanel{background:#e9e9e9;border-right:1px solid #aaa;}
            QPushButton#categoryButton{
                text-align:left;padding:0 8px;border:1px solid #aaa;
                border-radius:3px;background:#f8f8f8;
            }
            QPushButton#categoryButton:hover{background:#edf3f8;}
            QPushButton#categoryButton:checked{
                background:#dce8f2;border-color:#7f9db8;font-weight:700;
            }
            QPushButton#quickFilterButton{
                text-align:left;padding:0 9px;border:1px solid transparent;background:transparent;
            }
            QPushButton#quickFilterButton:hover{background:#e0e8ef;border-color:#b7c4cf;}
            QLabel#detailName{font-size:21px;font-weight:700;background:transparent;}
            QPushButton#favoriteButton:checked{
                background:#fff1a8;color:#806000;border-color:#d0aa21;
            }
            QPushButton#profilePhoto{background:#e5e5e5;border:1px solid #aaa;font-weight:700;}
            QPushButton{
                padding:0 8px;border:1px solid #aaa;border-radius:3px;background:#fafafa;
            }
            QPushButton:hover{background:#e7f0f8;}
            QPushButton:disabled{background:#e2e2e2;color:#929292;}
            QLineEdit,QComboBox,QTextEdit{
                background:white;border:1px solid #aaa;border-radius:2px;padding:3px 6px;
            }
            QLabel#buildLabel{
                padding:2px 7px;border:1px solid #aaa;background:#e5e5e5;font-weight:700;
            }
            """
        )

    def _sidebar_collapsed_changed(self, collapsed: bool):
        self.sidebar_action.blockSignals(True)
        self.sidebar_action.setChecked(not collapsed)
        self.sidebar_action.blockSignals(False)

    def _refresh_quick_tags(self):
        usage = self.repo.tag_usage()
        ranked = sorted(usage.items(), key=lambda item: (-item[1], item[0].casefold()))
        self.sidebar.set_quick_tags([name for name, _ in ranked[:5]])

    def _quick_tag(self, tag):
        self.navigate("Girls")
        self.pages["Girls"].apply_quick_tag(tag)

    def navigate(self, name: str, girl_filter=None):
        if name not in self.pages:
            return

        if self.current_section and self.current_section != name:
            current = self.pages[self.current_section]
            if isinstance(current, TablePage):
                current.save_header_state()
            self.repo.cleanup_blank_new_rows()

        self.current_section = name
        page = self.pages[name]
        if name == "Odkazy":
            if girl_filter is None:
                page.set_girl_filter(None)
            else:
                page.set_girl_filter(girl_filter)
        page.refresh()
        if isinstance(page, TablePage):
            page.set_top_visible(self.top_visible)
        self.stack.setCurrentWidget(page)
        self.sidebar.set_active(name)
        self.setWindowTitle(f"{APP_NAME} – {name}")
        self._refresh_quick_tags()
        self.update_status()

    def current_page(self):
        return self.pages.get(self.current_section)

    def update_status(self):
        page = self.current_page()
        if page is None or self.current_section == "Přehled":
            self.count_label.setText("")
            self.extra_label.setText("")
            return
        count = page.record_count()
        self.count_label.setText(f"Záznamů: {count}" if count is not None else "")
        self.extra_label.setText(page.status_extra())

    def change_row_level(self, delta):
        self.row_level = max(1, min(5, self.row_level + int(delta)))
        self.row_level_label.setText(str(self.row_level))
        self.settings.setValue("table/row_level", self.row_level)
        for page in self.pages.values():
            if isinstance(page, TablePage):
                page.set_row_height_level(self.row_level)

    def set_top_visible(self, visible):
        self.top_visible = bool(visible)
        self.settings.setValue("view/top_visible", int(self.top_visible))
        for page in self.pages.values():
            if isinstance(page, TablePage):
                page.set_top_visible(self.top_visible)

    def rebuild_columns_menu(self):
        self.columns_menu.clear()
        page = self.current_page()
        if isinstance(page, TablePage):
            page.column_actions(self.columns_menu)
        else:
            action = self.columns_menu.addAction("Tato sekce nemá tabulkové sloupce")
            action.setEnabled(False)

    def clear_current_filters(self):
        page = self.current_page()
        if hasattr(page, "_clear_all"):
            page._clear_all()

    def import_lf2(self):
        if QMessageBox.question(
            self,
            "Import Latflix 2.0",
            "Importovat dostupná data z předchozích tabulek lf2_* do Latflixu 2.1?\n"
            "Import se nespouští automaticky a provede se pouze jednou.",
            QMessageBox.Yes | QMessageBox.No,
        ) != QMessageBox.Yes:
            return
        result = self.repo.import_from_lf2()
        if result.get("already_done"):
            QMessageBox.information(self, "Import", "Import už byl dříve proveden.")
        elif result.get("missing_source"):
            QMessageBox.information(self, "Import", "V databázi nejsou nalezené tabulky lf2_*.")
        else:
            QMessageBox.information(
                self,
                "Import",
                f"Importováno: Girls {result.get('girls',0)}, "
                f"Odkazy {result.get('links',0)}, katalogy {result.get('catalog',0)}.",
            )
        for page in self.pages.values():
            page.refresh()
        self._refresh_quick_tags()
        self.update_status()

    def closeEvent(self, event):
        page = self.current_page()
        if isinstance(page, TablePage):
            page.save_header_state()
        self.repo.cleanup_blank_new_rows()
        event.accept()
