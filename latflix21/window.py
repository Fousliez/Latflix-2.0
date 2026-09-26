from __future__ import annotations

from collections import Counter

from PySide6.QtCore import QModelIndex, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDialog, QFormLayout, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QMainWindow, QMenu, QMessageBox, QPushButton, QStackedWidget, QStatusBar,
    QVBoxLayout, QWidget, QInputDialog,
)

from .config import APP_NAME
from .db import Repository
from .dialogs import (
    BulkLinksDialog, ExportLinksDialog, GirlDetailDialog, LinkCatalogDialog,
    TagsDialog, VideoDetailDialog, VisibleLinkFiltersDialog,
)
from .models import BaseModel, Col, GirlsModel, LinksModel, SmartProxy, StudiosModel, VideosModel
from .widgets import (
    AutoCompleteDelegate, ChoiceDelegate, ChipButton, DataTableView, FlowWidget,
    SearchBox, SplitAddButton, TextDelegate, open_note_for_table, selected_source_ids,
)

BUTTON_H = 30
TOP_PANEL_H = 136


class Sidebar(QWidget):
    sectionRequested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(148)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self.collapse = QPushButton("◀")
        self.collapse.setFixedHeight(28)
        layout.addWidget(self.collapse)

        self.buttons = {}
        for name in ("Přehled", "Girls", "Oblíbené", "Odkazy", "Videa", "Super", "Studia"):
            button = QPushButton(name)
            button.setCheckable(True)
            button.setFixedHeight(33)
            button.clicked.connect(
                lambda checked=False, section=name: self.sectionRequested.emit(section)
            )
            layout.addWidget(button)
            self.buttons[name] = button

        layout.addStretch()

        for name in ("Stavy", "Kvality", "Tagy", "Typy", "Národnosti"):
            button = QPushButton(name)
            button.setCheckable(True)
            button.setFixedHeight(31)
            button.clicked.connect(
                lambda checked=False, section=name: self.sectionRequested.emit(section)
            )
            layout.addWidget(button)
            self.buttons[name] = button

    def set_active(self, name):
        for section, button in self.buttons.items():
            button.setChecked(section == name)


