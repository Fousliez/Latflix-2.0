import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from latflix2.database import Repository
from latflix2.window import MainWindow


def test_main_window_starts_with_new_model_view_layout(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    repository = Repository(tmp_path / "latflix2.db")
    window = MainWindow(repository)
    try:
        app.processEvents()
        assert window.current_category == "Girls"
        assert window.table.model() is window.proxy
        assert window.proxy.sourceModel() is window.model
        assert window.detail.height() == 136

        menus = [action.text() for action in window.menuBar().actions()]
        assert menus == ["Soubor", "Úpravy", "Nástroje", "Zobrazení", "Nastavení", "Nápověda"]

        assert window.toolbar.add_button.isEnabled()
        assert window.toolbar.delete_button.isEnabled()
        assert window.average_age_label.text().startswith("Průměrný věk:")

        window.load_category("Oblíbené")
        app.processEvents()
        assert not window.toolbar.add_button.isEnabled()
        assert not window.toolbar.delete_button.isEnabled()
    finally:
        window.close()
        app.processEvents()
