# Architektura Latflixu 2.0

## Pevná pravidla

1. UI pracuje přes Qt model/view. Hlavní datové tabulky nesmí být postavené na `QTableWidget`.
2. SQLite vlastní vrstva `Repository`. Widgety nesmí zapisovat SQL přímo.
3. Jedna interakce má jednoho vlastníka. Žádné paralelní handlery pro tentýž klik, signál nebo zápis.
4. Žádné class-level monkeypatchování za běhu, přepisování přes `sys.modules` ani installery spouštěné vedlejším efektem importu.
5. Import modulu nesmí měnit databázi ani instalovat runtime logiku.
6. Startup nesmí automaticky migrovat uživatelský obsah. Technické schema změny budou verzované a testované.
7. Každý výkonově důležitý přechod se měří. Optimalizace bez měření je jen dražší forma pocitu.
8. Latflix 1 zůstává během vývoje referenční aplikace. Latflix 2 pracuje nad vlastní kopií dat.

## Vrstvy

```text
UI (QMainWindow, QTableView, dialogy)
            ↓
Qt modely / proxy modely
            ↓
aplikační služby
            ↓
Repository
            ↓
SQLite
```

## Směr migrace funkcí

1. rychlá kostra + tabulka + přepínání sekcí
2. bezpečný import kopie reálné databáze
3. Girls / Oblíbené
4. Videa / SUPER
5. filtry, řazení a vyhledávání
6. editace, zámky, Stav, Kvalita, Tagy
7. Odkazy
8. detail a média
9. Přehled
10. zálohy, export, nastavení
11. vizuální doladění proti Latflixu 1
