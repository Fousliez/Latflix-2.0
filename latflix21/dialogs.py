from __future__ import annotations

from collections import Counter
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
    QFormLayout, QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMessageBox, QPushButton, QScrollArea, QTableWidget, QTableWidgetItem,
    QTextEdit, QVBoxLayout, QWidget,
)

from .db import Repository


class GirlDetailDialog(QDialog):
    def __init__(self, repo: Repository, girl_id: int, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.girl_id = girl_id
        self.girl = repo.girl(girl_id)
        self.alias_edits: list[QLineEdit] = []
        self.setWindowTitle("Detail herečky")
        self.resize(900, 680)

        outer = QVBoxLayout(self)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        body = QWidget()
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)
        layout = QVBoxLayout(body)

        form = QFormLayout()
        layout.addLayout(form)

        self.name = QLineEdit(self.girl.name if self.girl else "")
        form.addRow("Jméno", self.name)

        alias_box = QWidget()
        self.alias_grid = QGridLayout(alias_box)
        self.alias_grid.setContentsMargins(0, 0, 0, 0)
        for alias in (self.girl.aliases if self.girl else ()):
            self._append_alias(alias)
        if not self.alias_edits:
            self._append_alias("")
        add_alias = QPushButton("Přidat alias")
        add_alias.clicked.connect(lambda: self._append_alias(""))
        alias_layout = QVBoxLayout()
        alias_layout.setContentsMargins(0, 0, 0, 0)
        alias_layout.addWidget(alias_box)
        alias_layout.addWidget(add_alias, 0, Qt.AlignLeft)
        alias_host = QWidget()
        alias_host.setLayout(alias_layout)
        form.addRow("Aliasy", alias_host)

        self.type_name = QComboBox()
        self.type_name.addItems([""] + repo.catalog("types"))
        self.type_name.setCurrentText(self.girl.type_name if self.girl else "")
        form.addRow("Typ", self.type_name)

        self.sex = QComboBox()
        self.sex.addItems(["", "Ano", "Ne", "Asi ano", "Asi ne", "Zjistit"])
        self.sex.setCurrentText(self.girl.sex if self.girl else "")
        form.addRow("Sex", self.sex)

        self.nudity = QComboBox()
        self.nudity.addItems(["", "Ano", "Ne", "Asi ano", "Asi ne", "Zjistit"])
        self.nudity.setCurrentText(self.girl.nudity if self.girl else "")
        form.addRow("Nahota", self.nudity)

        self.age = QLineEdit(self.girl.age_source if self.girl else "")
        form.addRow("Věk", self.age)

        self.birth_date = QLineEdit(self.girl.birth_date if self.girl else "")
        form.addRow("Datum narození", self.birth_date)

        self.nationality = QComboBox()
        self.nationality.addItems([""] + repo.catalog("nationalities"))
        self.nationality.setCurrentText(self.girl.nationality if self.girl else "")
        form.addRow("Národnost", self.nationality)

        self.rating = QLineEdit(self.girl.rating if self.girl else "")
        form.addRow("Hodnocení", self.rating)

        self.tags = QLineEdit(", ".join(self.girl.tags if self.girl else ()))
        form.addRow("Tagy", self.tags)

        self.last_check = QLineEdit(self.girl.last_check if self.girl else "")
        form.addRow("Poslední kontrola", self.last_check)

        self.profile = QLineEdit(self.girl.profile_path if self.girl else "")
        browse = QPushButton("Vybrat…")
        picture_row = QHBoxLayout()
        picture_row.setContentsMargins(0, 0, 0, 0)
        picture_row.addWidget(self.profile)
        picture_row.addWidget(browse)
        picture_box = QWidget()
        picture_box.setLayout(picture_row)
        form.addRow("Obrázek", picture_box)
        browse.clicked.connect(self._browse)

        self.last_image = QLineEdit(self.girl.last_image if self.girl else "")
        form.addRow("Poslední obrázek", self.last_image)

        self.note = QTextEdit(self.girl.note if self.girl else "")
        self.note.setMaximumHeight(110)
        form.addRow("Poznámka", self.note)

        created = "—"
        if self.girl:
            with repo.connect() as db:
                row = db.execute("SELECT created_at FROM lf21_girls WHERE id=?", (girl_id,)).fetchone()
                if row:
                    created = str(row[0] or "—")
        created_label = QLabel(created)
        form.addRow("Datum přidání", created_label)

        self.favorite = QCheckBox("V oblíbených")
        self.favorite.setChecked(bool(self.girl and self.girl.favorite))
        form.addRow("Oblíbené", self.favorite)

        self.status = QComboBox()
        self.status.addItems(["", "Aktivní", "Neaktivní", "Smazaná"])
        self.status.setCurrentText(self.girl.status if self.girl else "")
        form.addRow("Stav", self.status)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    def _append_alias(self, text: str):
        edit = QLineEdit(text)
        index = len(self.alias_edits)
        self.alias_edits.append(edit)
        self.alias_grid.addWidget(edit, index // 4, index % 4)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Profilový obrázek",
            "/home/jirka/Plocha",
            "Obrázky (*.png *.jpg *.jpeg *.webp)",
        )
        if path:
            self.profile.setText(path)

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
            "note": self.note.toPlainText(),
            "profile_path": self.profile.text(),
            "last_image": self.last_image.text(),
            "status": self.status.currentText(),
        }
        for key, value in values.items():
            self.repo.update_girl(self.girl_id, key, value)
        self.repo.set_aliases(
            self.girl_id,
            [edit.text().strip() for edit in self.alias_edits if edit.text().strip()],
        )
        self.repo.set_tags(
            self.girl_id,
            [x.strip() for x in self.tags.text().split(",") if x.strip()],
        )
        self.repo.set_favorite(self.girl_id, self.favorite.isChecked())
        self.accept()


