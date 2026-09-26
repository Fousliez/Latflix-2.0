from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .database import GirlRecord, LinkRecord
from .flow_layout import FlowLayout


class ProfileButton(QPushButton):
    choose_requested = Signal()
    crop_requested = Signal()
    delete_requested = Signal()

    def __init__(self, parent=None):
        super().__init__("FOTKA", parent)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.choose_requested.emit)
        self._double = False

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self._timer.stop()
            self.delete_requested.emit()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._double = True
            self._timer.stop()
            self.crop_requested.emit()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton:
            if self._double:
                self._double = False
            else:
                self._timer.start(QApplication.doubleClickInterval() + 20)


class PersonDetail(QFrame):
    favorite_changed = Signal(int, bool)
    links_requested = Signal(int)
    detail_requested = Signal(int)
    show_links_requested = Signal(int)
    photo_choose_requested = Signal(int)
    photo_crop_requested = Signal(int)
    photo_delete_requested = Signal(int)

    HEIGHT = 136

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("detailPanel")
        self.setFixedHeight(self.HEIGHT)
        self._record_id: int | None = None

        root = QHBoxLayout(self)
        root.setContentsMargins(8, 7, 8, 7)
        root.setSpacing(10)

        self.photo = ProfileButton(self)
        self.photo.setObjectName("profilePhoto")
        self.photo.setFixedSize(74, 118)
        self.photo.choose_requested.connect(lambda: self._emit(self.photo_choose_requested))
        self.photo.crop_requested.connect(lambda: self._emit(self.photo_crop_requested))
        self.photo.delete_requested.connect(lambda: self._emit(self.photo_delete_requested))
        root.addWidget(self.photo, 0, Qt.AlignTop)

        center = QWidget(self)
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(3)

        headline = QHBoxLayout()
        self.name = QLabel("Vyber herečku", center)
        self.name.setObjectName("detailName")
        headline.addWidget(self.name)

        self.favorite = QPushButton("☆ Oblíbené", center)
        self.favorite.setObjectName("favoriteButton")
        self.favorite.setCheckable(True)
        self.favorite.clicked.connect(self._favorite_clicked)
        headline.addWidget(self.favorite)
        headline.addStretch(1)
        center_layout.addLayout(headline)

        metadata = QHBoxLayout()
        self.age = QLabel("<b>Věk:</b> —", center)
        self.occurrences = QLabel("<b>Počet výskytů:</b> 0", center)
        metadata.addWidget(self.age)
        metadata.addSpacing(10)
        metadata.addWidget(self.occurrences)
        metadata.addStretch(1)
        center_layout.addLayout(metadata)

        self.links_host = QWidget(center)
        self.links_host.setFixedHeight(55)
        self.links_flow = FlowLayout(self.links_host, margin=0, horizontal_spacing=5, vertical_spacing=4)
        center_layout.addWidget(self.links_host)
        center_layout.addStretch(1)

        root.addWidget(center, 1)

        actions = QVBoxLayout()
        actions.setSpacing(5)
        self.links_button = QPushButton("Odkazy", self)
        self.detail_button = QPushButton("Detail", self)
        self.show_links_button = QPushButton("Zobrazit odkazy", self)
        for button in (self.links_button, self.detail_button, self.show_links_button):
            button.setFixedHeight(29)
            actions.addWidget(button)
        self.links_button.clicked.connect(lambda: self._emit(self.links_requested))
        self.detail_button.clicked.connect(lambda: self._emit(self.detail_requested))
        self.show_links_button.clicked.connect(lambda: self._emit(self.show_links_requested))
        actions.addStretch(1)
        root.addLayout(actions)

        self.clear()

    def _emit(self, signal: Signal) -> None:
        if self._record_id is not None:
            signal.emit(int(self._record_id))

    def _favorite_clicked(self, checked: bool) -> None:
        if self._record_id is None:
            return
        self.favorite.setText("★ V oblíbených" if checked else "☆ Oblíbené")
        self.favorite_changed.emit(int(self._record_id), bool(checked))

    def clear(self) -> None:
        self._record_id = None
        self.name.setText("Vyber herečku")
        self.age.setText("<b>Věk:</b> —")
        self.occurrences.setText("<b>Počet výskytů:</b> 0")
        self.favorite.blockSignals(True)
        self.favorite.setChecked(False)
        self.favorite.setText("☆ Oblíbené")
        self.favorite.blockSignals(False)
        self.photo.setIcon(QIcon())
        self.photo.setText("FOTKA")
        self._clear_links()
        for button in (
            self.favorite,
            self.links_button,
            self.detail_button,
            self.show_links_button,
            self.photo,
        ):
            button.setEnabled(False)

    def _clear_links(self) -> None:
        self.links_flow.clear()

    def show_record(
        self,
        record: GirlRecord,
        links: tuple[LinkRecord, ...],
        source_rank: dict[str, int],
        display_age: str,
    ) -> None:
        self._record_id = record.id
        self.name.setText(record.name or "(bez jména)")
        self.age.setText(f"<b>Věk:</b> {display_age or '—'}")
        self.occurrences.setText(f"<b>Počet výskytů:</b> {record.occurrences}")

        self.favorite.blockSignals(True)
        self.favorite.setChecked(record.favorite)
        self.favorite.setText("★ V oblíbených" if record.favorite else "☆ Oblíbené")
        self.favorite.blockSignals(False)

        self.photo.setIcon(QIcon())
        self.photo.setText("FOTKA")
        path = Path(record.profile_path).expanduser() if record.profile_path else None
        if path and path.is_file():
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                self.photo.setText("")
                self.photo.setIcon(QIcon(pixmap))
                self.photo.setIconSize(self.photo.size())

        self._clear_links()
        grouped: dict[str, list[str]] = defaultdict(list)
        for link in links:
            grouped[link.source or "Odkaz"].append(link.url)

        ordered = sorted(
            grouped.items(),
            key=lambda item: (source_rank.get(item[0].casefold(), 999999), item[0].casefold()),
        )
        for source, urls in ordered:
            label = f"{source} ({len(urls)})" if len(urls) > 1 else source
            button = QPushButton(label, self.links_host)
            button.setObjectName("linkChip")
            button.setFixedHeight(24)
            button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            targets = tuple(url for url in urls if url.strip())
            if targets:
                button.clicked.connect(lambda _checked=False, values=targets: self._open_urls(values))
            else:
                button.setEnabled(False)
            self.links_flow.addWidget(button)

        for button in (
            self.favorite,
            self.links_button,
            self.detail_button,
            self.show_links_button,
            self.photo,
        ):
            button.setEnabled(True)

    @staticmethod
    def _open_urls(urls: tuple[str, ...]) -> None:
        for raw in urls:
            value = str(raw or "").strip()
            if value:
                QDesktopServices.openUrl(QUrl.fromUserInput(value))
