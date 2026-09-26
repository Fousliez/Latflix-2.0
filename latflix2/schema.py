from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ColumnKind = Literal["text", "choice", "age", "tags", "computed", "note"]


@dataclass(frozen=True)
class ColumnSpec:
    key: str
    title: str
    kind: ColumnKind = "text"
    choices: tuple[str, ...] = ()
    source: str | None = None
    read_only: bool = False
    primary_text: bool = False
    default_width: int = 120


@dataclass(frozen=True)
class FilterSpec:
    key: str
    title: str
    choices: tuple[str, ...] = ()
    source: str | None = None
    special: str | None = None


FACE_VALUES = ("Ano", "Asi ano", "Asi ne", "Ne", "Zjistit")
YES_VALUES = ("Ano", "Ne", "Asi ne", "Asi ano", "Zjistit")
GIRL_STATUS_VALUES = ("Aktivní", "Neaktivní", "Smazaná")

GIRL_COLUMNS = (
    ColumnSpec("name", "Jméno", primary_text=True, default_width=190),
    ColumnSpec("face", "Obličej", kind="choice", choices=FACE_VALUES, default_width=105),
    ColumnSpec("sex", "Sex", kind="choice", choices=YES_VALUES, default_width=90),
    ColumnSpec("type_name", "Typ", kind="choice", source="types", default_width=120),
    ColumnSpec("nudity", "Nahota", kind="choice", choices=YES_VALUES, default_width=100),
    ColumnSpec("age_source", "Věk", kind="age", default_width=70),
    ColumnSpec("nationality", "Národnost", kind="choice", source="nationalities", default_width=130),
    ColumnSpec("tags", "Tagy", kind="tags", read_only=True, default_width=180),
    ColumnSpec("tracking", "Sledování", kind="computed", read_only=True, default_width=90),
    ColumnSpec("last_check", "Posl. kontrola", default_width=125),
    ColumnSpec("occurrences", "Počet výskytů", kind="computed", read_only=True, default_width=115),
    ColumnSpec("note", "Pozn.", kind="note", read_only=True, default_width=210),
    ColumnSpec("status", "Stav", kind="choice", choices=GIRL_STATUS_VALUES, default_width=110),
)

GIRL_FILTERS = (
    FilterSpec("nationality", "Národnost", source="nationalities", special="nationality_ranked"),
    FilterSpec("type_name", "Typ", source="types"),
    FilterSpec("status", "Stav", choices=GIRL_STATUS_VALUES),
    FilterSpec("sex", "Sex", choices=YES_VALUES),
    FilterSpec("nudity", "Nahota", choices=YES_VALUES),
    FilterSpec("face", "Obličej", choices=FACE_VALUES),
    FilterSpec("profile", "Profilovka", choices=("Ano", "Ne"), special="profile"),
)

GIRL_CATEGORIES = {"Girls", "Oblíbené"}
MAIN_SECTIONS = ("Přehled", "Girls", "Oblíbené", "Odkazy", "Videa", "Super", "Studia")
HELPER_SECTIONS = ("Stavy", "Kvality", "Tagy", "Typy", "Národnosti")


def display_age(raw: str, current_year: int) -> str:
    text = str(raw or "").strip()
    if not text:
        return ""
    try:
        number = int(text)
    except ValueError:
        return text
    if 1 <= number <= 100:
        return str(number)
    if 1800 <= number <= current_year:
        return str(current_year - number)
    return text
