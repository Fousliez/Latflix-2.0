from pathlib import Path

from latflix2.database import Repository


def test_repository_seeds_and_loads(tmp_path: Path):
    repo = Repository(tmp_path / "latflix2.db")
    assert "Girls" in repo.categories()
    dataset = repo.load("Girls")
    assert dataset.category == "Girls"
    assert dataset.columns
    assert dataset.rows == ()


def test_repository_updates_single_cell(tmp_path: Path):
    repo = Repository(tmp_path / "latflix2.db")
    record_id = repo.add_record("Girls")
    dataset = repo.load("Girls")
    first_column = dataset.columns[0]
    repo.update_cell(record_id, first_column.id, "Test")
    dataset = repo.load("Girls")
    assert dataset.rows[0].values[0] == "Test"


def test_favorites_are_a_view_over_girls(tmp_path: Path):
    repo = Repository(tmp_path / "latflix2.db")
    record_id = repo.add_record("Girls")
    repo.update_named_cell(record_id, "Girls", "Jméno", "Test Girl")
    repo.set_favorite(record_id, True)

    favorites = repo.load("Oblíbené")
    assert favorites.category == "Oblíbené"
    assert [row.id for row in favorites.rows] == [record_id]
    assert record_id in favorites.favorite_ids
