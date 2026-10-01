import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from latflix2.database import Repository
from latflix2.spec_dialog import DocumentationDialog
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


def test_project_documentation_dialog_reads_live_markdown(tmp_path: Path):
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


def test_help_menu_contains_project_documentation_actions(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    repository = Repository(tmp_path / "latflix2.db")
    window = MainWindow(repository)
    try:
        help_menu = window.menuBar().actions()[-1].menu()
        texts = [action.text() for action in help_menu.actions()]
        assert "Specifikace Latflixu" in texts
        assert "Stav implementace" in texts
        assert "O aplikaci" in texts
    finally:
        window.close()
        app.processEvents()
