from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from .database import Repository


class OverviewPanel(QWidget):
    category_requested = Signal(str)

    ORDER = ("Girls", "Oblíbené", "Videa", "Odkazy", "Studia", "Tagy")

    def __init__(self, repository: Repository, parent=None):
        super().__init__(parent)
        self.repository = repository
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        title = QLabel("Přehled databáze", self)
        title.setObjectName("overviewTitle")
        root.addWidget(title)

        self.grid = QGridLayout()
        self.grid.setSpacing(10)
        root.addLayout(self.grid)
        root.addStretch(1)
        self.cards: dict[str, tuple[QFrame, QLabel]] = {}

        for index, category in enumerate(self.ORDER):
            frame = QFrame(self)
            frame.setObjectName("overviewCard")
            layout = QVBoxLayout(frame)
            label = QLabel(category, frame)
            label.setObjectName("overviewCardTitle")
            count = QLabel("0", frame)
            count.setObjectName("overviewCount")
            button = QPushButton("Otevřít", frame)
            button.clicked.connect(lambda checked=False, name=category: self.category_requested.emit(name))
            layout.addWidget(label)
            layout.addWidget(count)
            layout.addStretch(1)
            layout.addWidget(button)
            self.grid.addWidget(frame, index // 3, index % 3)
            self.cards[category] = (frame, count)

    def refresh(self) -> None:
        counts = self.repository.overview_counts()
        for category, (_frame, label) in self.cards.items():
            label.setText(str(counts.get(category, 0)))
