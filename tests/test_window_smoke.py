import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from latflix2.database import Repository
from latflix2.window import MainWindow


def test_main_window_starts_with_core_legacy_layout(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    repository = Repository(tmp_path / "latflix2.db")

    window = MainWindow(repository)
    try:
        assert window.current_category == "Girls"
        assert window.table.model() is window.proxy
        assert window.detail.isVisible() is False or window.detail.height() > 0

        menus = [action.text() for action in window.menuBar().actions()]
        assert menus == ["Soubor", "Úpravy", "Zobrazení", "Nastavení", "Nápověda"]

        assert window.record_count_label.text().startswith("Záznamů:")
        assert window.average_age_label.text().startswith("Průměrný věk:")
        assert "0.3.0" in window.build_label.text()
        assert window.detail.links_button.text() == "Odkazy"
        assert window.detail.detail_button.text() == "Detail"
        assert window.detail.show_links_button.text() == "Zobrazit odkazy"
        assert window.detail.favorite_button.text() == "☆ Oblíbené"
        assert window.detail.height() == window.detail.GIRL_DETAIL_HEIGHT
    finally:
        window.close()
        app.processEvents()
