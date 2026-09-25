from __future__ import annotations

import argparse
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from latflix2.config import database_path


def copy_database(source: Path, target: Path, *, force: bool = False) -> Path:
    source = source.expanduser().resolve()
    target = target.expanduser().resolve()

    if not source.is_file():
        raise FileNotFoundError(f"Zdrojová databáze neexistuje: {source}")
    if source == target:
        raise ValueError("Zdroj a cíl nesmí být stejný soubor.")

    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if not force:
            raise FileExistsError(
                f"Cílová databáze už existuje: {target}\n"
                "Použij --force jen pokud ji opravdu chceš nahradit."
            )
        backup = target.with_name(
            f"{target.stem}-before-import-{datetime.now():%Y%m%d-%H%M%S}{target.suffix}"
        )
        os.replace(target, backup)
        print(f"Předchozí databáze Latflixu 2.0 byla odložena: {backup}")

    temporary = target.with_suffix(target.suffix + ".importing")
    if temporary.exists():
        temporary.unlink()

    try:
        source_uri = f"file:{source.as_posix()}?mode=ro"
        with sqlite3.connect(source_uri, uri=True) as source_db:
            with sqlite3.connect(temporary) as target_db:
                source_db.backup(target_db)
                result = target_db.execute("PRAGMA integrity_check").fetchone()
                if result is None or str(result[0]).casefold() != "ok":
                    raise RuntimeError(f"Kontrola kopie databáze selhala: {result}")
        os.replace(temporary, target)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise

    return target


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bezpečně zkopíruje databázi Latflixu 1 pro Latflix 2.0."
    )
    parser.add_argument("source", type=Path, help="Cesta k původní girls.db")
    parser.add_argument(
        "--target",
        type=Path,
        default=database_path(),
        help="Cílová DB Latflixu 2.0",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Nahradit existující cílovou DB po vytvoření její bezpečnostní kopie",
    )
    args = parser.parse_args()

    try:
        target = copy_database(args.source, args.target, force=args.force)
    except Exception as exc:
        print(f"IMPORT SELHAL: {exc}")
        return 1

    print(f"Import hotový: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