class BasePage(QWidget):
    def __init__(self, repo: Repository, title: str, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.title = title
        self.outer = QVBoxLayout(self)
        self.outer.setContentsMargins(8, 6, 8, 5)
        self.outer.setSpacing(5)

    def clear_filters(self):
        pass

    def refresh(self):
        pass


class OverviewCard(QFrame):
    clicked = Signal(str)

    def __init__(self, title, count, subtitle, parent=None):
        super().__init__(parent)
        self.title = title
        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(
            "QFrame{background:#f7f8fa;border:1px solid #ccd5e0;border-radius:9px;}"
            "QFrame:hover{background:#f1f5fa;} QLabel{border:0;background:transparent;}"
        )
        layout = QVBoxLayout(self)
        count_label = QLabel(str(count))
        count_label.setStyleSheet("font-size:30px;font-weight:700;color:#1f5189")
        layout.addWidget(count_label)
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size:16px;font-weight:700")
        layout.addWidget(title_label)
        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet("color:#7b8797")
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
            QLabel("Aktuální počty uložených položek. Kliknutím na kartu zobrazíš podrobnosti.")
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
            card.setMinimumHeight(110)
            self.grid.addWidget(card, index // 3, index % 3)

    def open_detail(self, name):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Přehled · {name} — Latflix")
        layout = QVBoxLayout(dialog)
        title = QLabel(name)
        title.setStyleSheet("font-size:20px;font-weight:700")
        layout.addWidget(title)
        form = QFormLayout()
        layout.addLayout(form)

        girls = self.repo.girls(False)
        favorites = [g for g in girls if g.favorite]
        videos = self.repo.videos(False)
        super_videos = [v for v in videos if v.in_super]
        studios = self.repo.studios()
        links = self.repo.links()

        def average_age(rows):
            from .models import age_display
            values = []
            for girl in rows:
                try:
                    age = int(age_display(girl.age_source))
                    if 1 <= age <= 100:
                        values.append(age)
                except Exception:
                    pass
            if not values:
                return "—"
            return f"{sum(values) / len(values):.1f}".replace(".", ",")

        def nationalities(rows):
            counts = Counter(g.nationality for g in rows if g.nationality)
            items = sorted(counts.items(), key=lambda x: (-x[1], x[0].casefold()))[:3]
            return "\n".join(
                f"{i + 1}. {country} ({count}×)"
                for i, (country, count) in enumerate(items)
            ) or "—"

        if name == "Girls":
            form.addRow("Počet dívek:", QLabel(str(len(girls))))
            form.addRow("Průměrný věk:", QLabel(average_age(girls)))
            form.addRow("Nejčastější národnosti:", QLabel(nationalities(girls)))
            form.addRow("Oblíbené:", QLabel(str(len(favorites))))
        elif name == "Oblíbené":
            form.addRow("Počet dívek:", QLabel(str(len(favorites))))
            form.addRow("Průměrný věk:", QLabel(average_age(favorites)))
            form.addRow("Nejčastější národnosti:", QLabel(nationalities(favorites)))
        elif name == "Videa":
            counts = Counter()
            for video in videos:
                for _, girl_name, _ in video.participants:
                    counts[girl_name] += 1
            top = sorted(counts.items(), key=lambda x: (-x[1], x[0].casefold()))[:3]
            form.addRow("Počet videí:", QLabel(str(len(videos))))
            form.addRow(
                "Nejčastější herečky:",
                QLabel("\n".join(
                    f"{i + 1}. {girl} ({count}×)"
                    for i, (girl, count) in enumerate(top)
                ) or "—"),
            )
        elif name == "SUPER":
            studios_count = Counter(v.studio_name for v in super_videos if v.studio_name)
            girls_count = Counter(p[1] for v in super_videos for p in v.participants)
            form.addRow("Počet videí:", QLabel(str(len(super_videos))))
            form.addRow(
                "Nejčastější studia:",
                QLabel("\n".join(
                    f"{i + 1}. {studio} ({count}×)"
                    for i, (studio, count) in enumerate(studios_count.most_common(3))
                ) or "—"),
            )
            form.addRow(
                "Nejčastější herečky:",
                QLabel("\n".join(
                    f"{i + 1}. {girl} ({count}×)"
                    for i, (girl, count) in enumerate(girls_count.most_common(3))
                ) or "—"),
            )
        elif name == "Studia":
            used = [studio for studio in studios if studio.occurrences > 0]
            ranked = sorted(
                studios, key=lambda studio: (-studio.occurrences, studio.name.casefold())
            )[:3]
            form.addRow("Počet studií:", QLabel(str(len(studios))))
            form.addRow("Použitých ve videích:", QLabel(str(len(used))))
            form.addRow(
                "Nejčastější studia:",
                QLabel("\n".join(
                    f"{i + 1}. {studio.name} ({studio.occurrences}×)"
                    for i, studio in enumerate(ranked)
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
            tags = self.repo.catalog("tags")
            used = Counter(tag for girl in girls for tag in girl.tags)
            top = sorted(used.items(), key=lambda x: (-x[1], x[0].casefold()))[:1]
            form.addRow("Počet tagů:", QLabel(str(len(tags))))
            form.addRow("Použitých tagů:", QLabel(str(len(used))))
            form.addRow(
                "Nejpoužívanější tag:",
                QLabel(f"{top[0][0]} ({top[0][1]}×)" if top else "—"),
            )

        buttons = QHBoxLayout()
        go = QPushButton(f"Přejít do sekce {name}")
        close = QPushButton("Zavřít")
        buttons.addStretch()
        buttons.addWidget(go)
        buttons.addWidget(close)
        layout.addLayout(buttons)
        go.clicked.connect(
            lambda: (dialog.accept(), self.navigate("Super" if name == "SUPER" else name))
        )
        close.clicked.connect(dialog.reject)
        dialog.exec()


class TablePage(BasePage):
    def __init__(self, repo, title, model, parent=None):
        super().__init__(repo, title, parent)
        self.model = model
        self.proxy = SmartProxy(self)
        self.proxy.setSourceModel(model)

        self.top = QWidget(self)
        self.top.setFixedHeight(TOP_PANEL_H)
        self.outer.addWidget(self.top)

        self.toolbar = QWidget(self)
        self.toolbar_lay = QHBoxLayout(self.toolbar)
        self.toolbar_lay.setContentsMargins(0, 0, 0, 0)
        self.toolbar_lay.setSpacing(4)
        self.outer.addWidget(self.toolbar)

        self.table = DataTableView(self)
        self.table.setModel(self.proxy)
        self.outer.addWidget(self.table, 1)
        self.table.noteRequested.connect(lambda idx: open_note_for_table(self.table, idx))
        self.table.webRequested.connect(self._web_clicked)
        self.table.tagRequested.connect(self._tag_clicked)

        self._install_delegates()
        self._apply_widths()
        self.table.horizontalHeader().sectionClicked.connect(self._sort)

        self.clear = QPushButton("Vyčistit")
        self.clear.setFixedHeight(BUTTON_H)

    def _sort(self, section):
        header = self.table.horizontalHeader()
        order = (
            Qt.DescendingOrder
            if header.sortIndicatorSection() == section
            and header.sortIndicatorOrder() == Qt.AscendingOrder
            else Qt.AscendingOrder
        )
        self.proxy.sort(section, order)
        header.setSortIndicatorShown(False)

    def _choices(self, source):
        if source == "face":
            return ["", "Ano", "Asi ano", "Asi ne", "Ne", "Zjistit"]
        if source == "yes":
            return ["", "Ano", "Ne", "Asi ano", "Asi ne", "Zjistit"]
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
                        lambda index, source=col.source: self._choices(source),
                        self.table,
                    ),
                )
            elif col.kind == "autocomplete":
                self.table.setItemDelegateForColumn(
                    column_index,
                    AutoCompleteDelegate(
                        lambda text, source=col.source: self._suggestions(source, text),
                        self.table,
                    ),
                )
            elif col.kind in {"text", "note"}:
                self.table.setItemDelegateForColumn(
                    column_index,
                    TextDelegate(self.table, self.table),
                )

    def _apply_widths(self):
        self.table.setColumnWidth(0, 34)
        self.table.setColumnWidth(1, 44)
        for index, col in enumerate(self.model.columns, start=2):
            self.table.setColumnWidth(index, col.width)

    def _web_clicked(self, index):
        pass

    def _tag_clicked(self, index):
        pass

    def current_source_row(self):
        index = self.table.currentIndex()
        return self.proxy.mapToSource(index) if index.isValid() else QModelIndex()

    def refresh(self):
        self.model.reload()
        self.proxy.invalidate()
        self._apply_widths()


class GirlsPage(TablePage):
    def __init__(self, repo, favorites=False, parent=None):
        self.favorites = favorites
        title = "Oblíbené" if favorites else "Girls"
        super().__init__(repo, title, GirlsModel(repo, favorites), parent)
        self._build_top()
        self._build_toolbar()
        self.table.selectionModel().selectionChanged.connect(
            lambda *_: self._update_top()
        )
        self._update_top()

    def _build_top(self):
        layout = QHBoxLayout(self.top)
        layout.setContentsMargins(6, 5, 6, 5)

        self.photo = QLabel("Bez foto")
        self.photo.setAlignment(Qt.AlignCenter)
        self.photo.setFixedSize(72, 126)
        self.photo.setStyleSheet("border:1px solid #bbb;background:#fafafa")
        layout.addWidget(self.photo)

        middle = QVBoxLayout()
        self.name = QLabel(self.title)
        self.name.setStyleSheet("font-size:20px;font-weight:700")
        middle.addWidget(self.name)

        info = QHBoxLayout()
        self.age = QLabel("Věk: —")
        self.occ = QLabel("Počet výskytů: —")
        info.addWidget(self.age)
        info.addSpacing(18)
        info.addWidget(self.occ)
        info.addStretch()
        middle.addLayout(info)

        self.chips = FlowWidget(max_rows=2)
        middle.addWidget(self.chips, 1)
        layout.addLayout(middle, 1)

        right = QVBoxLayout()
        self.links_btn = QPushButton("Odkazy")
        self.detail_btn = QPushButton("Detail")
        self.show_links_btn = QPushButton("Zobrazit odkazy")
        right.addWidget(self.links_btn)
        right.addWidget(self.detail_btn)
        right.addWidget(self.show_links_btn)
        right.addStretch()
        layout.addLayout(right)

        self.detail_btn.clicked.connect(self._detail)
        self.show_links_btn.clicked.connect(self._show_links)

    def _build_toolbar(self):
        self.add = SplitAddButton()
        self.delete = QPushButton("Smazat")
        self.bulk = QPushButton("Hromadné akce")
        self.search = SearchBox()

        self.toolbar_lay.addWidget(self.add)
        self.toolbar_lay.addWidget(self.delete)
        self.toolbar_lay.addWidget(self.bulk)
        self.toolbar_lay.addWidget(self.search)

        self.filter_boxes = {}
        specs = [
            ("nationality", "Národnost", self.repo.catalog("nationalities")),
            ("type_name", "Typ", self.repo.catalog("types")),
            ("status", "Stav", ["Aktivní", "Neaktivní", "Smazaná"]),
            ("sex", "Sex", ["Ano", "Ne", "Asi ano", "Asi ne", "Zjistit"]),
            ("nudity", "Nahota", ["Ano", "Ne", "Asi ano", "Asi ne", "Zjistit"]),
            ("face", "Obličej", ["Ano", "Asi ano", "Asi ne", "Ne", "Zjistit"]),
            ("profile", "Profilovka", ["Ano", "Ne"]),
        ]
        for key, title, values in specs:
            combo = QComboBox()
            combo.addItems([title] + list(values))
            combo.currentTextChanged.connect(self._filters_changed)
            self.filter_boxes[key] = combo
            self.toolbar_lay.addWidget(combo)

        self.toolbar_lay.addStretch()
        self.toolbar_lay.addWidget(self.clear)

        self.add.addRequested.connect(self._add_rows)
        self.delete.clicked.connect(self._delete)
        self.bulk.clicked.connect(self._bulk_menu)
        self.search.textChanged.connect(self.proxy.set_query)
        self.clear.clicked.connect(self._clear_all)

        if self.favorites:
            self.add.setEnabled(False)
            self.delete.setEnabled(False)

    def _filters_changed(self, *_):
        for key, combo in self.filter_boxes.items():
            if key == "profile":
                continue
            self.proxy.set_filter_values(
                key,
                set() if combo.currentIndex() == 0 else {combo.currentText()},
            )

        profile = self.filter_boxes["profile"]
        if profile.currentIndex() == 0:
            self.proxy.predicate = None
        elif profile.currentText() == "Ano":
            self.proxy.predicate = lambda girl: bool(girl.profile_path)
        else:
            self.proxy.predicate = lambda girl: not bool(girl.profile_path)
        self.proxy.invalidateFilter()

    def _add_rows(self, count):
        self.repo.add_girls(count)
        self.refresh()

    def _delete(self):
        ids = selected_source_ids(self.table)
        if ids and QMessageBox.question(
            self, "Smazat", f"Smazat {len(ids)} označených řádků?"
        ) == QMessageBox.Yes:
            self.repo.delete_girls(ids)
            self.refresh()

    def _bulk_menu(self):
        menu = QMenu(self)
        add_favorite = menu.addAction("Přidat do Oblíbených")
        remove_favorite = menu.addAction("Odebrat z Oblíbených")
        selected_action = menu.exec(
            self.bulk.mapToGlobal(self.bulk.rect().bottomLeft())
        )
        ids = selected_source_ids(self.table)

        if selected_action == add_favorite:
            for row_id in ids:
                self.repo.set_favorite(row_id, True)
        elif (
            selected_action == remove_favorite
            and ids
            and QMessageBox.question(
                self, "Oblíbené", "Odebrat označené z Oblíbených?"
            ) == QMessageBox.Yes
        ):
            for row_id in ids:
                self.repo.set_favorite(row_id, False)
        self.refresh()

    def _selected_girl(self):
        source = self.current_source_row()
        return self.model.rows[source.row()] if source.isValid() else None

    def _detail(self):
        girl = self._selected_girl()
        if girl and GirlDetailDialog(self.repo, girl.id, self).exec():
            self.refresh()

    def _show_links(self):
        girl = self._selected_girl()
        if girl:
            self.window().navigate("Odkazy", girl_filter=girl.id)

    def _tag_clicked(self, index):
        source = self.proxy.mapToSource(index)
        girl_id = self.model.record_id(source.row())
        position = self.table.viewport().mapToGlobal(
            self.table.visualRect(index).bottomLeft()
        )
        if TagsDialog(self.repo, girl_id, self, position).exec():
            self.refresh()

    def _update_top(self):
        girl = self._selected_girl()
        if not girl:
            self.name.setText(self.title)
            self.age.setText("Věk: —")
            self.occ.setText("Počet výskytů: —")
            self.chips.set_items([])
            return

        from .models import age_display
        self.name.setText(("★ " if girl.favorite else "") + girl.name)
        self.age.setText(f"Věk: {age_display(girl.age_source) or '—'}")
        self.occ.setText(f"Počet výskytů: {girl.occurrences}")

        per_type = Counter(
            link.type_name for link in self.repo.links() if link.girl_id == girl.id
        )
        global_use = {
            item["name"]: item["distinct_girls"] for item in self.repo.link_types()
        }

        widgets = []
        for type_name, count in sorted(
            per_type.items(),
            key=lambda item: (-global_use.get(item[0], 0), item[0].casefold()),
        ):
            text = type_name + (f" ({count})" if count > 1 else "")
            button = ChipButton(text, type_name)
            button.clicked.connect(
                lambda checked=False, name=type_name, gid=girl.id:
                    self._open_girl_links(gid, name)
            )
            widgets.append(button)
        self.chips.set_items(widgets)

    def _open_girl_links(self, girl_id, type_name):
        for link in self.repo.links():
            if link.girl_id == girl_id and link.type_name == type_name:
                QDesktopServices.openUrl(QUrl(link.url))

    def _clear_all(self):
        self.search.clear()
        for combo in self.filter_boxes.values():
            combo.setCurrentIndex(0)
        self.proxy.clear_filters()

    def refresh(self):
        super().refresh()
        self._update_top()


class VideosPage(TablePage):
    def __init__(self, repo, super_only=False, parent=None):
        self.super_only = super_only
        title = "Super" if super_only else "Videa"
        model = VideosModel(repo, super_only)
        super().__init__(repo, title, model, parent)
        model.unknown_girl = self._unknown_girl
        model.unknown_studio = self._unknown_studio
        self.chip_mode = "Studia"
        self._chip_selected = set()
        self._build_top()
        self._build_toolbar()
        self._refresh_chips()

    def _unknown_girl(self, text):
        if QMessageBox.question(
            self,
            "Nová herečka",
            f"'{text}' není v Girls. Přidat jako nový záznam?",
        ) == QMessageBox.Yes:
            return self.repo.add_girl(text)
        return None

    def _unknown_studio(self, text):
        if QMessageBox.question(
            self,
            "Nové studio",
            f"'{text}' není ve Studiích. Přidat jako nové studio?",
        ) == QMessageBox.Yes:
            studio_id = self.repo.add_studio(text)
            return next((s for s in self.repo.studios() if s.id == studio_id), None)
        return None

    def _build_top(self):
        layout = QVBoxLayout(self.top)
        layout.setContentsMargins(6, 4, 6, 2)

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

        self.chips = FlowWidget(max_rows=3, row_height=28)
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
                (s.name, s.occurrences)
                for s in sorted(
                    self.repo.studios(),
                    key=lambda studio: (-studio.occurrences, studio.name.casefold()),
                )
                if s.name
            ]
        else:
            items = [
                (g.name, g.occurrences)
                for g in sorted(
                    self.repo.girls(False),
                    key=lambda girl: (-girl.occurrences, girl.name.casefold()),
                )
                if g.name
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
        modifiers = QApplication.keyboardModifiers()
        multi = bool(modifiers & (Qt.ControlModifier | Qt.ShiftModifier))
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

    def _build_toolbar(self):
        self.add = SplitAddButton()
        self.delete = QPushButton("Smazat")
        self.super_btn = QPushButton(
            "Odebrat ze SUPER" if self.super_only else "Přidat do SUPER"
        )
        self.search = SearchBox()
        self.studio_filter = QComboBox()
        self.state_filter = QComboBox()
        self.quality_filter = QComboBox()

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
        self.search.textChanged.connect(self.proxy.set_query)
        self.clear.clicked.connect(self._clear_all)

        self._fill_filters()
        self.studio_filter.currentTextChanged.connect(self._filter_changed)
        self.state_filter.currentTextChanged.connect(self._filter_changed)
        self.quality_filter.currentTextChanged.connect(self._filter_changed)

    def _fill_filters(self):
        self.studio_filter.blockSignals(True)
        self.state_filter.blockSignals(True)
        self.quality_filter.blockSignals(True)

        self.studio_filter.clear()
        self.studio_filter.addItem("Studio")
        for studio in sorted(
            self.repo.studios(),
            key=lambda item: (-item.occurrences, item.name.casefold()),
        ):
            self.studio_filter.addItem(studio.name)

        self.state_filter.clear()
        self.state_filter.addItems(["Stav"] + self.repo.catalog("states"))
        self.quality_filter.clear()
        self.quality_filter.addItems(["Kvalita"] + self.repo.catalog("qualities"))

        self.studio_filter.blockSignals(False)
        self.state_filter.blockSignals(False)
        self.quality_filter.blockSignals(False)

    def _filter_changed(self):
        self.proxy.set_filter_values(
            "studio_name",
            set() if self.studio_filter.currentIndex() == 0
            else {self.studio_filter.currentText()},
        )
        self.proxy.set_filter_values(
            "state",
            set() if self.state_filter.currentIndex() == 0
            else {self.state_filter.currentText()},
        )
        self.proxy.set_filter_values(
            "quality",
            set() if self.quality_filter.currentIndex() == 0
            else {self.quality_filter.currentText()},
        )

    def _add_rows(self, count):
        for _ in range(count):
            self.repo.add_video()
        self.refresh()

    def _delete(self):
        ids = selected_source_ids(self.table)
        if ids and QMessageBox.question(
            self, "Smazat", f"Smazat {len(ids)} videí?"
        ) == QMessageBox.Yes:
            self.repo.delete_videos(ids)
            self.refresh()

    def _super_action(self):
        ids = selected_source_ids(self.table)
        if not ids:
            return
        if self.super_only:
            if QMessageBox.question(
                self, "SUPER", "Odebrat označená videa ze SUPER?"
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
        self.studio_filter.setCurrentIndex(0)
        self.state_filter.setCurrentIndex(0)
        self.quality_filter.setCurrentIndex(0)
        self._chip_selected.clear()
        self.proxy.clear_filters()
        self._refresh_chips()

    def refresh(self):
        super().refresh()
        self._fill_filters()
        self._refresh_chips()
        self._apply_chip_filter()


class StudiosPage(TablePage):
    def __init__(self, repo, parent=None):
        super().__init__(repo, "Studia", StudiosModel(repo), parent)
        layout = QVBoxLayout(self.top)
        label = QLabel("Studia")
        label.setStyleSheet("font-size:20px;font-weight:700")
        layout.addWidget(label)
        layout.addStretch()
        self._build_toolbar()

    def _build_toolbar(self):
        self.add = SplitAddButton()
        self.delete = QPushButton("Smazat")
        self.search = SearchBox()
        self.toolbar_lay.addWidget(self.add)
        self.toolbar_lay.addWidget(self.delete)
        self.toolbar_lay.addWidget(self.search)
        self.toolbar_lay.addStretch()
        self.toolbar_lay.addWidget(self.clear)
        self.add.addRequested.connect(self._add)
        self.delete.clicked.connect(self._delete)
        self.search.textChanged.connect(self.proxy.set_query)
        self.clear.clicked.connect(
            lambda: (self.search.clear(), self.proxy.clear_filters())
        )

    def _add(self, count):
        for _ in range(count):
            self.repo.add_studio("")
        self.refresh()

    def _delete(self):
        ids = selected_source_ids(self.table)
        if ids and QMessageBox.question(
            self, "Smazat", f"Smazat {len(ids)} studií?"
        ) == QMessageBox.Yes:
            self.repo.delete_studios(ids)
            self.refresh()


class LinksPage(TablePage):
    CATEGORY_MAP = {
        "Vše": None,
        "Sítě": "Síť",
        "Zdroje": "Zdroj",
        "Rozcestníky": "Rozcestník",
    }

    def __init__(self, repo, parent=None):
        model = LinksModel(repo)
        super().__init__(repo, "Odkazy", model, parent)
        model.unknown_girl = self._unknown_girl
        self.category = "Vše"
        self._chip_selected = set()
        self.external_girl_filter = None
        self._build_top()
        self._build_toolbar()
        self._refresh_chips()

    def _unknown_girl(self, text):
        if QMessageBox.question(
            self,
            "Nová herečka",
            f"'{text}' není v Girls. Přidat jako nový záznam?",
        ) == QMessageBox.Yes:
            return self.repo.add_girl(text)
        return None

    def _build_top(self):
        layout = QHBoxLayout(self.top)
        layout.setContentsMargins(6, 3, 6, 3)

        left = QVBoxLayout()
        head = QHBoxLayout()
        label = QLabel("Odkazy")
        label.setStyleSheet("font-size:20px;font-weight:700")
        head.addWidget(label)

        self.tabs = {}
        for name in ("Vše", "Sítě", "Zdroje", "Rozcestníky"):
            button = QPushButton(name)
            button.setCheckable(True)
            button.setChecked(name == "Vše")
            button.clicked.connect(
                lambda checked=False, value=name: self._set_category(value)
            )
            head.addWidget(button)
            self.tabs[name] = button
        head.addStretch()
        left.addLayout(head)

        self.chips = FlowWidget(max_rows=3, row_height=27)
        left.addWidget(self.chips, 1)
        layout.addLayout(left, 1)

        right = QVBoxLayout()
        self.bulk_add = QPushButton("Přidat odkazy")
        self.catalog = QPushButton("Seznam položek")
        self.visible = QPushButton("Viditelné filtry…")
        self.export = QPushButton("Exportovat odkazy")
        self.show = QPushButton("Zobrazit odkazy")
        right.addWidget(self.bulk_add)
        right.addWidget(self.catalog)
        right.addWidget(self.visible)
        right.addWidget(self.export)
        right.addStretch()
        right.addWidget(self.show)
        layout.addLayout(right)

        self.bulk_add.clicked.connect(self._bulk_add)
        self.catalog.clicked.connect(self._catalog)
        self.visible.clicked.connect(self._visible)
        self.export.clicked.connect(self._export)

    def _build_toolbar(self):
        self.add = SplitAddButton()
        self.remove = QPushButton("Odebrat")
        self.bulk = QPushButton("Hromadné akce")
        self.search = SearchBox()
        self.image_filter = QComboBox()
        self.image_filter.addItems(["Obrázek", "Má obrázek", "Bez obrázku"])

        self.toolbar_lay.addWidget(self.add)
        self.toolbar_lay.addWidget(self.remove)
        self.toolbar_lay.addWidget(self.bulk)
        self.toolbar_lay.addWidget(self.search)
        self.toolbar_lay.addWidget(self.image_filter)
        self.toolbar_lay.addStretch()
        self.toolbar_lay.addWidget(self.clear)

        self.add.addRequested.connect(self._quick_add)
        self.remove.clicked.connect(self._remove)
        self.bulk.clicked.connect(self._bulk_actions)
        self.search.textChanged.connect(self.proxy.set_query)
        self.image_filter.currentTextChanged.connect(self._apply_filters)
        self.clear.clicked.connect(self._clear_all)

    def _set_category(self, name):
        self.category = name
        for tab_name, button in self.tabs.items():
            button.setChecked(tab_name == name)
        self._chip_selected.clear()
        self._refresh_chips()
        self._apply_filters()

    def _refresh_chips(self):
        category = self.CATEGORY_MAP[self.category]
        widgets = []
        for link_type in self.repo.link_types():
            if category and link_type["category"] != category:
                continue
            if self.category == "Vše" and not link_type["visible_all"]:
                continue
            if self.category != "Vše" and not link_type["visible_category"]:
                continue
            name = str(link_type["name"])
            button = ChipButton(
                f"{name} ({link_type['distinct_girls']})",
                name,
            )
            button.setChecked(name in self._chip_selected)
            button.clicked.connect(
                lambda checked=False, value=name: self._chip_click(value, checked)
            )
            widgets.append(button)
        self.chips.set_items(widgets)

    def _chip_click(self, name, checked):
        multi = bool(
            QApplication.keyboardModifiers()
            & (Qt.ControlModifier | Qt.ShiftModifier)
        )
        if not multi:
            self._chip_selected = {name}
        elif checked:
            self._chip_selected.add(name)
        else:
            self._chip_selected.discard(name)
        self._refresh_chips()
        self._apply_filters()

    def _apply_filters(self, *_):
        category = self.CATEGORY_MAP[self.category]
        chips = set(self._chip_selected)
        girl_filter = self.external_girl_filter
        image_index = self.image_filter.currentIndex()

        self.proxy.predicate = lambda link: (
            (not category or link.category == category)
            and (not chips or link.type_name in chips)
            and (not girl_filter or link.girl_id == girl_filter)
            and (image_index != 1 or bool(link.last_image))
            and (image_index != 2 or not bool(link.last_image))
        )
        self.proxy.invalidateFilter()

    def set_girl_filter(self, girl_id):
        self.external_girl_filter = girl_id
        self._apply_filters()

    def _quick_add(self, count):
        if count > 1:
            self._bulk_add()
            return
        url, ok = QInputDialog.getText(self, "Přidat odkaz", "URL")
        if ok and url.strip():
            self.repo.add_link(self.repo.detect_link_type(url), None, url.strip())
            self.refresh()

    def _remove(self):
        ids = selected_source_ids(self.table)
        if ids and QMessageBox.question(
            self, "Odebrat", f"Odebrat {len(ids)} odkazů?"
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
        if not ids or not selected:
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

    def _web_clicked(self, index):
        source = self.proxy.mapToSource(index)
        link = self.model.rows[source.row()]
        if link.url:
            QDesktopServices.openUrl(QUrl(link.url))

    def _clear_all(self):
        self.search.clear()
        self.image_filter.setCurrentIndex(0)
        self._chip_selected.clear()
        self.external_girl_filter = None
        self.proxy.clear_filters()
        self._refresh_chips()
        self._apply_filters()

    def refresh(self):
        super().refresh()
        self._refresh_chips()
        self._apply_filters()


class HelperModel(BaseModel):
    def __init__(self, repo, kind):
        self.kind = kind
        self.columns = (Col("name", "Název", width=260),)
        super().__init__(repo)

    def load_rows(self):
        class Row:
            def __init__(self, data):
                self.id = data["id"]
                self.name = data["name"]
                self.locked = False

        return [Row(item) for item in self.repo.catalog_rows(self.kind)]

    def set_value(self, record, col, value):
        self.repo.update_catalog(record.id, value)
        return True


class HelperPage(TablePage):
    def __init__(self, repo, title, kind, parent=None):
        self.kind = kind
        super().__init__(repo, title, HelperModel(repo, kind), parent)

        layout = QVBoxLayout(self.top)
        label = QLabel(self.title)
        label.setStyleSheet("font-size:20px;font-weight:700")
        layout.addWidget(label)
        layout.addStretch()

        add = QPushButton("Přidat")
        delete = QPushButton("Smazat")
        search = SearchBox()
        self.toolbar_lay.addWidget(add)
        self.toolbar_lay.addWidget(delete)
        self.toolbar_lay.addWidget(search)
        self.toolbar_lay.addStretch()
        self.toolbar_lay.addWidget(self.clear)

        add.clicked.connect(self._add)
        delete.clicked.connect(self._delete)
        search.textChanged.connect(self.proxy.set_query)
        self.clear.clicked.connect(
            lambda: (search.clear(), self.proxy.clear_filters())
        )

    def _add(self):
        name, ok = QInputDialog.getText(
            self, "Přidat", f"Nová položka – {self.title}"
        )
        if ok and name.strip():
            self.repo.add_catalog(self.kind, name)
            self.refresh()

    def _delete(self):
        for row_id in selected_source_ids(self.table):
            self.repo.delete_catalog(row_id)
        self.refresh()


class MainWindow(QMainWindow):
    def __init__(self, repo: Repository):
        super().__init__()
        self.repo = repo
        self.setWindowTitle(APP_NAME)
        self.resize(1500, 900)
        self._menu()

        self.sidebar = Sidebar(self)
        self.stack = QStackedWidget(self)

        host = QWidget()
        layout = QHBoxLayout(host)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(host)

        self.sidebar.sectionRequested.connect(self.navigate)
        self.sidebar.collapse.clicked.connect(lambda: self.sidebar.setVisible(False))

        self._build_pages()

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.navigate("Přehled")

    def _menu(self):
        bar = self.menuBar()
        for name in ("Soubor", "Úpravy", "Nástroje", "Zobrazení", "Nastavení", "Nápověda"):
            menu = bar.addMenu(name)
            if name == "Zobrazení":
                show = menu.addAction("Zobrazit levé menu")
                show.triggered.connect(lambda: self.sidebar.setVisible(True))

    def _build_pages(self):
        self.pages = {
            "Přehled": OverviewPage(self.repo, self.navigate),
            "Girls": GirlsPage(self.repo, False),
            "Oblíbené": GirlsPage(self.repo, True),
            "Odkazy": LinksPage(self.repo),
            "Videa": VideosPage(self.repo, False),
            "Super": VideosPage(self.repo, True),
            "Studia": StudiosPage(self.repo),
            "Stavy": HelperPage(self.repo, "Stavy", "states"),
            "Kvality": HelperPage(self.repo, "Kvality", "qualities"),
            "Tagy": HelperPage(self.repo, "Tagy", "tags"),
            "Typy": HelperPage(self.repo, "Typy", "types"),
            "Národnosti": HelperPage(self.repo, "Národnosti", "nationalities"),
        }
        for page in self.pages.values():
            self.stack.addWidget(page)

    def navigate(self, name: str, girl_filter=None):
        if name not in self.pages:
            return
        page = self.pages[name]
        page.refresh()
        self.stack.setCurrentWidget(page)
        self.sidebar.set_active(name)
        if name == "Odkazy" and girl_filter:
            self.pages["Odkazy"].set_girl_filter(girl_filter)
        self.status.showMessage("" if name == "Přehled" else name)

    def closeEvent(self, event):
        self.repo.cleanup_blank_girls()
        event.accept()
