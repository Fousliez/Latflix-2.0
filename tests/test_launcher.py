from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_launcher_prefers_project_virtualenv():
    launcher = (ROOT / "start_app.sh").read_text(encoding="utf-8")
    assert '.venv/bin/python' in launcher
    assert 'exec "$PYTHON" main.py "$@"' in launcher
