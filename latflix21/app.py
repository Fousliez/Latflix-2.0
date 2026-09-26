from __future__ import annotations
import sys
from PySide6.QtWidgets import QApplication
from .config import APP_NAME, database_path
from .db import Repository
from .window import MainWindow

def run()->int:
    app=QApplication(sys.argv);app.setApplicationName(APP_NAME);app.setOrganizationName("Latflix");window=MainWindow(Repository(database_path()));window.showMaximized();return app.exec()
