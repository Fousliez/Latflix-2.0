from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
    QFormLayout, QFrame, QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMessageBox, QPushButton, QScrollArea, QTableWidget,
    QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget, QInputDialog,
)

from .db import Girl, Link, Repository


class GirlDetailDialog(QDialog):
    def __init__(self, repo: Repository, girl_id: int, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.girl_id = int(girl_id)
        self.girl = repo.girl(self.girl_id)
        self.alias_edits: list[QLineEdit] = []
        self.setWindowTitle("Detail herečky")
        self.resize(860, 680)

        root = QVBoxLayout(self)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        host = QWidget(scroll)
        form = QFormLayout(host)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        scroll.setWidget(host)
        root.addWidget(scroll, 1)

        girl = self.girl
        self.name = QLineEdit(girl.name if girl else "")
        form.addRow("Jméno:", self.name)

        alias_host = QWidget(host)
        alias_root = QVBoxLayout(alias_host)
        alias_root.setContentsMargins(0, 0, 0, 0)
        self.alias_grid = QGridLayout()
        self.alias_grid.setContentsMargins(0, 0, 0, 0)
        self.alias_grid.setHorizontalSpacing(6)
        self.alias_grid.setVerticalSpacing(5)
        alias_root.addLayout(self.alias_grid)
        add_alias = QPushButton("Přidat alias")
        add_alias.setFixedWidth(110)
        alias_root.addWidget(add_alias, 0, Qt.AlignLeft)
        form.addRow("Aliasy:", alias_host)
        add_alias.clicked.connect(lambda: self._add_alias(""))
        aliases = list(girl.aliases if girl else ())
        for alias in aliases or [""]:
            self._add_alias(alias)

        self.type_name = QComboBox()
        self.type_name.addItems([""] + repo.catalog("types"))
        self.type_name.setCurrentText(girl.type_name if girl else "")
        form.addRow("Typ:", self.type_name)

        self.sex = self._combo(["", "Ano", "Ne", "Asi ano", "Asi ne", "Zjistit"], girl.sex if girl else "")
        form.addRow("Sex:", self.sex)

        self.nudity = self._combo(["", "Ano", "Ne", "Asi ano", "Asi ne", "Zjistit"], girl.nudity if girl else "")
        form.addRow("Nahota:", self.nudity)

        self.age = QLineEdit(girl.age_source if girl else "")
        form.addRow("Věk:", self.age)

        self.birth_date = QLineEdit(girl.birth_date if girl else "")
        form.addRow("Datum narození:", self.birth_date)

        self.nationality = QComboBox()
        self.nationality.addItems([""] + repo.catalog("nationalities"))
        self.nationality.setCurrentText(girl.nationality if girl else "")
        form.addRow("Národnost:", self.nationality)

        self.rating = QLineEdit(girl.rating if girl else "")
        form.addRow("Hodnocení:", self.rating)

        self.tags = QLineEdit(", ".join(girl.tags if girl else ()))
        form.addRow("Tagy:", self.tags)

        self.last_check = QLineEdit(girl.last_check if girl else "")
        form.addRow("Poslední kontrola:", self.last_check)

        self.profile = QLineEdit(girl.profile_path if girl else "")
        browse_profile = QPushButton("Vybrat…")
        profile_row = QWidget(host)
        profile_lay = QHBoxLayout(profile_row)
        profile_lay.setContentsMargins(0, 0, 0, 0)
        profile_lay.addWidget(self.profile, 1)
        profile_lay.addWidget(browse_profile)
        form.addRow("Obrázek:", profile_row)
        browse_profile.clicked.connect(lambda: self._browse(self.profile))

        self.last_image = QLineEdit(girl.last_image if girl else "")
        browse_last = QPushButton("Vybrat…")
        last_row = QWidget(host)
        last_lay = QHBoxLayout(last_row)
        last_lay.setContentsMargins(0, 0, 0, 0)
        last_lay.addWidget(self.last_image, 1)
        last_lay.addWidget(browse_last)
        form.addRow("Poslední obrázek:", last_row)
        browse_last.clicked.connect(lambda: self._browse(self.last_image))

        self.note = QTextEdit(girl.note if girl else "")
        self.note.setMinimumHeight(110)
        form.addRow("Poznámka:", self.note)

        self.created = QLineEdit(girl.created_at if girl else "")
        self.created.setReadOnly(True)
        form.addRow("Datum přidání:", self.created)

        self.favorite = QCheckBox("V oblíbených")
        self.favorite.setChecked(bool(girl and girl.favorite))
        form.addRow("Oblíbené:", self.favorite)

        self.status = self._combo(["", "Aktivní", "Neaktivní", "Smazaná"], girl.status if girl else "")
        form.addRow("Stav:", self.status)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, self)
        buttons.button(QDialogButtonBox.Save).setText("Uložit")
        buttons.button(QDialogButtonBox.Cancel).setText("Zrušit")
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    @staticmethod
    def _combo(values, current):
        combo = QComboBox()
        combo.addItems(values)
        combo.setCurrentText(current)
        return combo

    def _add_alias(self, text: str):
        edit = QLineEdit(text)
        index = len(self.alias_edits)
        self.alias_edits.append(edit)
        self.alias_grid.addWidget(edit, index // 4, index % 4)

    def _browse(self, target: QLineEdit):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Vybrat obrázek",
            str(Path.home() / "Plocha"),
            "Obrázky (*.png *.jpg *.jpeg *.webp *.bmp)",
        )
        if path:
            target.setText(path)

    def save(self):
        values = {
            "name": self.name.text(),
            "type_name": self.type_name.currentText(),
            "sex": self.sex.currentText(),
            "nudity": self.nudity.currentText(),
            "age_source": self.age.text(),
            "birth_date": self.birth_date.text(),
            "nationality": self.nationality.currentText(),
            "rating": self.rating.text(),
            "last_check": self.last_check.text(),
            "profile_path": self.profile.text(),
            "last_image": self.last_image.text(),
            "note": self.note.toPlainText(),
            "status": self.status.currentText(),
        }
        for key, value in values.items():
            self.repo.update_girl(self.girl_id, key, value)
        self.repo.set_aliases(
            self.girl_id,
            [edit.text().strip() for edit in self.alias_edits if edit.text().strip()],
        )
        allowed = {name.casefold(): name for name in self.repo.catalog("tags")}
        requested = [
            value.strip()
            for value in self.tags.text().split(",")
            if value.strip()
        ]
        self.repo.set_tags(
            self.girl_id,
            [allowed[value.casefold()] for value in requested if value.casefold() in allowed],
        )
        self.repo.set_favorite(self.girl_id, self.favorite.isChecked())
        self.accept()


