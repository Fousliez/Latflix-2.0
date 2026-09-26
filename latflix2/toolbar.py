from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QMenu,
    QPushButton,
    QToolButton,
    QWidget,
)


class TableToolbar(QWidget):
    add_one = Signal()
    add_many = Signal(int)
    delete_requested = Signal()
    bulk_favorite = Signal(bool)
    bulk_links = Signal()
    search_changed = Signal(str)
    clear_search = Signal()
    clear_all = Signal()
    filter_requested = Signal(str, object)

    HEIGHT = 30

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        self.add_button = QToolButton(self)
        self.add_button.setObjectName("addSplitButton")
        self.add_button.setText("Přidat")
        self.add_button.setPopupMode(QToolButton.MenuButtonPopup)
        add_menu = QMenu(self.add_button)
        add_menu.addAction("Přidat 5 řádků", lambda: self.add_many.emit(5))
        add_menu.addAction("Přidat 10 řádků", lambda: self.add_many.emit(10))
        self.add_button.setMenu(add_menu)
        self.add_button.clicked.connect(self.add_one.emit)
        layout.addWidget(self.add_button)

        self.delete_button = QPushButton("Smazat", self)
        self.delete_button.clicked.connect(self.delete_requested.emit)
        layout.addWidget(self.delete_button)

        self.bulk_button = QPushButton("Hromadné akce", self)
        self.bulk_menu = QMenu(self.bulk_button)
        self.bulk_menu.addAction("Přidat do Oblíbených", lambda: self.bulk_favorite.emit(True))
        self.bulk_menu.addAction("Odebrat z Oblíbených", lambda: self.bulk_favorite.emit(False))
        self.bulk_menu.addSeparator()
        self.bulk_menu.addAction("Hromadně přidat odkazy", self.bulk_links.emit)
        self.bulk_button.clicked.connect(
            lambda: self.bulk_menu.exec(self.bulk_button.mapToGlobal(self.bulk_button.rect().bottomLeft()))
        )
        layout.addWidget(self.bulk_button)

        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Hledat…")
        self.search.setMinimumWidth(190)
        self.search.setMaximumWidth(250)
        self.search.textChanged.connect(self.search_changed.emit)
        layout.addWidget(self.search)

        self.search_clear = QPushButton("🗑", self)
        self.search_clear.setObjectName("searchClearButton")
        self.search_clear.setFixedWidth(self.HEIGHT)
        self.search_clear.clicked.connect(self._clear_search)
        layout.addWidget(self.search_clear)

        self.filter_buttons: dict[str, QPushButton] = {}
        for key, title in (
            ("nationality", "Národnost"),
            ("type_name", "Typ"),
            ("status", "Stav"),
            ("sex", "Sex"),
            ("nudity", "Nahota"),
            ("face", "Obličej"),
            ("profile", "Profilovka"),
        ):
            button = QPushButton(title, self)
            button.setProperty("filterKey", key)
            button.clicked.connect(lambda _checked=False, k=key, b=button: self.filter_requested.emit(k, b))
            self.filter_buttons[key] = button
            layout.addWidget(button)

        layout.addStretch(1)
        self.clear_button = QPushButton("Vyčistit", self)
        self.clear_button.clicked.connect(self.clear_all.emit)
        layout.addWidget(self.clear_button)

        for widget in self.findChildren((QPushButton, QToolButton, QLineEdit)):
            widget.setFixedHeight(self.HEIGHT)

    def _clear_search(self) -> None:
        self.search.clear()
        self.clear_search.emit()

    def set_favorites_mode(self, enabled: bool) -> None:
        self.add_button.setEnabled(not enabled)
        self.delete_button.setEnabled(not enabled)

    def update_filter_label(self, key: str, title: str, value: str) -> None:
        button = self.filter_buttons.get(key)
        if button is not None:
            button.setText(f"{title}: {value}" if value else title)

    def clear_filter_labels(self) -> None:
        titles = {
            "nationality": "Národnost",
            "type_name": "Typ",
            "status": "Stav",
            "sex": "Sex",
            "nudity": "Nahota",
            "face": "Obličej",
            "profile": "Profilovka",
        }
        for key, title in titles.items():
            self.update_filter_label(key, title, "")
