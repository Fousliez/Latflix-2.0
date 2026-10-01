import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLineEdit

from latflix21.db import Repository
from latflix21.window import MainWindow


def _editor_line(table):
    for editor in table.viewport().findChildren(QLineEdit):
        if editor.property("row") is not None:
            return editor
    return None


def test_header_titles_and_hidden_columns_restore_for_all_table_sections(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    repo = Repository(tmp_path / "latflix21.db")
    window = MainWindow(repo)
    settings = QSettings(str(tmp_path / "table-state.ini"), QSettings.IniFormat)

    try:
        for name, page in window.pages.items():
            if not hasattr(page, "table"):
                continue
            table = page.table
            table._settings = settings
            source = table.model().sourceModel()
            if source.columnCount() <= 2:
                continue

            logical = 2
            key = source.col(logical).key
            expected = f"TEST-{name}"
            prefix = table._settings_prefix()
            settings.setValue(f"{prefix}/title/{key}", expected)
            table.setColumnHidden(logical, True)
            table._save_layout()

            source.title_overrides.clear()
            table.setColumnHidden(logical, False)
            table.restore_layout()

            assert source.headerData(logical, Qt.Horizontal, Qt.DisplayRole) == expected
            assert table.isColumnHidden(logical)

        settings.sync()
    finally:
        window.close()
        app.processEvents()


def test_text_enter_moves_exactly_one_row(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    repo = Repository(tmp_path / "latflix21.db")
    repo.add_girls(3)
    window = MainWindow(repo)
    try:
        page = window.pages["Girls"]
        page.refresh()
        table = page.table
        index = table.model().index(0, 2)
        table.setCurrentIndex(index)
        table.edit(index)
        app.processEvents()

        editor = _editor_line(table)
        assert editor is not None
        QTest.keyClick(editor, Qt.Key_Return)
        app.processEvents()
        QTest.qWait(10)
        app.processEvents()

        assert table.currentIndex().row() == 1
        assert table.currentIndex().column() == 2
    finally:
        window.close()
        app.processEvents()
