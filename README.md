# Latflix 2.0

Čistý přepis Latflixu se zaměřením na rychlost, jednoduché vlastnictví UI logiky a kompatibilitu se stávajícími daty.

## Cíl první etapy

První prototyp už používá skutečnou model/view architekturu:

- Python + PySide6
- `QTableView` místo `QTableWidget`
- `QAbstractTableModel` jako jediný vlastník dat hlavní tabulky
- `QSortFilterProxyModel` pro hledání a řazení
- SQLite za jednou `Repository` vrstvou
- žádné runtime monkeypatchování tříd ani skryté installery
- měření času načtení sekce přímo ve stavovém řádku

## Spuštění

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
./start_app.sh
```

Při prvním spuštění vznikne samostatná testovací databáze:

```text
~/.local/share/latflix2/database/latflix2.db
```

Latflix 2.0 tedy automaticky nesahá na databázi původního Latflixu.

## Import kopie databáze Latflixu 1

Pro testování na reálných datech použij bezpečný kopírovací nástroj:

```bash
.venv/bin/python tools/import_latflix1.py /cesta/k/puvodni/girls.db
```

Import používá SQLite backup API a vytvoří vlastní kopii pro Latflix 2.0. Zdrojová databáze se otevírá pouze pro čtení.

Pokud už cílová databáze Latflixu 2.0 existuje, import ji bez `--force` nepřepíše.

## Stav

Toto je zatím základ nové aplikace, ne náhrada Latflixu 1. Funkce budeme převádět po blocích a po každém bloku měřit.
