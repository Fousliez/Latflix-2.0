from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from .schema import HELPER_SECTIONS, MAIN_SECTIONS


class Sidebar(QWidget):
    category_changed = Signal(str)
    quick_tag_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.expanded_width = 156
        self.collapsed_width = 30
        self.is_collapsed = False
        self.buttons: dict[str, QPushButton] = {}
        self.quick_buttons: list[QPushButton] = []

        self.setObjectName("sidebarPanel")
        self._set_width(self.expanded_width)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self.toggle_button = QPushButton("◀", self)
        self.toggle_button.setObjectName("sidebarToggle")
        self.toggle_button.setFixedHeight(27)
        self.toggle_button.clicked.connect(self.toggle_sidebar)
        layout.addWidget(self.toggle_button)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)

        for name in MAIN_SECTIONS:
            layout.addWidget(self._make_button(name))

        layout.addStretch(1)

        for name in HELPER_SECTIONS:
            layout.addWidget(self._make_button(name))

        self.quick_label = QLabel("Rychlé filtry", self)
        self.quick_label.setObjectName("quickFiltersLabel")
        layout.addWidget(self.quick_label)

        for tag in ("Latex", "Ruined"):
            button = QPushButton(tag, self)
            button.setObjectName("quickFilterButton")
            button.setFixedHeight(27)
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda _checked=False, value=tag: self.quick_tag_selected.emit(value))
            layout.addWidget(button)
            self.quick_buttons.append(button)

    def _make_button(self, name: str) -> QPushButton:
        button = QPushButton(name, self)
        button.setObjectName("categoryButton")
        button.setCheckable(True)
        button.setFixedHeight(29)
        button.setCursor(Qt.PointingHandCursor)
        self.group.addButton(button)
        button.clicked.connect(lambda _checked=False, value=name: self.category_changed.emit(value))
        self.buttons[name] = button
        return button

    def set_active(self, name: str) -> None:
        button = self.buttons.get(name)
        if button is not None:
            button.setChecked(True)

    def _set_width(self, width: int) -> None:
        self.setFixedWidth(width)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

    def toggle_sidebar(self) -> None:
        self.is_collapsed = not self.is_collapsed
        widgets = [*self.buttons.values(), *self.quick_buttons, self.quick_label]
        for widget in widgets:
            widget.setVisible(not self.is_collapsed)
        self._set_width(self.collapsed_width if self.is_collapsed else self.expanded_width)
        self.toggle_button.setText("▶" if self.is_collapsed else "◀")