class VideoDetailDialog(QDialog):
    def __init__(self, repo: Repository, video_id: int, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.video_id = video_id
        self.video = next((v for v in repo.videos(False) if v.id == video_id), None)
        self.setWindowTitle("Detail videa")
        self.resize(780, 620)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)
        video = self.video

        self.title = QLineEdit(video.title if video else "")
        form.addRow("Název", self.title)

        self.studio = QComboBox()
        self.studio.setEditable(True)
        self.studio.addItems([""] + [x[0] for x in repo.studio_suggestions("")])
        self.studio.setCurrentText(video.studio_name if video else "")
        form.addRow("Studio", self.studio)

        self.release = QLineEdit(video.release_date if video else "")
        form.addRow("Datum vydání", self.release)

        self.state = QComboBox()
        self.state.addItems([""] + repo.catalog("states"))
        self.state.setCurrentText(video.state if video else "")
        form.addRow("Stav", self.state)

        self.quality = QComboBox()
        self.quality.addItems([""] + repo.catalog("qualities"))
        self.quality.setCurrentText(video.quality if video else "")
        form.addRow("Kvalita", self.quality)

        self.available = QComboBox()
        self.available.addItems([""] + repo.catalog("qualities"))
        self.available.setCurrentText(video.available_quality if video else "")
        form.addRow("Dostup. kvalita", self.available)

        self.size = QLineEdit(video.size if video else "")
        form.addRow("Velikost", self.size)

        self.duration = QLineEdit(video.duration if video else "")
        form.addRow("Délka", self.duration)

        self.mixed = QComboBox()
        self.mixed.addItems(["", "Ano", "Ne"])
        self.mixed.setCurrentText(video.mixed_gender if video else "")
        form.addRow("M+Ž", self.mixed)

        self.rating = QLineEdit(video.rating if video else "")
        form.addRow("Hodnocení", self.rating)

        self.note = QTextEdit(video.note if video else "")
        self.note.setMaximumHeight(90)
        form.addRow("Poznámka", self.note)

        layout.addWidget(QLabel("Herečky ve videu"))
        self.people = QListWidget()
        self.people.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addWidget(self.people, 1)

        for girl_id, name, _ in (video.participants if video else ()):
            self._add_person_item(girl_id, name)

        actions = QHBoxLayout()
        add = QPushButton("Přidat herečku")
        remove = QPushButton("Odebrat označené")
        actions.addWidget(add)
        actions.addWidget(remove)
        actions.addStretch()
        layout.addLayout(actions)
        add.clicked.connect(self._add_person)
        remove.clicked.connect(self._remove_people)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _add_person_item(self, girl_id, name):
        item = QListWidgetItem(name)
        item.setData(Qt.UserRole, girl_id)
        self.people.addItem(item)

    def _add_person(self):
        from PySide6.QtWidgets import QInputDialog

        suggestions = [x[0] for x in self.repo.girl_suggestions("")]
        text, ok = QInputDialog.getItem(
            self, "Přidat herečku", "Jméno nebo alias", suggestions, 0, True
        )
        if not ok or not text.strip():
            return

        found = self.repo.find_girl_exact(text)
        if not found:
            if QMessageBox.question(
                self,
                "Nová herečka",
                f"'{text}' není v Girls. Přidat jako nový záznam?",
            ) != QMessageBox.Yes:
                return
            girl_id = self.repo.add_girl(text)
            canonical_name = text
        else:
            girl_id = found[0]
            canonical_name = next(
                (g.name for g in self.repo.girls(False) if g.id == girl_id),
                text,
            )

        if any(
            self.people.item(i).data(Qt.UserRole) == girl_id
            for i in range(self.people.count())
        ):
            return
        self._add_person_item(girl_id, canonical_name)

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
                    f"'{studio_name}' není ve Studiích. Přidat?",
                ) == QMessageBox.Yes:
                    studio_id = self.repo.add_studio(studio_name)
                else:
                    return
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


