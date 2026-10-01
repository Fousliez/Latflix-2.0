from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime


DATE_FORMATS = (
    "%Y-%m-%d",
    "%d.%m.%Y",
    "%d. %m. %Y",
    "%d.%m.%y",
    "%d. %m. %y",
    "%d/%m/%Y",
    "%d-%m-%Y",
)


@dataclass(frozen=True)
class LinkStatus:
    level: str
    tooltip: str
    control_error: bool = False


def parse_link_date(value: str | None) -> date | None:
    text = " ".join(str(value or "").strip().split())
    if not text:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + int(months)
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, monthrange(year, month)[1])
    return date(year, month, day)


def link_status(
    checked_value: str | None,
    downloaded_value: str | None,
    today: date | None = None,
) -> LinkStatus:
    checked = parse_link_date(checked_value)
    downloaded = parse_link_date(downloaded_value)
    reference = today or date.today()

    control_error = bool(downloaded and (checked is None or downloaded > checked))
    if control_error:
        return LinkStatus(
            "green",
            "Stažení je novější než kontrola. Nový obsah existuje, ale datum kontroly je potřeba opravit.",
            True,
        )

    if checked and downloaded:
        earlier, later = sorted((checked, downloaded))
        if later > add_months(earlier, 12):
            return LinkStatus(
                "red",
                "Rozdíl mezi poslední kontrolou a stažením je delší než 1 rok.",
            )

    if downloaded and reference < add_months(downloaded, 3):
        return LinkStatus(
            "green",
            f"Staženo {downloaded.strftime('%d.%m.%Y')}, tedy před méně než 3 měsíci.",
        )

    if downloaded:
        return LinkStatus(
            "yellow",
            f"Staženo {downloaded.strftime('%d.%m.%Y')}, tedy před více než 3 měsíci.",
        )

    return LinkStatus(
        "yellow",
        "Datum stažení není vyplněné nebo mu aplikace nerozumí.",
    )


def link_date_sort_key(value: str | None):
    parsed = parse_link_date(value)
    if parsed is None:
        return (1, date.max)
    return (0, parsed)
