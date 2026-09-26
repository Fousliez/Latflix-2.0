from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRubberBand,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .database import GirlRecord, LinkRecord, Repository
from .schema import FACE_VALUES, GIRL_STATUS_VALUES, YES_VALUES


def detect_source(url: str) -> str:
    raw = str(url or "").strip()
    if not raw:
        return "Automaticky"
    parsed = urlparse(raw if "://" in raw else "https://" + raw)
    host = parsed.netloc.casefold().removeprefix("www.")
    known = (
        ("instagram", "Instagram"),
        ("facebook", "Facebook"),
        ("redgifs", "Redgifs"),
        ("pornhub", "Pornhub"),
        ("linktr.ee", "Linktree"),
        ("x.com", "X"),
        ("twitter", "X"),
        ("tiktok", "TikTok"),
        ("reddit", "Reddit"),
        ("youtube", "YouTube"),
    )
    for needle, name in known:
        if needle in host:
            return name
    stem = host.split(".")[0].strip()
    return stem.capitalize() if stem else "Odkaz"


class TagsDialog(QDialog):
    def __init__(self, repository: Repository, selected: tuple[str, ...], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tagy")
        self._buttons: list[QPushButton] = []

        root = QVBoxLayout(self)
        chips = QHBoxLayout()
        for entry in repository.catalog("tags"):
            button = QPushButton(entry.name, self)
            button.setCheckable(True)
            button.setChecked(entry.name in selected)
            button.setStyleSheet(
                f"QPushButton {{ background: {entry.color}; padding: 5px 9px; border: 1px solid #999; }}"
                "QPushButton:checked { border: 2px solid #2f78bd; }"
            )
            chips.addWidget(button)
            self._buttons.append(button)
        chips.addStretch(1)
        root.addLayout(chips)
        root.addStretch(1)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, self)
        buttons.button(QDialogButtonBox.Save).setText("Uložit")
        buttons.button(QDialogButtonBox.Cancel).setText("Zrušit")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def selected_tags(self) -> list[str]:
        return [button.text() for button in self._buttons if button.isChecked()]


