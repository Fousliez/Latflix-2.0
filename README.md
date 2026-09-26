# Latflix 2.0

Čistý přepis Latflixu podle nové specifikace.

## Stav

Aktuální větev je první skutečná model/view verze, ne rychlý QTableWidget prototyp.

Základ:

- Python + PySide6
- SQLite přes jedinou `Repository` vrstvu
- `QTableView` + vlastní `QAbstractTableModel`
- jedna filtrační/řadicí proxy
- jeden společný tabulkový základ pro další sekce
- žádné runtime monkeypatchování
- žádné kopírování Girls do Oblíbených; Oblíbené jsou pohled nad Girls

První reálná etapa je zaměřená na **Girls / Oblíbené** a společnou tabulkovou logiku.
Další sekce budou přidávány konfigurací stejného základu.

## Spuštění

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
./start_app.sh
```

Databáze:

```text
~/.local/share/latflix2/database/latflix2.db
```

Nová implementace používá vlastní tabulky s prefixem `lf2_`, takže nepřepisuje staré experimentální tabulky v existující testovací databázi.

## Specifikace

Zdroj pravdy je:

```text
docs/SPEC_LATFLIX_2.md
```

Psaná specifikace má přednost před starými screenshoty a prototypovým chováním.
