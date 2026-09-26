from pathlib import Path

from latflix2.database import Repository


def test_repository_creates_clean_tables_and_catalogs(tmp_path: Path):
    repo = Repository(tmp_path / "latflix2.db")
    assert repo.catalog_names("types")
    assert repo.catalog_names("nationalities")
    assert repo.catalog_names("tags")
    assert repo.list_girls() == ()


def test_girl_add_edit_lock_and_favorite_view(tmp_path: Path):
    repo = Repository(tmp_path / "latflix2.db")
    girl_id = repo.add_girls(1)[0]
    repo.update_field(girl_id, "name", "Test Girl")
    repo.update_field(girl_id, "age_source", "1992")
    repo.set_locked(girl_id, True)
    repo.set_favorite(girl_id, True)

    girl = repo.girl(girl_id)
    assert girl is not None
    assert girl.name == "Test Girl"
    assert girl.age_source == "1992"
    assert girl.locked is True
    assert girl.favorite is True
    assert [row.id for row in repo.list_girls(True)] == [girl_id]


def test_locked_rows_survive_delete(tmp_path: Path):
    repo = Repository(tmp_path / "latflix2.db")
    unlocked, locked = repo.add_girls(2)
    repo.update_field(unlocked, "name", "Unlocked")
    repo.update_field(locked, "name", "Locked")
    repo.set_locked(locked, True)

    assert repo.delete_unlocked([unlocked, locked]) == 1
    assert repo.girl(unlocked) is None
    assert repo.girl(locked) is not None


def test_blank_new_rows_are_cleaned_only_while_new(tmp_path: Path):
    repo = Repository(tmp_path / "latflix2.db")
    blank = repo.add_girls(1)[0]
    assert repo.cleanup_blank_new_rows() == 1
    assert repo.girl(blank) is None

    kept = repo.add_girls(1)[0]
    repo.update_field(kept, "name", "A")
    repo.update_field(kept, "name", "")
    repo.cleanup_blank_new_rows()
    assert repo.girl(kept) is not None


def test_links_and_tracking(tmp_path: Path):
    repo = Repository(tmp_path / "latflix2.db")
    girl_id = repo.add_girls(1)[0]
    repo.update_field(girl_id, "name", "Link Girl")
    repo.add_link(girl_id, "Instagram", "https://instagram.com/example")
    repo.add_link(girl_id, "Instagram", "https://instagram.com/example2")

    girl = repo.girl(girl_id)
    assert girl is not None
    assert girl.tracking == 2
    assert len(repo.links(girl_id)) == 2
