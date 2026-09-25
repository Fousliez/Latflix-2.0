from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .config import APP_NAME, database_path
from .database import Repository
from .window import MainWindow


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("Latflix")
    repository = Repository(database_path())
    window = MainWindow(repository)
    window.showMaximized()
    return app.exec()
