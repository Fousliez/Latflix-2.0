from pathlib import Path

from latflix21.db import Repository


def repo(tmp_path: Path) -> Repository:
    return Repository(tmp_path / "latflix21.db")


def make_valid_video(r: Repository, girl_ids, studio_id=None, title="Video"):
    video_id = r.add_video()
    r.update_video(video_id, "title", title)
    r.update_video(video_id, "release_date", "2026")
    r.update_video(video_id, "state", "MÁM")
    if studio_id is not None:
        r.set_video_studio(video_id, studio_id)
    r.set_video_participants(video_id, girl_ids)
    return video_id


def test_alias_autocomplete_returns_only_matching_name_or_alias(tmp_path):
    r = repo(tmp_path)
    girl_id = r.add_girl("Sona")
    r.set_aliases(girl_id, ["Tereza", "SonaX"])

    sona = [name for name, _, _ in r.girl_suggestions("sona")]
    tereza = [name for name, _, _ in r.girl_suggestions("tereza")]

    assert "Sona" in sona
    assert "SonaX" in sona
    assert "Tereza" not in sona
    assert tereza == ["Tereza"]
    assert r.find_girl_exact("Tereza")[0] == girl_id


def test_occurrences_count_only_full_video_records(tmp_path):
    r = repo(tmp_path)
    girl_id = r.add_girl("Anna")
    studio_id = r.add_studio("Studio A")

    incomplete = r.add_video()
    r.update_video(incomplete, "title", "Only title")
    r.set_video_participants(incomplete, [girl_id])

    assert r.girl(girl_id).occurrences == 0
    assert next(s for s in r.studios() if s.id == studio_id).occurrences == 0

    valid = make_valid_video(r, [girl_id], studio_id)
    assert valid
    assert r.girl(girl_id).occurrences == 1
    assert next(s for s in r.studios() if s.id == studio_id).occurrences == 1


def test_participants_are_rendered_by_current_occurrence_count(tmp_path):
    r = repo(tmp_path)
    common = r.add_girl("Common")
    rare = r.add_girl("Rare")
    studio = r.add_studio("Studio")

    make_valid_video(r, [common], studio, "Existing 1")
    make_valid_video(r, [common], studio, "Existing 2")
    target = make_valid_video(r, [rare, common], studio, "Target")

    video = next(v for v in r.videos() if v.id == target)
    assert [p[1] for p in video.participants[:2]] == ["Common", "Rare"]


def test_new_girl_and_studio_are_defaulted_to_top(tmp_path):
    r = repo(tmp_path)
    r.add_girl("Older")
    newest_girl = r.add_girl("Newest")
    assert r.girls()[0].id == newest_girl

    r.add_studio("Older Studio")
    newest_studio = r.add_studio("Newest Studio")
    assert r.studios()[0].id == newest_studio


def test_super_is_subset_not_duplicate_occurrence(tmp_path):
    r = repo(tmp_path)
    girl = r.add_girl("A")
    studio = r.add_studio("S")
    video = make_valid_video(r, [girl], studio)
    r.set_video_super([video], True)

    assert len(r.videos(False)) == 1
    assert len(r.videos(True)) == 1
    assert r.girl(girl).occurrences == 1
