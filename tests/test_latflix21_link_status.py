from datetime import date

from latflix21.link_status import link_status, parse_link_date


def test_link_date_parser_accepts_legacy_formats():
    assert parse_link_date("2026-09-30") == date(2026, 9, 30)
    assert parse_link_date("30.09.2026") == date(2026, 9, 30)
    assert parse_link_date("30. 09. 2026") == date(2026, 9, 30)
    assert parse_link_date("30/09/2026") == date(2026, 9, 30)
    assert parse_link_date("30-09-2026") == date(2026, 9, 30)
    assert parse_link_date("") is None
    assert parse_link_date("nesmysl") is None


def test_link_status_matches_legacy_semaphore_rules():
    today = date(2026, 10, 1)

    recent = link_status("01.10.2026", "01.09.2026", today)
    assert recent.level == "green"
    assert not recent.control_error

    old = link_status("01.10.2026", "01.01.2026", today)
    assert old.level == "yellow"

    stale_gap = link_status("01.10.2026", "01.01.2025", today)
    assert stale_gap.level == "red"

    bad_control = link_status("01.08.2026", "01.09.2026", today)
    assert bad_control.level == "green"
    assert bad_control.control_error

    no_download = link_status("01.10.2026", "", today)
    assert no_download.level == "yellow"