class LinkInputRow(QWidget):
    def __init__(self, sources: tuple[str, ...], parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        self.source = QComboBox(self)
        self.source.setEditable(True)
        self.source.addItem("Automaticky")
        self.source.addItems(sources)
        self.source.setMinimumWidth(150)
        self.source.setProperty("manualSource", False)

        self.url = QLineEdit(self)
        self.url.setPlaceholderText("https://…")

        self.source.activated.connect(self._manual_source)
        self.url.textChanged.connect(self._detect)
        layout.addWidget(self.source)
        layout.addWidget(self.url, 1)

    def _manual_source(self, _index: int) -> None:
        self.source.setProperty("manualSource", self.source.currentText() != "Automaticky")

    def _detect(self, text: str) -> None:
        if not bool(self.source.property("manualSource")):
            self.source.setCurrentText(detect_source(text) if text.strip() else "Automaticky")

    def values(self) -> tuple[str, str]:
        source = self.source.currentText().strip()
        url = self.url.text().strip()
        if not source or source == "Automaticky":
            source = detect_source(url)
        return source, url


class LinksDialog(QDialog):
    def __init__(self, repository: Repository, girl_id: int, parent=None):
        super().__init__(parent)
        self.repository = repository
        self.girl_id = int(girl_id)
        self._new_rows: list[LinkInputRow] = []
        self.setWindowTitle("Odkazy")
        self.resize(760, 650)

        root = QVBoxLayout(self)
        root.addWidget(QLabel("<b>Uložené odkazy</b>", self))

        self.saved_host = QWidget(self)
        self.saved_layout = QVBoxLayout(self.saved_host)
        self.saved_layout.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self.saved_host)

        root.addWidget(QLabel("<b>Přidat nové odkazy</b>", self))
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        new_host = QWidget(scroll)
        self.new_layout = QVBoxLayout(new_host)
        self.new_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(new_host)
        root.addWidget(scroll, 1)

        for _ in range(10):
            self.add_input_row()

        add = QPushButton("Přidat řádek", self)
        add.clicked.connect(self.add_input_row)
        root.addWidget(add, 0, Qt.AlignLeft)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, self)
        buttons.button(QDialogButtonBox.Save).setText("Uložit")
        buttons.button(QDialogButtonBox.Cancel).setText("Zrušit")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self.refresh_saved()

    def refresh_saved(self) -> None:
        while self.saved_layout.count():
            item = self.saved_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for link in self.repository.links(self.girl_id):
            row = QWidget(self.saved_host)
            layout = QHBoxLayout(row)
            layout.setContentsMargins(0, 0, 0, 0)
            source = QPushButton(link.source or "Odkaz", row)
            source.clicked.connect(lambda _checked=False, value=link.url: QMessageBox.information(self, "URL", value))
            edit = QPushButton("Editovat", row)
            edit.clicked.connect(lambda _checked=False, value=link: self.edit_link(value))
            delete = QPushButton("×", row)
            delete.setFixedWidth(32)
            delete.clicked.connect(lambda _checked=False, value=link.id: self.delete_link(value))
            layout.addWidget(source, 1)
            layout.addWidget(edit)
            layout.addWidget(delete)
            self.saved_layout.addWidget(row)

    def add_input_row(self) -> None:
        row = LinkInputRow(self.repository.catalog_names("link_sources"), self)
        self.new_layout.addWidget(row)
        self._new_rows.append(row)

    def edit_link(self, link: LinkRecord) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Editovat odkaz")
        form = QFormLayout(dialog)
        source = QComboBox(dialog)
        source.setEditable(True)
        source.addItems(self.repository.catalog_names("link_sources"))
        source.setCurrentText(link.source)
        url = QLineEdit(link.url, dialog)
        form.addRow("Zdroj:", source)
        form.addRow("URL:", url)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        if dialog.exec() == QDialog.Accepted:
            self.repository.update_link(link.id, source.currentText(), url.text())
            self.refresh_saved()

    def delete_link(self, link_id: int) -> None:
        result = QMessageBox.question(
            self,
            "Smazat odkaz",
            "Chcete odkaz smazat?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if result == QMessageBox.Yes:
            self.repository.delete_link(link_id)
            self.refresh_saved()

    def _save(self) -> None:
        for row in self._new_rows:
            source, url = row.values()
            if url:
                self.repository.add_link(self.girl_id, source, url)
        self.accept()


class BulkLinksDialog(QDialog):
    def __init__(self, repository: Repository, girls: list[GirlRecord], parent=None):
        super().__init__(parent)
        self.repository = repository
        self.rows: list[tuple[int, LinkInputRow]] = []
        self.setWindowTitle("Hromadně přidat odkazy")
        self.resize(800, 500)

        root = QVBoxLayout(self)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        host = QWidget(scroll)
        layout = QVBoxLayout(host)

        for girl in girls:
            line = QWidget(host)
            row_layout = QHBoxLayout(line)
            row_layout.setContentsMargins(0, 0, 0, 0)
            name = QLineEdit(girl.name, line)
            name.setReadOnly(True)
            name.setMinimumWidth(190)
            input_row = LinkInputRow(repository.catalog_names("link_sources"), line)
            row_layout.addWidget(name)
            row_layout.addWidget(input_row, 1)
            layout.addWidget(line)
            self.rows.append((girl.id, input_row))

        layout.addStretch(1)
        scroll.setWidget(host)
        root.addWidget(scroll, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, self)
        buttons.button(QDialogButtonBox.Save).setText("Uložit")
        buttons.button(QDialogButtonBox.Cancel).setText("Zrušit")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _save(self) -> None:
        for girl_id, row in self.rows:
            source, url = row.values()
            if url:
                self.repository.add_link(girl_id, source, url)
        self.accept()


class GirlDetailDialog(QDialog):
    def __init__(self, repository: Repository, record: GirlRecord, parent=None):
        super().__init__(parent)
        self.repository = repository
        self.record = record
        self.setWindowTitle("Detail herečky")
        self.resize(620, 620)

        form = QFormLayout(self)

        self.name = QLineEdit(record.name, self)
        self.aliases = QLineEdit(", ".join(record.aliases), self)
        self.type_name = QComboBox(self)
        self.type_name.setEditable(True)
        self.type_name.addItems(repository.catalog_names("types"))
        self.type_name.setCurrentText(record.type_name)
        self.sex = self._choice(YES_VALUES, record.sex)
        self.nudity = self._choice(YES_VALUES, record.nudity)
        self.face = self._choice(FACE_VALUES, record.face)
        self.age_source = QLineEdit(record.age_source, self)
        self.nationality = QComboBox(self)
        self.nationality.setEditable(True)
        self.nationality.addItems(repository.catalog_names("nationalities"))
        self.nationality.setCurrentText(record.nationality)
        self.tags = QLineEdit(", ".join(record.tags), self)
        self.last_check = QLineEdit(record.last_check, self)
        self.occurrences = QLineEdit(str(record.occurrences), self)
        self.occurrences.setReadOnly(True)
        self.tracking = QLineEdit(str(record.tracking), self)
        self.tracking.setReadOnly(True)
        self.status = self._choice(GIRL_STATUS_VALUES, record.status)
        self.note = QTextEdit(self)
        self.note.setPlainText(record.note)

        form.addRow("Jméno:", self.name)
        form.addRow("Aliasy:", self.aliases)
        form.addRow("Typ:", self.type_name)
        form.addRow("Sex:", self.sex)
        form.addRow("Nahota:", self.nudity)
        form.addRow("Obličej:", self.face)
        form.addRow("Věk / rok narození:", self.age_source)
        form.addRow("Národnost:", self.nationality)
        form.addRow("Tagy:", self.tags)
        form.addRow("Sledování:", self.tracking)
        form.addRow("Posl. kontrola:", self.last_check)
        form.addRow("Počet výskytů:", self.occurrences)
        form.addRow("Stav:", self.status)
        form.addRow("Poznámka:", self.note)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, self)
        buttons.button(QDialogButtonBox.Save).setText("Uložit")
        buttons.button(QDialogButtonBox.Cancel).setText("Zrušit")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _choice(self, values: tuple[str, ...], current: str) -> QComboBox:
        combo = QComboBox(self)
        combo.addItems(values)
        combo.setCurrentText(current)
        return combo

    def save(self) -> None:
        values = {
            "name": self.name.text(),
            "type_name": self.type_name.currentText(),
            "sex": self.sex.currentText(),
            "nudity": self.nudity.currentText(),
            "face": self.face.currentText(),
            "age_source": self.age_source.text(),
            "nationality": self.nationality.currentText(),
            "last_check": self.last_check.text(),
            "status": self.status.currentText(),
            "note": self.note.toPlainText(),
        }
        for key, value in values.items():
            self.repository.update_field(self.record.id, key, value)
        self.repository.set_aliases(
            self.record.id,
            [value.strip() for value in self.aliases.text().split(",") if value.strip()],
        )
        allowed = set(self.repository.catalog_names("tags"))
        self.repository.set_tags(
            self.record.id,
            [value.strip() for value in self.tags.text().split(",") if value.strip() in allowed],
        )


class ScreenCropDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setCursor(Qt.CrossCursor)
        self._origin = QPoint()
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
            target = QRect(screen_geometry.topLeft() - geometry.topLeft(), screen_geometry.size())
            painter.drawPixmap(target, pixmap)
        painter.end()

        self.setGeometry(geometry)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self._screenshot)

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.LeftButton:
            return
        self._start = event.position().toPoint()
        self._rubber.setGeometry(QRect(self._start, self._start))
        self._rubber.show()

    def mouseMoveEvent(self, event) -> None:
        if not self._rubber.isVisible():
            return
        self._rubber.setGeometry(QRect(self._start, event.position().toPoint()).normalized())

    def mouseReleaseEvent(self, event) -> None:
        if event.button() != Qt.LeftButton or not self._rubber.isVisible():
            return
        rect = self._rubber.geometry().normalized()
        if rect.width() >= 5 and rect.height() >= 5:
            self.result_pixmap = self._screenshot.copy(rect)
            self.accept()
        else:
            self._rubber.hide()
