import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from latflix21.db import Repository
from latflix21.window import MainWindow


def test_latflix21_window_smoke(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    repo = Repository(tmp_path / "latflix21.db")
    window = MainWindow(repo)

    for section in (
        "Přehled", "Girls", "Oblíbené", "Odkazy", "Videa",
        "Super", "Studia", "Stavy", "Kvality", "Tagy", "Typy", "Národnosti",
    ):
        window.navigate(section)
        assert window.stack.currentWidget() is window.pages[section]

    window.close()
    app.processEvents()
