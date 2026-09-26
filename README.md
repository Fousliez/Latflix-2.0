# Latflix 2.1

Čistý desktopový přepis Latflixu podle `docs/SPEC_LATFLIX_2.md` a referenčních screenshotů.

## Základ

- Python + PySide6
- SQLite přes jednu `Repository` vrstvu
- `QTableView` + `QAbstractTableModel`
- sdílená filtrační/řadicí proxy
- společná tabulková logika pro sekce
- Girls / Oblíbené a Videa / Super jsou párové pohledy nad stejnými záznamy
- samostatné tabulky `lf21_*`, takže starší prototypová data zůstávají nedotčená
- při prvním spuštění se použitelné údaje z `lf2_*` jednorázově převedou do `lf21_*`

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

## Zdroj pravdy

```text
docs/SPEC_LATFLIX_2.md
```

Psaná specifikace má přednost před starými screenshoty. Screenshoty slouží jako vizuální a funkční reference tam, kde specifikace není přesnější.