class VideoDetailDialog(QDialog):
    def __init__(self, repo: Repository, video_id: int, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.video_id = int(video_id)
        self.video = repo.video(self.video_id)
        self.setWindowTitle("Detail videa")
        self.resize(800, 650)

        root = QVBoxLayout(self)
        form = QFormLayout()
        root.addLayout(form)
        video = self.video

        self.title = QLineEdit(video.title if video else "")
        form.addRow("Název:", self.title)

        self.studio = QComboBox()
        self.studio.setEditable(True)
        self.studio.addItems([""] + [x[0] for x in repo.studio_suggestions("")])
        self.studio.setCurrentText(video.studio_name if video else "")
        form.addRow("Studio:", self.studio)

        self.release = QLineEdit(video.release_date if video else "")
        form.addRow("Datum vydání:", self.release)

        self.state = self._combo([""] + repo.catalog("states"), video.state if video else "")
        form.addRow("Stav:", self.state)

        self.quality = self._combo([""] + repo.catalog("qualities"), video.quality if video else "")
        form.addRow("Kvalita:", self.quality)

        self.available = self._combo([""] + repo.catalog("qualities"), video.available_quality if video else "")
        form.addRow("Dostup. kvalita:", self.available)

        self.size = QLineEdit(video.size if video else "")
        form.addRow("Velikost:", self.size)

        self.duration = QLineEdit(video.duration if video else "")
        form.addRow("Délka:", self.duration)

        self.mixed = self._combo(["", "Ano", "Ne"], video.mixed_gender if video else "")
        form.addRow("M+Ž:", self.mixed)

        self.rating = QLineEdit(video.rating if video else "")
        form.addRow("Hodnocení:", self.rating)

        self.note = QTextEdit(video.note if video else "")
        self.note.setMinimumHeight(90)
        form.addRow("Poznámka:", self.note)

        root.addWidget(QLabel("Herečky ve videu"))
        self.people = QListWidget()
        self.people.setSelectionMode(QAbstractItemView.ExtendedSelection)
        root.addWidget(self.people, 1)
        for girl_id, name, _ in (video.participants if video else ()):
            self._add_person_item(girl_id, name)

        row = QHBoxLayout()
        add = QPushButton("Přidat herečku")
        remove = QPushButton("Odebrat označené")
        row.addWidget(add)
        row.addWidget(remove)
        row.addStretch()
        root.addLayout(row)
        add.clicked.connect(self._add_person)
        remove.clicked.connect(self._remove_people)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Uložit")
        buttons.button(QDialogButtonBox.Cancel).setText("Zrušit")
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    @staticmethod
    def _combo(values, current):
        combo = QComboBox()
        combo.addItems(values)
        combo.setCurrentText(current)
        return combo

    def _add_person_item(self, girl_id, name):
        item = QListWidgetItem(name)
        item.setData(Qt.UserRole, int(girl_id))
        self.people.addItem(item)

    def _add_person(self):
        suggestions = [x[0] for x in self.repo.girl_suggestions("")]
        text, ok = QInputDialog.getItem(
            self, "Přidat herečku", "Jméno nebo alias:", suggestions, 0, True
        )
        if not ok or not text.strip():
            return
        found = self.repo.find_girl_exact(text)
        if not found:
            if QMessageBox.question(
                self,
                "Nová herečka",
                f"'{text}' není v Girls. Přidat jako nový záznam?",
                QMessageBox.Yes | QMessageBox.No,
            ) != QMessageBox.Yes:
                return
            girl_id = self.repo.add_girl(text)
            canonical = text
        else:
            girl_id = found[0]
            girl = self.repo.girl(girl_id)
            canonical = girl.name if girl else text
        if any(self.people.item(i).data(Qt.UserRole) == girl_id for i in range(self.people.count())):
            return
        self._add_person_item(girl_id, canonical)

    def _remove_people(self):
        for item in self.people.selectedItems():
            self.people.takeItem(self.people.row(item))

    def save(self):
        video = self.video
        if not video:
            self.reject()
            return

        studio_name = self.studio.currentText().strip()
        studio_id = None
        if studio_name:
            studio = self.repo.studio_by_name(studio_name)
            if not studio:
                if QMessageBox.question(
                    self,
                    "Nové studio",
                    f"'{studio_name}' není ve Studiích. Přidat jako nový záznam?",
                    QMessageBox.Yes | QMessageBox.No,
                ) != QMessageBox.Yes:
                    return
                studio_id = self.repo.add_studio(studio_name)
            else:
                studio_id = studio.id
        self.repo.set_video_studio(video.id, studio_id)

        values = {
            "title": self.title.text(),
            "release_date": self.release.text(),
            "state": self.state.currentText(),
            "quality": self.quality.currentText(),
            "available_quality": self.available.currentText(),
            "size": self.size.text(),
            "duration": self.duration.text(),
            "mixed_gender": self.mixed.currentText(),
            "rating": self.rating.text(),
            "note": self.note.toPlainText(),
        }
        for key, value in values.items():
            self.repo.update_video(video.id, key, value)

        self.repo.set_video_participants(
            video.id,
            [self.people.item(i).data(Qt.UserRole) for i in range(self.people.count())],
        )
        self.accept()


class EditLinkDialog(QDialog):
    def __init__(self, repo: Repository, link: Link, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.link = link
        self.setWindowTitle("Editovat odkaz")
        form = QFormLayout(self)
        self.source = QComboBox()
        for item in repo.link_types():
            self.source.addItem(str(item["name"]), int(item["id"]))
        if link.type_id is not None:
            idx = self.source.findData(int(link.type_id))
            if idx >= 0:
                self.source.setCurrentIndex(idx)
        self.url = QLineEdit(link.url)
        form.addRow("Zdroj / platforma:", self.source)
        form.addRow("URL:", self.url)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Uložit")
        buttons.button(QDialogButtonBox.Cancel).setText("Zrušit")
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def save(self):
        self.repo.set_link_type(self.link.id, self.source.currentData())
        self.repo.update_link(self.link.id, "url", self.url.text())
        self.accept()


class AutoLinkRow(QWidget):
    def __init__(self, repo: Repository, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.manual = False
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        self.source = QComboBox(self)
        self.source.addItem("Automaticky", None)
        for item in repo.link_types():
            self.source.addItem(str(item["name"]), int(item["id"]))
        self.source.setMinimumWidth(180)

        self.url = QLineEdit(self)
        self.url.setPlaceholderText("Adresa / URL")

        row.addWidget(self.source)
        row.addWidget(self.url, 1)

        self.source.activated.connect(self._source_changed)
        self.url.textChanged.connect(self._detect)

    def _source_changed(self, index):
        self.manual = index > 0

    def _detect(self, text):
        if self.manual:
            return
        type_id = self.repo.detect_link_type(text)
        if type_id is None:
            self.source.setCurrentIndex(0)
            return
        idx = self.source.findData(type_id)
        if idx >= 0:
            self.source.blockSignals(True)
            self.source.setCurrentIndex(idx)
            self.source.blockSignals(False)
            self.manual = False

    def values(self):
        type_id = self.source.currentData()
        if type_id is None:
            type_id = self.repo.detect_link_type(self.url.text())
        return type_id, self.url.text().strip()


class GirlLinksDialog(QDialog):
    def __init__(self, repo: Repository, girl_id: int, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.girl_id = int(girl_id)
        self.rows: list[AutoLinkRow] = []
        girl = repo.girl(girl_id)
        self.setWindowTitle(f"Odkazy – {girl.name if girl else ''}")
        self.resize(760, 690)

        root = QVBoxLayout(self)

        saved_frame = QFrame(self)
        saved_frame.setFrameShape(QFrame.StyledPanel)
        saved_layout = QVBoxLayout(saved_frame)
        saved_layout.addWidget(QLabel("Uložené odkazy"))
        self.saved_host = QWidget(saved_frame)
        self.saved_list = QVBoxLayout(self.saved_host)
        self.saved_list.setContentsMargins(0, 0, 0, 0)
        self.saved_list.setSpacing(3)
        saved_layout.addWidget(self.saved_host)
        root.addWidget(saved_frame)
        self.refresh_saved()

        root.addWidget(QLabel("Přidat nové odkazy"))
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.rows_host = QWidget(self.scroll)
        self.rows_layout = QVBoxLayout(self.rows_host)
        self.rows_layout.setContentsMargins(2, 2, 2, 2)
        self.rows_layout.setSpacing(4)
        self.scroll.setWidget(self.rows_host)
        root.addWidget(self.scroll, 1)

        for _ in range(10):
            self.add_row()

        add = QPushButton("Přidat řádek")
        add.clicked.connect(self.add_row)
        root.addWidget(add, 0, Qt.AlignLeft)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Uložit")
        buttons.button(QDialogButtonBox.Cancel).setText("Zrušit")
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def refresh_saved(self):
        while self.saved_list.count():
            item = self.saved_list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        links = self.repo.links_for_girl(self.girl_id)
        if not links:
            label = QLabel("Zatím nejsou uložené žádné odkazy.")
            label.setStyleSheet("color:#777")
            self.saved_list.addWidget(label)
            return

        for link in links:
            line = QWidget(self.saved_host)
            row = QHBoxLayout(line)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(5)
            name = QPushButton(link.type_name or "Odkaz")
            name.setFlat(True)
            name.setStyleSheet("text-align:left;color:#245b96")
            edit = QPushButton("Editovat")
            delete = QPushButton("×")
            delete.setFixedWidth(30)
            row.addWidget(name, 1)
            row.addWidget(edit)
            row.addWidget(delete)
            name.clicked.connect(
                lambda checked=False, url=link.url:
                    QMessageBox.information(self, "URL", url or "(prázdná URL)")
            )
            edit.clicked.connect(
                lambda checked=False, item=link: self.edit_link(item)
            )
            delete.clicked.connect(
                lambda checked=False, link_id=link.id: self.delete_link(link_id)
            )
            self.saved_list.addWidget(line)

    def edit_link(self, link: Link):
        if EditLinkDialog(self.repo, link, self).exec():
            self.refresh_saved()

    def delete_link(self, link_id: int):
        if QMessageBox.question(
            self,
            "Smazat odkaz",
            "Chcete odkaz smazat?",
            QMessageBox.Yes | QMessageBox.No,
        ) == QMessageBox.Yes:
            self.repo.delete_links([link_id])
            self.refresh_saved()

    def add_row(self):
        widget = AutoLinkRow(self.repo, self.rows_host)
        self.rows_layout.addWidget(widget)
        self.rows.append(widget)

    def save(self):
        for row in self.rows:
            type_id, url = row.values()
            if url:
                self.repo.add_link(type_id, self.girl_id, url, is_new=False)
        self.accept()


class BulkGirlLinksDialog(QDialog):
    def __init__(self, repo: Repository, girls: list[Girl], parent=None):
        super().__init__(parent)
        self.repo = repo
        self.entries: list[tuple[int, AutoLinkRow]] = []
        self.setWindowTitle("Hromadně přidat odkazy")
        self.resize(860, 580)

        root = QVBoxLayout(self)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        host = QWidget(scroll)
        layout = QVBoxLayout(host)
        layout.setSpacing(4)

        for girl in girls:
            line = QWidget(host)
            line_lay = QHBoxLayout(line)
            line_lay.setContentsMargins(0, 0, 0, 0)
            name = QLineEdit(girl.name)
            name.setReadOnly(True)
            name.setMinimumWidth(190)
            row = AutoLinkRow(repo, line)
            line_lay.addWidget(name)
            line_lay.addWidget(row, 1)
            layout.addWidget(line)
            self.entries.append((girl.id, row))

        layout.addStretch()
        scroll.setWidget(host)
        root.addWidget(scroll, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Uložit")
        buttons.button(QDialogButtonBox.Cancel).setText("Zrušit")
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def save(self):
        for girl_id, row in self.entries:
            type_id, url = row.values()
            if url:
                self.repo.add_link(type_id, girl_id, url, is_new=False)
        self.accept()


class VisibleLinkFiltersDialog(QDialog):
    CATEGORY_MAP = {
        "Vše": None,
        "Sítě": "Síť",
        "Zdroje": "Zdroj",
        "Rozcestníky": "Rozcestník",
    }

    def __init__(self, repo: Repository, category: str, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.category = category
        self.setWindowTitle(f"Viditelné filtry Odkazů – {category}")
        self.resize(540, 600)

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel("Zaškrtni názvy, které chceš zobrazovat jako modré filtry nahoře.")
        )
        self.list = QListWidget()
        layout.addWidget(self.list, 1)

        wanted = self.CATEGORY_MAP.get(category)
        for link_type in repo.link_types():
            if wanted and str(link_type["category"]) != wanted:
                continue
            item = QListWidgetItem(f"{link_type['name']} ({link_type['distinct_girls']})")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            visible = (
                bool(link_type["visible_all"])
                if category == "Vše"
                else bool(link_type["visible_category"])
            )
            item.setCheckState(Qt.Checked if visible else Qt.Unchecked)
            item.setData(Qt.UserRole, int(link_type["id"]))
            self.list.addItem(item)

        row = QHBoxLayout()
        all_button = QPushButton("Vybrat vše")
        none_button = QPushButton("Zrušit vše")
        row.addWidget(all_button)
        row.addWidget(none_button)
        row.addStretch()
        layout.addLayout(row)
        all_button.clicked.connect(lambda: self._set_all(Qt.Checked))
        none_button.clicked.connect(lambda: self._set_all(Qt.Unchecked))

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("OK")
        buttons.button(QDialogButtonBox.Cancel).setText("Zrušit")
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _set_all(self, state):
        for i in range(self.list.count()):
            self.list.item(i).setCheckState(state)

    def save(self):
        for i in range(self.list.count()):
            item = self.list.item(i)
            visible = item.checkState() == Qt.Checked
            self.repo.set_link_type_visibility(
                item.data(Qt.UserRole),
                all_visible=visible if self.category == "Vše" else None,
                category_visible=visible if self.category != "Vše" else None,
            )
        self.accept()


class LinkCatalogDialog(QDialog):
    def __init__(self, repo: Repository, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.setWindowTitle("Seznam všech odkazů")
        self.resize(940, 620)

        root = QVBoxLayout(self)
        root.addWidget(
            QLabel(
                "Použití: první číslo je počet různých hereček. "
                "V závorce je celkový počet uložených odkazů."
            )
        )
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Typ", "Název", "Obecný web", "Použití"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        root.addWidget(self.table, 1)
        self.reload()

        row = QHBoxLayout()
        add = QPushButton("+ Přidat")
        delete = QPushButton("− Odstranit")
        merge = QPushButton("Sloučit názvy…")
        open_web = QPushButton("Otevřít web")
        row.addWidget(add)
        row.addWidget(delete)
        row.addWidget(merge)
        row.addStretch()
        row.addWidget(open_web)
        root.addLayout(row)
        add.clicked.connect(self.add)
        delete.clicked.connect(self.delete)
        merge.clicked.connect(self.merge)
        open_web.clicked.connect(self.open_web)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Uložit")
        buttons.button(QDialogButtonBox.Cancel).setText("Zrušit")
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def reload(self):
        rows = self.repo.link_types()
        self.table.setRowCount(len(rows))
        for row, link_type in enumerate(rows):
            category = QComboBox()
            category.addItems(["Síť", "Zdroj", "Rozcestník"])
            category.setCurrentText(str(link_type["category"]))
            category.setProperty("id", int(link_type["id"]))
            self.table.setCellWidget(row, 0, category)
            self.table.setItem(row, 1, QTableWidgetItem(str(link_type["name"])))
            self.table.setItem(row, 2, QTableWidgetItem(str(link_type["general_web"] or "")))
            usage = str(link_type["distinct_girls"])
            total = int(link_type["total_links"])
            if total != int(link_type["distinct_girls"]):
                usage += f" ({total})"
            usage_item = QTableWidgetItem(usage)
            usage_item.setFlags(usage_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 3, usage_item)

    def add(self):
        base = "Nový odkaz"
        name = base
        index = 2
        known = {str(item["name"]).casefold() for item in self.repo.link_types()}
        while name.casefold() in known:
            name = f"{base} {index}"
            index += 1
        self.repo.add_link_type("Zdroj", name)
        self.reload()

    def selected_type_ids(self):
        result = []
        for index in self.table.selectionModel().selectedRows():
            combo = self.table.cellWidget(index.row(), 0)
            if combo:
                result.append(int(combo.property("id")))
        return list(dict.fromkeys(result))

    def delete(self):
        ids = self.selected_type_ids()
        if not ids:
            return
        if QMessageBox.question(
            self, "Odstranit", f"Odstranit {len(ids)} položek katalogu?"
        ) != QMessageBox.Yes:
            return
        for type_id in ids:
            self.repo.delete_link_type(type_id)
        self.reload()

    def merge(self):
        ids = self.selected_type_ids()
        if len(ids) < 2:
            QMessageBox.information(self, "Sloučit názvy", "Označ alespoň dvě položky.")
            return
        items = [item for item in self.repo.link_types() if int(item["id"]) in ids]
        labels = [str(item["name"]) for item in items]
        target_name, ok = QInputDialog.getItem(
            self, "Sloučit názvy", "Cílový název:", labels, 0, False
        )
        if not ok:
            return
        target = next(item for item in items if str(item["name"]) == target_name)
        self.repo.merge_link_types(
            int(target["id"]),
            [int(item["id"]) for item in items if int(item["id"]) != int(target["id"])],
        )
        self.reload()

    def save(self):
        for row in range(self.table.rowCount()):
            combo = self.table.cellWidget(row, 0)
            name_item = self.table.item(row, 1)
            web_item = self.table.item(row, 2)
            if combo and name_item and web_item:
                self.repo.update_link_type(
                    int(combo.property("id")),
                    combo.currentText(),
                    name_item.text(),
                    web_item.text(),
                )
        self.accept()

    def open_web(self):
        row = self.table.currentRow()
        if row < 0:
            return
        item = self.table.item(row, 2)
        if item and item.text().strip():
            QDesktopServices.openUrl(QUrl.fromUserInput(item.text().strip()))


class BulkLinksDialog(QDialog):
    def __init__(self, repo: Repository, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.setWindowTitle("Hromadně přidat odkazy")
        self.resize(1120, 650)

        root = QVBoxLayout(self)
        root.addWidget(
            QLabel(
                "Každý řádek vytvoří jeden odkaz. Název lze určit automaticky podle URL "
                "nebo ručně z katalogu."
            )
        )

        self.table = QTableWidget(10, 7)
        self.table.setHorizontalHeaderLabels(
            ["Název", "URL", "Herečka", "Kontrola", "Staženo", "Poslední obrázek", "Poslední text"]
        )
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        root.addWidget(self.table, 1)
        for row in range(10):
            self._init_row(row)
        self.table.cellChanged.connect(self._cell_changed)

        actions = QHBoxLayout()
        add = QPushButton("+ Přidat řádek")
        remove = QPushButton("− Odebrat vybrané řádky")
        actions.addWidget(add)
        actions.addWidget(remove)
        actions.addStretch()
        root.addLayout(actions)
        add.clicked.connect(self.add_row)
        remove.clicked.connect(self.remove_rows)

        buttons = QDialogButtonBox(QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Cancel).setText("Zrušit")
        save = buttons.addButton("Přidat odkazy", QDialogButtonBox.AcceptRole)
        save.clicked.connect(self.save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _init_row(self, row):
        combo = QComboBox()
        combo.addItem("Automaticky", None)
        for link_type in self.repo.link_types():
            combo.addItem(str(link_type["name"]), int(link_type["id"]))
        combo.setProperty("manual", False)
        combo.activated.connect(
            lambda index, box=combo: box.setProperty("manual", index > 0)
        )
        self.table.setCellWidget(row, 0, combo)
        for column in range(1, 7):
            self.table.setItem(row, column, QTableWidgetItem(""))

    def _cell_changed(self, row, column):
        if column != 1:
            return
        combo = self.table.cellWidget(row, 0)
        item = self.table.item(row, 1)
        if not combo or not item or bool(combo.property("manual")):
            return
        type_id = self.repo.detect_link_type(item.text())
        idx = combo.findData(type_id) if type_id is not None else 0
        combo.blockSignals(True)
        combo.setCurrentIndex(idx if idx >= 0 else 0)
        combo.blockSignals(False)
        combo.setProperty("manual", False)

    def add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self._init_row(row)

    def remove_rows(self):
        rows = sorted({index.row() for index in self.table.selectedIndexes()}, reverse=True)
        for row in rows:
            self.table.removeRow(row)

    def save(self):
        for row in range(self.table.rowCount()):
            def text(col):
                item = self.table.item(row, col)
                return item.text().strip() if item else ""

            url = text(1)
            if not url:
                continue
            combo = self.table.cellWidget(row, 0)
            type_id = combo.currentData() if combo else None
            if type_id is None:
                type_id = self.repo.detect_link_type(url)

            girl_id = None
            girl_text = text(2)
            if girl_text:
                found = self.repo.find_girl_exact(girl_text)
                if not found:
                    if QMessageBox.question(
                        self,
                        "Nová herečka",
                        f"'{girl_text}' není v Girls. Přidat jako nový záznam?",
                    ) != QMessageBox.Yes:
                        continue
                    girl_id = self.repo.add_girl(girl_text)
                else:
                    girl_id = found[0]

            self.repo.add_link(
                type_id,
                girl_id,
                url,
                check_value=text(3),
                downloaded=text(4),
                last_image=text(5),
                last_text=text(6),
                is_new=False,
            )
        self.accept()


class ExportLinksDialog(QDialog):
    def __init__(self, repo: Repository, visible_links: list[Link], parent=None):
        super().__init__(parent)
        self.repo = repo
        self.visible_links = visible_links
        self.setWindowTitle("Exportovat odkazy")
        self.resize(520, 610)

        root = QVBoxLayout(self)
        root.addWidget(
            QLabel(
                "Zobrazené jsou pouze typy, které jsou právě ve vyfiltrované tabulce. "
                "Do TXT se uloží jen URL, každá na samostatný řádek."
            )
        )
        self.list = QListWidget()
        root.addWidget(self.list, 1)

        counts: dict[str, int] = {}
        for link in visible_links:
            if link.type_name:
                counts[link.type_name] = counts.get(link.type_name, 0) + 1
        for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0].casefold())):
            item = QListWidgetItem(f"{name} ({count})")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            item.setData(Qt.UserRole, name)
            self.list.addItem(item)

        row = QHBoxLayout()
        all_button = QPushButton("Vybrat vše")
        none_button = QPushButton("Zrušit vše")
        row.addWidget(all_button)
        row.addWidget(none_button)
        row.addStretch()
        root.addLayout(row)
        all_button.clicked.connect(lambda: self._set_all(Qt.Checked))
        none_button.clicked.connect(lambda: self._set_all(Qt.Unchecked))

        buttons = QDialogButtonBox(QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Cancel).setText("Zrušit")
        export = buttons.addButton("Exportovat…", QDialogButtonBox.AcceptRole)
        export.clicked.connect(self.export)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _set_all(self, state):
        for i in range(self.list.count()):
            self.list.item(i).setCheckState(state)

    def export(self):
        names = {
            self.list.item(i).data(Qt.UserRole)
            for i in range(self.list.count())
            if self.list.item(i).checkState() == Qt.Checked
        }
        urls = [
            link.url
            for link in self.visible_links
            if link.type_name in names and link.url.strip()
        ]
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export odkazů",
            str(Path.home() / "odkazy.txt"),
            "Text (*.txt)",
        )
        if not path:
            return
        Path(path).write_text("\n".join(urls) + ("\n" if urls else ""), encoding="utf-8")
        self.accept()
