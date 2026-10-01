from __future__ import annotations

import os
import re
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)


HEADING_RE = re.compile(r"^(#{1,4})\\s+(.+?)\\s*$", re.MULTILINE)
DONE_RE = re.compile(r"^- \\[x\\]", re.MULTILINE | re.IGNORECASE)
OPEN_RE = re.compile(r"^- \\[ \\]", re.MULTILINE)


def find_project_root(explicit: Path | None = None) -> Path:
    """Najde kořen checkoutu bez vytváření druhé kopie dokumentace."""
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(Path(explicit).expanduser().resolve())

    env_root = os.environ.get("LATFLIX_PROJECT_ROOT", "").strip()
    if env_root:
        candidates.append(Path(env_root).expanduser().resolve())

    candidates.extend(
        [
            Path(__file__).resolve().parents[1],
            Path.cwd().resolve(),
        ]
    )

    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if (
            (candidate / "docs" / "SPEC_LATFLIX_2.md").is_file()
            and (candidate / "docs" / "IMPLEMENTATION_CHECKLIST_2_1.md").is_file()
        ):
            return candidate

    # Vracíme očekávanou cestu, aby chyba v GUI byla konkrétní.
    return candidates[0] if candidates else Path.cwd().resolve()


class DocumentPane(QWidget):
    def __init__(
        self,
        source_path: Path,
        *,
        checklist: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.source_path = Path(source_path)
        self.is_checklist = bool(checklist)
        self.raw_text = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(7)

        top = QHBoxLayout()
        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Hledat v dokumentu…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._search_changed)
        self.search.returnPressed.connect(self.find_next)
        top.addWidget(QLabel("Hledání:", self))
        top.addWidget(self.search, 1)

        self.summary = QLabel("", self)
        self.summary.setObjectName("documentationSummary")
        top.addWidget(self.summary)
        root.addLayout(top)

        splitter = QSplitter(Qt.Horizontal, self)
        self.contents = QListWidget(splitter)
        self.contents.setObjectName("documentationContents")
        self.contents.setMinimumWidth(250)
        self.contents.setMaximumWidth(420)
        self.contents.itemClicked.connect(self._heading_clicked)

        self.browser = QTextBrowser(splitter)
        self.browser.setObjectName("documentationBrowser")
        self.browser.setOpenExternalLinks(True)
        self.browser.setReadOnly(True)

        splitter.addWidget(self.contents)
        splitter.addWidget(self.browser)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([300, 820])
        root.addWidget(splitter, 1)

        self.path_label = QLabel("", self)
        self.path_label.setObjectName("documentationPath")
        self.path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        root.addWidget(self.path_label)

        self.reload()

    def reload(self) -> None:
        self.contents.clear()
        self.raw_text = ""
        try:
            self.raw_text = self.source_path.read_text(encoding="utf-8")
        except OSError as exc:
            self.browser.setPlainText(
                "Dokument se nepodařilo načíst.\\n\\n"
                f"Očekávaná cesta:\\n{self.source_path}\\n\\n"
                f"Chyba: {type(exc).__name__}: {exc}"
            )
            self.summary.setText("Dokument není dostupný")
            self.path_label.setText(f"Zdroj: {self.source_path}")
            return

        self.browser.setMarkdown(self.raw_text)
        self.path_label.setText(f"Zdroj: {self.source_path}")
        self._populate_contents(self.search.text())

        if self.is_checklist:
            done = len(DONE_RE.findall(self.raw_text))
            remaining = len(OPEN_RE.findall(self.raw_text))
            total = done + remaining
            self.summary.setText(
                f"Hotovo: {done}   Zbývá/ověřit: {remaining}   Celkem: {total}"
            )
        else:
            heading_count = len(HEADING_RE.findall(self.raw_text))
            self.summary.setText(f"Kapitol a podkapitol: {heading_count}")

    def _headings(self) -> list[tuple[int, str]]:
        return [
            (len(match.group(1)), match.group(2).strip())
            for match in HEADING_RE.finditer(self.raw_text)
        ]

    def _populate_contents(self, query: str = "") -> None:
        query_folded = str(query or "").strip().casefold()
        self.contents.clear()
        for level, title in self._headings():
            if query_folded and query_folded not in title.casefold():
                continue
            item = QListWidgetItem(f"{'   ' * max(0, level - 1)}{title}")
            item.setData(Qt.UserRole, title)
            item.setToolTip(title)
            self.contents.addItem(item)

    def _heading_clicked(self, item: QListWidgetItem) -> None:
        title = str(item.data(Qt.UserRole) or "").strip()
        if not title:
            return
        cursor = self.browser.textCursor()
        cursor.movePosition(QTextCursor.Start)
        self.browser.setTextCursor(cursor)
        self.browser.find(title)
        self.browser.ensureCursorVisible()

    def _search_changed(self, text: str) -> None:
        self._populate_contents(text)
        query = str(text or "").strip()
        if not query:
            cursor = self.browser.textCursor()
            cursor.clearSelection()
            self.browser.setTextCursor(cursor)
            return
        cursor = self.browser.textCursor()
        cursor.movePosition(QTextCursor.Start)
        self.browser.setTextCursor(cursor)
        self.browser.find(query)
        self.browser.ensureCursorVisible()

    def find_next(self) -> None:
        query = self.search.text().strip()
        if not query:
            return
        if not self.browser.find(query):
            cursor = self.browser.textCursor()
            cursor.movePosition(QTextCursor.Start)
            self.browser.setTextCursor(cursor)
            self.browser.find(query)
        self.browser.ensureCursorVisible()


class DocumentationDialog(QDialog):
    SPEC_TAB = 0
    CHECKLIST_TAB = 1

    def __init__(
        self,
        parent=None,
        *,
        initial_tab: str = "spec",
        project_root: Path | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Latflix – projektová dokumentace")
        self.resize(1180, 760)
        self.setMinimumSize(860, 560)

        root_path = find_project_root(project_root)
        docs = root_path / "docs"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(7)

        intro = QLabel(
            "Aktuální specifikace a stav implementace. "
            "Obsah se načítá přímo z projektových Markdown souborů.",
            self,
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.tabs = QTabWidget(self)
        self.spec_pane = DocumentPane(
            docs / "SPEC_LATFLIX_2.md",
            checklist=False,
            parent=self.tabs,
        )
        self.checklist_pane = DocumentPane(
            docs / "IMPLEMENTATION_CHECKLIST_2_1.md",
            checklist=True,
            parent=self.tabs,
        )
        self.tabs.addTab(self.spec_pane, "Specifikace")
        self.tabs.addTab(self.checklist_pane, "Stav implementace")
        layout.addWidget(self.tabs, 1)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.reload_button = QPushButton("Znovu načíst", self)
        self.reload_button.clicked.connect(self.reload_documents)
        buttons.addWidget(self.reload_button)
        close_button = QPushButton("Zavřít", self)
        close_button.clicked.connect(self.accept)
        buttons.addWidget(close_button)
        layout.addLayout(buttons)

        self.set_initial_tab(initial_tab)

    def set_initial_tab(self, tab: str) -> None:
        self.tabs.setCurrentIndex(
            self.CHECKLIST_TAB
            if str(tab).strip().casefold() in {"checklist", "stav", "status"}
            else self.SPEC_TAB
        )

    def reload_documents(self) -> None:
        self.spec_pane.reload()
        self.checklist_pane.reload()
