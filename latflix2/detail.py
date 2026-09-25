from __future__ import annotations

from collections import Counter, defaultdict

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .database import Dataset, Row
from .flow_layout import FlowLayout


GIRL_CATEGORIES = {"Girls", "Oblíbené"}


class PersonDetail(QFrame):
    favorite_changed = Signal(int, bool)
    rating_changed = Signal(int, int)
    links_requested = Signal(int)
    detail_requested = Signal(int)
    show_links_requested = Signal(int)

    GIRL_DETAIL_HEIGHT = 136
    GIRL_PHOTO_WIDTH = 72
    GIRL_PHOTO_HEIGHT = 96
    GIRL_ACTION_BUTTON_HEIGHT = 26
    LINK_ROW_HEIGHT = 23

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("detailBox")
        self._record_id: int | None = None
        self._favorite = False
        self._rating = 0
        self._category = "Girls"

        root = QHBoxLayout(self)
        root.setContentsMargins(8, 3, 8, 3)
        root.setSpacing(10)

        self.photo = QLabel("FOTKA", self)
        self.photo.setObjectName("profilePhoto")
        self.photo.setAlignment(Qt.AlignCenter)
        self.photo.setFixedSize(self.GIRL_PHOTO_WIDTH, self.GIRL_PHOTO_HEIGHT)
        root.addWidget(self.photo, 0, Qt.AlignTop)

        center = QWidget(self)
        center.setObjectName("detailCenter")
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(1)

        self.name = QLabel("Vyber dívku", center)
        self.name.setObjectName("detailName")
        center_layout.addWidget(self.name)

        self.rating_controls = QWidget(center)
        rating_layout = QHBoxLayout(self.rating_controls)
        rating_layout.setContentsMargins(0, 0, 0, 0)
        rating_layout.setSpacing(1)
        self.star_buttons: list[QPushButton] = []
        for value in range(1, 6):
            button = QPushButton("☆", self.rating_controls)
            button.setObjectName("ratingStar")
            button.setFlat(True)
            button.setFixedSize(30, 30)
            button.setToolTip(f"Nastavit hodnocení na {value} z 5")
            button.clicked.connect(
                lambda checked=False, rating=value: self._choose_rating(rating)
            )
            rating_layout.addWidget(button)
            self.star_buttons.append(button)

        self.favorite_button = QPushButton("☆ Oblíbené", self.rating_controls)
        self.favorite_button.setObjectName("favoriteButton")
        self.favorite_button.setCheckable(True)
        self.favorite_button.setMinimumHeight(30)
        self.favorite_button.setToolTip("Přidat nebo odebrat dívku z oblíbených")
        self.favorite_button.clicked.connect(self._toggle_favorite)
        rating_layout.addWidget(self.favorite_button)
        rating_layout.addStretch(1)
        center_layout.addWidget(self.rating_controls)

        self.metadata_widget = QWidget(center)
        self.metadata_widget.setObjectName("metadataRow")
        metadata_layout = QHBoxLayout(self.metadata_widget)
        metadata_layout.setContentsMargins(0, 0, 0, 0)
        metadata_layout.setSpacing(5)
        self.age_group, self.age_value = self._metadata_pill("Věk", self.metadata_widget)
        self.occurrence_group, self.occurrence_value = self._metadata_pill(
            "Počet výskytů",
            self.metadata_widget,
        )
        metadata_layout.addWidget(self.age_group)
        metadata_layout.addWidget(self.occurrence_group)
        metadata_layout.addStretch(1)
        self.metadata_widget.setFixedHeight(21)
        center_layout.addWidget(self.metadata_widget)

        self.links_widget = QWidget(center)
        self.links_widget.setObjectName("girlAssignedLinksFlow")
        self.links_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.links_flow = FlowLayout(
            self.links_widget,
            margin=0,
            horizontal_spacing=8,
            vertical_spacing=3,
        )
        self.links_widget.setLayout(self.links_flow)
        self.links_widget.hide()
        center_layout.addWidget(self.links_widget)
        center_layout.addStretch(1)
        root.addWidget(center, 1)

        right_wrapper = QWidget(self)
        right_layout = QHBoxLayout(right_wrapper)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)

        self.missing_sources = QWidget(right_wrapper)
        self.missing_sources.setObjectName("missingSources")
        self.missing_layout = QVBoxLayout(self.missing_sources)
        self.missing_layout.setContentsMargins(0, 0, 0, 0)
        self.missing_layout.setSpacing(3)
        self.missing_layout.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.missing_sources.hide()
        right_layout.addWidget(self.missing_sources, 0, Qt.AlignTop)

        actions = QVBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(4)
        actions.setAlignment(Qt.AlignTop)

        self.links_button = QPushButton("Odkazy", right_wrapper)
        self.detail_button = QPushButton("Detail", right_wrapper)
        self.show_links_button = QPushButton("Zobrazit odkazy", right_wrapper)
        self.links_button.setToolTip("Zobrazit a upravit všechny odkazy vybrané herečky")
        self.detail_button.setToolTip("Otevřít detail vybrané herečky")
        self.show_links_button.setToolTip(
            "Přejít do sekce Odkazy a zobrazit jen odkazy této herečky"
        )
        for button in (
            self.links_button,
            self.detail_button,
            self.show_links_button,
        ):
            button.setMinimumWidth(112)
            button.setMinimumHeight(self.GIRL_ACTION_BUTTON_HEIGHT)
            button.setMaximumHeight(self.GIRL_ACTION_BUTTON_HEIGHT)
            actions.addWidget(button)

        self.links_button.clicked.connect(
            lambda: self._emit_record_signal(self.links_requested)
        )
        self.detail_button.clicked.connect(
            lambda: self._emit_record_signal(self.detail_requested)
        )
        self.show_links_button.clicked.connect(
            lambda: self._emit_record_signal(self.show_links_requested)
        )
        actions.addStretch(1)
        right_layout.addLayout(actions)
        root.addWidget(right_wrapper, 0, Qt.AlignTop)

        self.show_category("Girls")

    @staticmethod
    def _metadata_pill(title: str, parent: QWidget) -> tuple[QWidget, QLabel]:
        group = QWidget(parent)
        group.setObjectName("metadataPillGroup")
        layout = QHBoxLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        key = QLabel(f"{title}:", group)
        key.setObjectName("metadataKey")
        value = QLabel("—", group)
        value.setObjectName("metadataValue")
        value.setToolTip(f"{title}: —")
        layout.addWidget(key)
        layout.addWidget(value)
        return group, value

    @staticmethod
    def _column_map(dataset: Dataset, row: Row) -> dict[str, str]:
        return {
            column.name: row.values[index] if index < len(row.values) else ""
            for index, column in enumerate(dataset.columns)
        }

    def show_category(self, category: str) -> None:
        self._category = category
        self._record_id = None
        is_girl = category in GIRL_CATEGORIES
        self.photo.setVisible(is_girl)
        self.rating_controls.setVisible(False)
        self.metadata_widget.setVisible(False)
        self._clear_link_chips()
        self._set_missing_sources([])
        self.name.setText("Vyber dívku" if is_girl else category)
        self._set_action_state(is_girl, False)
        self.setFixedHeight(self.GIRL_DETAIL_HEIGHT if is_girl else 88)

    def show_record(
        self,
        dataset: Dataset,
        row: Row,
        links: list[dict[str, str]] | None = None,
        missing_sources: list[str] | None = None,
    ) -> None:
        self._category = dataset.category
        self._record_id = row.id
        values = self._column_map(dataset, row)
        is_girl = dataset.category in GIRL_CATEGORIES

        title_key = "Jméno" if is_girl else "Název"
        self.name.setText(values.get(title_key, "") or f"Záznam #{row.id}")

        if not is_girl:
            self.photo.hide()
            self.rating_controls.hide()
            self.metadata_widget.hide()
            self._clear_link_chips()
            self._set_missing_sources([])
            self._set_action_state(False, False)
            self.setFixedHeight(88)
            return

        self.photo.show()
        self.rating_controls.show()
        self.metadata_widget.show()

        age = str(values.get("Věk", "")).strip() or "—"
        occurrence = str(values.get("Počet výskytů", "")).strip() or "—"
        self.age_value.setText(age)
        self.age_value.setToolTip(f"Věk: {age}")
        self.occurrence_value.setText(occurrence)
        self.occurrence_value.setToolTip(f"Počet výskytů: {occurrence}")

        try:
            self._rating = max(0, min(5, int(values.get("Hodnocení", "") or 0)))
        except ValueError:
            self._rating = 0
        self._favorite = row.id in dataset.favorite_ids
        self._refresh_person_controls()
        self._set_action_state(True, True)
        self._set_link_chips(links or [])
        self._set_missing_sources(missing_sources or [])
        self._refresh_dynamic_height()

    def _set_action_state(self, visible: bool, enabled: bool) -> None:
        for button in (
            self.links_button,
            self.detail_button,
            self.show_links_button,
        ):
            button.setVisible(visible)
            button.setEnabled(enabled)

    def _refresh_person_controls(self) -> None:
        self.favorite_button.blockSignals(True)
        self.favorite_button.setChecked(self._favorite)
        self.favorite_button.setText(
            "★ V oblíbených" if self._favorite else "☆ Oblíbené"
        )
        self.favorite_button.blockSignals(False)
        for index, button in enumerate(self.star_buttons, start=1):
            button.setText("★" if index <= self._rating else "☆")
            button.setProperty("activeRating", index <= self._rating)
            button.style().unpolish(button)
            button.style().polish(button)

    def _clear_link_chips(self) -> None:
        self.links_flow.clear()
        self.links_widget.hide()
        self.links_widget.setFixedHeight(0)

    def _set_link_chips(self, links: list[dict[str, str]]) -> None:
        self._clear_link_chips()
        counts = Counter()
        types_by_site: dict[str, set[str]] = defaultdict(set)
        urls_by_site: dict[str, list[str]] = defaultdict(list)

        for link in links:
            site = str(link.get("site", "") or "").strip() or "Bez názvu"
            counts[site] += 1
            types_by_site[site].add(str(link.get("type_label", "") or "Odkaz"))
            url = str(link.get("url", "") or "").strip()
            if url:
                urls_by_site[site].append(url)

        ordered = sorted(counts, key=lambda site: (-counts[site], site.casefold()))
        for site in ordered:
            count = counts[site]
            urls = tuple(urls_by_site[site])
            text = f"{site} ({count})" if count > 1 else site
            button = QToolButton(self.links_widget)
            button.setObjectName("girlAssignedLinkChip")
            button.setText(text)
            button.setFixedHeight(self.LINK_ROW_HEIGHT)
            button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            button.setCursor(Qt.PointingHandCursor if urls else Qt.ArrowCursor)
            tooltip = ", ".join(sorted(types_by_site[site], key=str.casefold))
            if urls:
                tooltip += "\n" + "\n".join(urls)
                button.clicked.connect(
                    lambda checked=False, targets=urls: self._open_urls(targets)
                )
            else:
                tooltip += "\nURL není vyplněná."
                button.setEnabled(False)
            button.setToolTip(tooltip)
            self.links_flow.addWidget(button)

        self.links_widget.setVisible(bool(ordered))

    def _set_missing_sources(self, names: list[str]) -> None:
        while self.missing_layout.count():
            item = self.missing_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for name in names:
            badge = QLabel(str(name), self.missing_sources)
            badge.setObjectName("missingSourceBadge")
            badge.setToolTip(f"Zdroj {name} zatím není přiřazen této herečce")
            self.missing_layout.addWidget(badge)
        self.missing_sources.setVisible(bool(names))

    def _open_urls(self, urls: tuple[str, ...]) -> None:
        for raw in urls:
            text = str(raw or "").strip()
            if text:
                QDesktopServices.openUrl(QUrl.fromUserInput(text))

    def _emit_record_signal(self, signal: Signal) -> None:
        if self._record_id is not None:
            signal.emit(int(self._record_id))

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

    def _refresh_dynamic_height(self) -> None:
        if self._category not in GIRL_CATEGORIES:
            return
        width = max(280, self.links_widget.width())
        link_height = (
            max(self.LINK_ROW_HEIGHT, self.links_flow.heightForWidth(width))
            if self.links_flow.count()
            else 0
        )
        self.links_widget.setFixedHeight(link_height)
        extra = max(0, link_height - self.LINK_ROW_HEIGHT)
        self.setFixedHeight(self.GIRL_DETAIL_HEIGHT + extra)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._category in GIRL_CATEGORIES and self.links_flow.count():
            self._refresh_dynamic_height()
