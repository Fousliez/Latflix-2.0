from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from .database import Dataset, Row


class PersonDetail(QFrame):
    favorite_changed = Signal(int, bool)
    rating_changed = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("detailBox")
        self._record_id: int | None = None
        self._favorite = False
        self._rating = 0

        root = QHBoxLayout(self)
        root.setContentsMargins(8, 5, 8, 5)
        root.setSpacing(10)

        self.photo = QLabel("FOTO", self)
        self.photo.setObjectName("profilePhoto")
        self.photo.setAlignment(Qt.AlignCenter)
        self.photo.setFixedSize(72, 96)
        root.addWidget(self.photo)

        center = QWidget(self)
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(2)

        self.name = QLabel("Girls", center)
        self.name.setObjectName("detailName")
        center_layout.addWidget(self.name)

        self.meta = QLabel("", center)
        self.meta.setObjectName("detailMeta")
        center_layout.addWidget(self.meta)

        stars = QHBoxLayout()
        stars.setSpacing(1)
        self.star_buttons: list[QPushButton] = []
        for value in range(1, 6):
            button = QPushButton("☆", center)
            button.setObjectName("ratingStar")
            button.setFixedSize(27, 25)
            button.clicked.connect(lambda checked=False, rating=value: self._choose_rating(rating))
            stars.addWidget(button)
            self.star_buttons.append(button)
        self.favorite_button = QPushButton("☆ Oblíbené", center)
        self.favorite_button.setObjectName("favoriteButton")
        self.favorite_button.setCheckable(True)
        self.favorite_button.setMinimumHeight(28)
        self.favorite_button.clicked.connect(self._toggle_favorite)
        stars.addWidget(self.favorite_button)
        stars.addStretch(1)
        center_layout.addLayout(stars)

        self.summary = QLabel("", center)
        self.summary.setObjectName("detailSummary")
        self.summary.setWordWrap(True)
        center_layout.addWidget(self.summary)
        center_layout.addStretch(1)
        root.addWidget(center, 1)

        actions = QVBoxLayout()
        actions.setSpacing(5)
        self.links_button = QPushButton("Odkazy", self)
        self.detail_button = QPushButton("Detail", self)
        for button in (self.links_button, self.detail_button):
            button.setFixedHeight(26)
            button.setMinimumWidth(105)
            actions.addWidget(button)
        actions.addStretch(1)
        root.addLayout(actions)

        self.show_category("Girls")

    @staticmethod
    def _column_map(dataset: Dataset, row: Row) -> dict[str, str]:
        return {
            column.name: row.values[index] if index < len(row.values) else ""
            for index, column in enumerate(dataset.columns)
        }

    def show_category(self, category: str) -> None:
        self._record_id = None
        self.photo.setVisible(category in {"Girls", "Oblíbené"})
        self.name.setText(category)
        self.meta.clear()
        self.summary.clear()
        self.favorite_button.setVisible(category in {"Girls", "Oblíbené"})
        self.links_button.setVisible(category in {"Girls", "Oblíbené"})
        self.detail_button.setVisible(category in {"Girls", "Oblíbené"})
        for button in self.star_buttons:
            button.setVisible(category in {"Girls", "Oblíbené"})
        self.setFixedHeight(136 if category in {"Girls", "Oblíbené"} else 88)

    def show_record(self, dataset: Dataset, row: Row) -> None:
        self._record_id = row.id
        values = self._column_map(dataset, row)
        title_key = "Jméno" if dataset.category in {"Girls", "Oblíbené"} else "Název"
        self.name.setText(values.get(title_key, "") or f"Záznam #{row.id}")

        if dataset.category in {"Girls", "Oblíbené"}:
            age = values.get("Věk", "").strip() or "—"
            nationality = values.get("Národnost", "").strip() or "—"
            girl_type = values.get("Typ", "").strip() or "—"
            self.meta.setText(f"Věk:  {age}     Národnost:  {nationality}     Typ:  {girl_type}")
            state = values.get("Stav", "").strip()
            tags = values.get("Tagy", "").strip()
            parts = [part for part in (state, tags) if part]
            self.summary.setText(" • ".join(parts))
            try:
                self._rating = max(0, min(5, int(values.get("Hodnocení", "") or 0)))
            except ValueError:
                self._rating = 0
            self._favorite = row.id in dataset.favorite_ids
            self._refresh_person_controls()
        else:
            nonempty = [
                f"{key}: {value}"
                for key, value in values.items()
                if key != title_key and str(value).strip()
            ]
            self.meta.setText("   •   ".join(nonempty[:4]))
            self.summary.setText("   •   ".join(nonempty[4:8]))

    def _refresh_person_controls(self) -> None:
        self.favorite_button.blockSignals(True)
        self.favorite_button.setChecked(self._favorite)
        self.favorite_button.setText("★ V oblíbených" if self._favorite else "☆ Oblíbené")
        self.favorite_button.blockSignals(False)
        for index, button in enumerate(self.star_buttons, start=1):
            button.setText("★" if index <= self._rating else "☆")

    def _toggle_favorite(self, checked=False) -> None:
        if self._record_id is None:
            return
        self._favorite = bool(checked)
        self._refresh_person_controls()
        self.favorite_changed.emit(self._record_id, self._favorite)

    def _choose_rating(self, rating: int) -> None:
        if self._record_id is None:
            return
        self._rating = 0 if self._rating == rating else rating
        self._refresh_person_controls()
        self.rating_changed.emit(self._record_id, self._rating)
