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


def test_top_detail_link_pager_limits_visible_chips(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    repository = Repository(tmp_path / "latflix2.db")
    window = MainWindow(repository)
    try:
        window.detail.links_container.resize(230, 80)
        window.detail._set_link_chips(
            [
                {
                    "site": f"Long source name {index}",
                    "url": f"https://example.com/{index}",
                    "type_label": "Zdroj",
                }
                for index in range(14)
            ]
        )
        window.detail._rebuild_link_pages(reset=True)

        assert len(window.detail._link_pages) >= 2
        assert not window.detail.link_pager.isHidden()
        assert window.detail.link_page_label.text().startswith("1/")
        visible_first = sum(
            not button.isHidden()
            for button in window.detail._link_buttons
        )

        window.detail._change_link_page(1)
        assert window.detail.link_page_label.text().startswith("2/")
        visible_second = sum(
            not button.isHidden()
            for button in window.detail._link_buttons
        )
        assert visible_first > 0
        assert visible_second > 0
    finally:
        window.close()
        app.processEvents()
