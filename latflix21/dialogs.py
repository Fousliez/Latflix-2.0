from __future__ import annotations

from collections import Counter
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
    QFormLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QTextEdit, QVBoxLayout, QWidget,
)

from .db import Repository


class GirlDetailDialog(QDialog):
    def __init__(self, repo: Repository, girl_id: int, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.girl_id = girl_id
        self.girl = repo.girl(girl_id)
        self.setWindowTitle("Detail herečky")
        self.resize(760, 540)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self.name = QLineEdit(self.girl.name if self.girl else "")
        form.addRow("Jméno", self.name)

        self.aliases = QLineEdit(", ".join(self.girl.aliases if self.girl else ()))
        form.addRow("Aliasy", self.aliases)

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
        form.addRow("Věk / rok narození", self.age)

        self.nationality = QComboBox()
        self.nationality.addItems([""] + repo.catalog("nationalities"))
        self.nationality.setCurrentText(self.girl.nationality if self.girl else "")
        form.addRow("Národnost", self.nationality)

        self.last_check = QLineEdit(self.girl.last_check if self.girl else "")
        form.addRow("Poslední kontrola", self.last_check)

        self.note = QTextEdit(self.girl.note if self.girl else "")
        self.note.setMaximumHeight(100)
        form.addRow("Poznámka", self.note)

        self.favorite = QCheckBox("V oblíbených")
        self.favorite.setChecked(bool(self.girl and self.girl.favorite))
        form.addRow("", self.favorite)

        self.profile = QLineEdit(self.girl.profile_path if self.girl else "")
        browse = QPushButton("Vybrat…")
        picture_row = QHBoxLayout()
        picture_row.addWidget(self.profile)
        picture_row.addWidget(browse)
        picture_box = QWidget()
        picture_box.setLayout(picture_row)
        form.addRow("Obrázek", picture_box)
        browse.clicked.connect(self._browse)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Profilový obrázek",
            str(Path.home() / "Plocha"),
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
            "nationality": self.nationality.currentText(),
            "last_check": self.last_check.text(),
            "note": self.note.toPlainText(),
            "profile_path": self.profile.text(),
        }
        for key, value in values.items():
            self.repo.update_girl(self.girl_id, key, value)
        self.repo.set_aliases(
            self.girl_id,
            [x.strip() for x in self.aliases.text().split(",") if x.strip()],
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

        layout = QVBoxLayout(self)
        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.NoSelection)
        layout.addWidget(self.list, 1)

        usage = Counter(tag for g in repo.girls(False) for tag in g.tags)
        tags = sorted(
            repo.catalog("tags"),
            key=lambda tag: (-usage.get(tag, 0), tag.casefold()),
        )
        for tag in tags:
            label = f"{tag} ({usage.get(tag, 0)})" if usage.get(tag, 0) else tag
            item = QListWidgetItem(label)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if tag in selected else Qt.Unchecked)
            item.setData(Qt.UserRole, tag)
            self.list.addItem(item)

        row = QHBoxLayout()
        row.addStretch()
        cancel = QPushButton("Zrušit")
        save = QPushButton("Uložit")
        save.setDefault(True)
        row.addWidget(cancel)
        row.addWidget(save)
        layout.addLayout(row)
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.save)

        self.resize(420, min(520, max(180, 70 + 32 * len(tags))))
        if anchor is not None:
            self.move(anchor)

    def save(self):
        values = [
            self.list.item(i).data(Qt.UserRole)
            for i in range(self.list.count())
            if self.list.item(i).checkState() == Qt.Checked
        ]
        self.repo.set_tags(self.girl_id, values)
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
        merge.clicked.connect(
            lambda: QMessageBox.information(
                self,
                "Sloučit názvy",
                "Sloučení názvů bude doladěno při testování 2.1.",
            )
        )

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
            usage = str(link_type["distinct_girls"])
            total = int(link_type["total_links"])
            if total != int(link_type["distinct_girls"]):
                usage += f" ({total})"
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
