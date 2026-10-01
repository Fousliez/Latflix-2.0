import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from latflix21.db import Repository
from latflix21.spec_dialog import DocumentationDialog
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


def test_latflix21_documentation_dialog_reads_live_markdown():
    app = QApplication.instance() or QApplication([])
    project_root = Path(__file__).resolve().parents[1]
    dialog = DocumentationDialog(project_root=project_root)
    try:
        app.processEvents()
        assert "Latflix 2.0" in dialog.spec_pane.raw_text
        assert "implementační checklist" in dialog.checklist_pane.raw_text
        assert dialog.spec_pane.contents.count() > 10
        assert dialog.checklist_pane.contents.count() > 5
        assert "Hotovo:" in dialog.checklist_pane.summary.text()

        dialog.set_initial_tab("checklist")
        assert dialog.tabs.currentIndex() == dialog.CHECKLIST_TAB
    finally:
        dialog.close()
        app.processEvents()


def test_latflix21_help_menu_contains_documentation_actions(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    repo = Repository(tmp_path / "latflix21.db")
    window = MainWindow(repo)
    try:
        help_menu = window.menuBar().actions()[-1].menu()
        texts = [action.text() for action in help_menu.actions()]
        assert "Specifikace Latflixu" in texts
        assert "Stav implementace" in texts
        assert "O aplikaci" in texts
    finally:
        window.close()
        app.processEvents()