class TagsDialog(QDialog):
    def __init__(self, repo: Repository, girl_id: int, parent=None, anchor=None):
        super().__init__(parent, Qt.Popup)
        self.repo = repo
        self.girl_id = girl_id
        self.setWindowTitle("Tagy")
        girl = repo.girl(girl_id)
        selected = set(girl.tags if girl else ())

        outer = QVBoxLayout(self)
        self.grid_host = QWidget(self)
        self.grid = QGridLayout(self.grid_host)
        self.grid.setContentsMargins(4, 4, 4, 4)
        self.grid.setHorizontalSpacing(6)
        self.grid.setVerticalSpacing(6)
        outer.addWidget(self.grid_host, 1)

        usage = Counter(tag for g in repo.girls(False) for tag in g.tags)
        tag_rows = {row["name"]: row for row in repo.catalog_rows("tags")}
        tags = sorted(
            repo.catalog("tags"),
            key=lambda tag: (-usage.get(tag, 0), tag.casefold()),
        )

        self.buttons = []
        columns = 4
        for index, tag in enumerate(tags):
            row = tag_rows.get(tag, {})
            color = str(row.get("color") or "#d7e9ff")
            button = QPushButton(tag)
            button.setCheckable(True)
            button.setChecked(tag in selected)
            button.setStyleSheet(
                "QPushButton{padding:5px 9px;border:1px solid #9a9a9a;"
                f"background:{color};border-radius:3px;}}"
                "QPushButton:checked{border:2px solid #1e5f9e;font-weight:700;}"
            )
            button.setProperty("tag_name", tag)
            self.buttons.append(button)
            self.grid.addWidget(button, index // columns, index % columns)

        row = QHBoxLayout()
        row.addStretch()
        self.cancel = QPushButton("Zrušit")
        self.save_btn = QPushButton("Uložit")
        self.save_btn.setDefault(True)
        row.addWidget(self.cancel)
        row.addWidget(self.save_btn)
        outer.addLayout(row)
        self.cancel.clicked.connect(self.reject)
        self.save_btn.clicked.connect(self.save)

        rows = max(1, (len(tags) + columns - 1) // columns)
        self.resize(520, min(560, 85 + rows * 40))
        if anchor is not None:
            self.move(anchor)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Left, Qt.Key_Right):
            if self.save_btn.isDefault():
                self.save_btn.setDefault(False)
                self.cancel.setDefault(True)
            else:
                self.cancel.setDefault(False)
                self.save_btn.setDefault(True)
            event.accept()
            return
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.cancel.isDefault():
                self.reject()
            else:
                self.save()
            event.accept()
            return
        super().keyPressEvent(event)

    def save(self):
        values = [
            str(button.property("tag_name"))
            for button in self.buttons
            if button.isChecked()
        ]
        self.repo.set_tags(self.girl_id, values)
        self.accept()


class GirlLinksDialog(QDialog):
    def __init__(self, repo: Repository, girl_id: int, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.girl_id = girl_id
        self.setWindowTitle("Odkazy herečky")
        self.resize(760, 650)
        self.outer = QVBoxLayout(self)
        self.saved_title = QLabel("Uložené odkazy")
        self.saved_title.setStyleSheet("font-weight:700")
        self.outer.addWidget(self.saved_title)
        self.saved_box = QVBoxLayout()
        self.outer.addLayout(self.saved_box)
        self.outer.addSpacing(8)
        self.outer.addWidget(QLabel("Přidat nové odkazy"))
        self.new_rows = QVBoxLayout()
        self.outer.addLayout(self.new_rows)
        self.rows = []
        for _ in range(10):
            self.add_row()
        add = QPushButton("Přidat řádek")
        add.clicked.connect(self.add_row)
        self.outer.addWidget(add, 0, Qt.AlignLeft)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_new)
        buttons.rejected.connect(self.reject)
        self.outer.addWidget(buttons)
        self.reload_saved()

    def reload_saved(self):
        while self.saved_box.count():
            item = self.saved_box.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        links = [x for x in self.repo.links() if x.girl_id == self.girl_id]
        if not links:
            self.saved_box.addWidget(QLabel("Zatím nejsou uložené žádné odkazy."))
            return
        for link in links:
            row = QWidget()
            lay = QHBoxLayout(row)
            lay.setContentsMargins(0, 0, 0, 0)
            name = QPushButton(link.type_name or "Odkaz")
            edit = QPushButton("Editovat")
            delete = QPushButton("×")
            lay.addWidget(name, 1)
            lay.addWidget(edit)
            lay.addWidget(delete)
            self.saved_box.addWidget(row)
            name.clicked.connect(lambda _=False, url=link.url: QMessageBox.information(self, "URL", url or "—"))
            edit.clicked.connect(lambda _=False, lid=link.id: self.edit_link(lid))
            delete.clicked.connect(lambda _=False, lid=link.id: self.delete_link(lid))

    def add_row(self):
        host = QWidget()
        lay = QHBoxLayout(host)
        lay.setContentsMargins(0, 0, 0, 0)
        combo = QComboBox()
        combo.addItem("Automaticky", None)
        for item in self.repo.link_types():
            combo.addItem(str(item["name"]), int(item["id"]))
        url = QLineEdit()
        url.setPlaceholderText("Adresa / URL")
        lay.addWidget(combo, 0)
        lay.addWidget(url, 1)
        self.new_rows.addWidget(host)
        self.rows.append((combo, url))

    def edit_link(self, link_id: int):
        link = next((x for x in self.repo.links() if x.id == link_id), None)
        if not link:
            return
        text, ok = QInputDialog.getText(self, "Editovat odkaz", "URL", text=link.url)
        if ok:
            self.repo.update_link(link_id, "url", text)
            self.reload_saved()

    def delete_link(self, link_id: int):
        if QMessageBox.question(self, "Smazat odkaz", "Chcete odkaz smazat?") == QMessageBox.Yes:
            self.repo.delete_links([link_id])
            self.reload_saved()

    def save_new(self):
        for combo, url_edit in self.rows:
            url = url_edit.text().strip()
            if not url:
                continue
            type_id = combo.currentData()
            if type_id is None:
                type_id = self.repo.detect_link_type(url)
            self.repo.add_link(type_id, self.girl_id, url)
        self.accept()


class BulkGirlLinksDialog(QDialog):
    def __init__(self, repo: Repository, girl_ids: list[int], parent=None):
        super().__init__(parent)
        self.repo = repo
        self.girl_ids = girl_ids
        self.setWindowTitle("Hromadně přidat odkazy")
        self.resize(900, 520)
        outer = QVBoxLayout(self)
        self.table = QTableWidget(len(girl_ids), 3)
        self.table.setHorizontalHeaderLabels(["Herečka", "Zdroj / platforma", "URL"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        outer.addWidget(self.table, 1)
        self.combos = []
        for row, girl_id in enumerate(girl_ids):
            girl = repo.girl(girl_id)
            name = QTableWidgetItem(girl.name if girl else "")
            name.setFlags(name.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, name)
            combo = QComboBox()
            combo.addItem("Automaticky", None)
            for item in repo.link_types():
                combo.addItem(str(item["name"]), int(item["id"]))
            self.table.setCellWidget(row, 1, combo)
            self.table.setItem(row, 2, QTableWidgetItem(""))
            self.combos.append(combo)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    def save(self):
        for row, girl_id in enumerate(self.girl_ids):
            url = self.table.item(row, 2).text().strip()
            if not url:
                continue
            type_id = self.combos[row].currentData()
            if type_id is None:
                type_id = self.repo.detect_link_type(url)
            self.repo.add_link(type_id, girl_id, url)
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
            item = QListWidgetItem(
                f"{link_type['name']} ({link_type['distinct_girls']})"
            )
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
        self.setWindowTitle("Seznam odkazů")
        self.resize(940, 620)

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(
                "Použití: první číslo je počet různých hereček. "
                "V závorce je celkový počet uložených odkazů."
            )
        )
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Typ", "Název", "Obecný web", "Použití"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        layout.addWidget(self.table, 1)
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
        layout.addLayout(row)

        add.clicked.connect(self.add)
        delete.clicked.connect(self.delete)
        open_web.clicked.connect(self.open_web)
        merge.clicked.connect(self.merge_names)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

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
            self.table.setItem(
                row, 2, QTableWidgetItem(str(link_type["general_web"] or ""))
            )
            total = int(link_type["total_links"])
            usage = f"{int(link_type['distinct_girls'])} ({total})"
            usage_item = QTableWidgetItem(usage)
            usage_item.setFlags(usage_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 3, usage_item)

    def add(self):
        self.repo.add_link_type("Zdroj", "Nový odkaz")
        self.reload()

    def delete(self):
        row = self.table.currentRow()
        if row < 0:
            return
        combo = self.table.cellWidget(row, 0)
        self.repo.delete_link_type(int(combo.property("id")))
        self.reload()

    def merge_names(self):
        rows = sorted({index.row() for index in self.table.selectedIndexes()})
        if len(rows) < 2:
            QMessageBox.information(
                self,
                "Sloučit názvy",
                "Označ alespoň dva názvy, které se mají sloučit.",
            )
            return
        candidates = []
        ids = []
        for row in rows:
            combo = self.table.cellWidget(row, 0)
            ids.append(int(combo.property("id")))
            candidates.append(self.table.item(row, 1).text())
        target_name, ok = QInputDialog.getItem(
            self,
            "Sloučit názvy",
            "Který název má zůstat?",
            candidates,
            0,
            False,
        )
        if not ok:
            return
        target_row = rows[candidates.index(target_name)]
        target_combo = self.table.cellWidget(target_row, 0)
        target_id = int(target_combo.property("id"))
        if QMessageBox.question(
            self,
            "Sloučit názvy",
            f"Sloučit {len(rows)} názvů do '{target_name}'?",
        ) != QMessageBox.Yes:
            return
        self.repo.merge_link_types(target_id, ids)
        self.reload()

    def save(self):
        for row in range(self.table.rowCount()):
            combo = self.table.cellWidget(row, 0)
            self.repo.update_link_type(
                int(combo.property("id")),
                combo.currentText(),
                self.table.item(row, 1).text(),
                self.table.item(row, 2).text(),
            )
        self.accept()

    def open_web(self):
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        row = self.table.currentRow()
        if row >= 0:
            QDesktopServices.openUrl(QUrl(self.table.item(row, 2).text()))


class BulkLinksDialog(QDialog):
    def __init__(self, repo: Repository, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.setWindowTitle("Hromadně přidat odkazy")
        self.resize(1100, 650)

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(
                "Každý řádek vytvoří jeden odkaz. Typ se může určit automaticky "
                "podle URL nebo ručně z katalogu."
            )
        )

        self.table = QTableWidget(10, 7)
        self.table.setHorizontalHeaderLabels(
            [
                "Název", "URL", "Herečka", "Kontrola", "Staženo",
                "Poslední obrázek", "Poslední text",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.table, 1)

        for row in range(10):
            self._init_row(row)

        row = QHBoxLayout()
        add = QPushButton("+ Přidat řádek")
        remove = QPushButton("− Odebrat vybrané řádky")
        row.addWidget(add)
        row.addWidget(remove)
        row.addStretch()
        layout.addLayout(row)
        add.clicked.connect(self.add_row)
        remove.clicked.connect(self.remove_rows)

        buttons = QDialogButtonBox(QDialogButtonBox.Cancel)
        save = buttons.addButton("Přidat odkazy", QDialogButtonBox.AcceptRole)
        save.clicked.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _init_row(self, row):
        combo = QComboBox()
        combo.addItem("Automaticky", None)
        for link_type in self.repo.link_types():
            combo.addItem(str(link_type["name"]), int(link_type["id"]))
        self.table.setCellWidget(row, 0, combo)
        for column in range(1, 7):
            self.table.setItem(row, column, QTableWidgetItem(""))

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
            url = (self.table.item(row, 1).text() if self.table.item(row, 1) else "").strip()
            girl_text = (
                self.table.item(row, 2).text() if self.table.item(row, 2) else ""
            ).strip()
            if not url:
                continue

            combo = self.table.cellWidget(row, 0)
            type_id = combo.currentData() or self.repo.detect_link_type(url)
            girl_id = None

            if girl_text:
                found = self.repo.find_girl_exact(girl_text)
                if not found:
                    if QMessageBox.question(
                        self,
                        "Nová herečka",
                        f"'{girl_text}' není v Girls. Přidat?",
                    ) == QMessageBox.Yes:
                        girl_id = self.repo.add_girl(girl_text)
                    else:
                        continue
                else:
                    girl_id = found[0]

            self.repo.add_link(
                type_id,
                girl_id,
                url,
                check_value=self.table.item(row, 3).text(),
                downloaded=self.table.item(row, 4).text(),
                last_image=self.table.item(row, 5).text(),
                last_text=self.table.item(row, 6).text(),
            )
        self.accept()


class ExportLinksDialog(QDialog):
    def __init__(self, repo: Repository, visible_links: list, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.visible_links = visible_links
        self.setWindowTitle("Exportovat odkazy")
        self.resize(500, 600)

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(
                "Vyber názvy/sítě, které chceš exportovat. Do TXT se uloží pouze URL, "
                "každá na samostatný řádek."
            )
        )
        self.list = QListWidget()
        layout.addWidget(self.list, 1)

        counts = Counter(link.type_name for link in visible_links if link.type_name)
        for name, count in sorted(
            counts.items(), key=lambda item: (-item[1], item[0].casefold())
        ):
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
        layout.addLayout(row)
        all_button.clicked.connect(lambda: self._set_all(Qt.Checked))
        none_button.clicked.connect(lambda: self._set_all(Qt.Unchecked))

        buttons = QDialogButtonBox(QDialogButtonBox.Cancel)
        export = buttons.addButton("Exportovat…", QDialogButtonBox.AcceptRole)
        export.clicked.connect(self.export)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

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
            if link.type_name in names and link.url
        ]
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export odkazů",
            str(Path.home() / "odkazy.txt"),
            "Text (*.txt)",
        )
        if not path:
            return
        Path(path).write_text(
            "\n".join(urls) + ("\n" if urls else ""),
            encoding="utf-8",
        )
        self.accept()
