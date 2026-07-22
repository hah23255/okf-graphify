# tests/test_migrate.py
from pathlib import Path
from migrate import classify, parse_flat, run_migration


def test_parse_flat_splits_on_delimiter(tmp_path):
    f = tmp_path / "MEMORY.md"
    f.write_text("entry one\n§\nentry two\n§\nentry three\n")
    assert parse_flat(f) == ["entry one", "entry two", "entry three"]


def test_classify_keyword_rules():
    assert classify("User prefers tea over coffee", "user") == "preferences"
    assert classify("We decided to use sqlite", "memory") == "decisions"
    assert classify("I was wrong about the API, use v2 instead", "memory") == "corrections"
    assert classify("He always reviews before merging", "memory") == "patterns"
    assert classify("The sky is blue", "memory") == "facts"
    assert classify("The sky is blue", "user") == "preferences"  # default by target


def make_legacy(home: Path):
    mem = home / "memories"
    mem.mkdir(parents=True)
    (mem / "MEMORY.md").write_text("sky is blue\n§\nWe decided to use sqlite\n")
    (mem / "USER.md").write_text("User prefers tea\n")


def test_dry_run_reports_without_writing(tmp_path):
    make_legacy(tmp_path)
    report = run_migration(tmp_path, dry_run=True)
    assert report["imported"] == 3
    assert not (tmp_path / "memory" / "facts.md").exists()
    assert (tmp_path / "memories" / "MEMORY.md").exists()  # untouched


def test_apply_imports_and_archives_originals(tmp_path):
    make_legacy(tmp_path)
    report = run_migration(tmp_path, dry_run=False)
    assert report["imported"] == 3
    assert "sky is blue" in (tmp_path / "memory" / "facts.md").read_text()
    assert "sqlite" in (tmp_path / "memory" / "decisions.md").read_text()
    assert "prefers tea" in (tmp_path / "memory" / "preferences.md").read_text()
    archived = list((tmp_path / "memories").glob(".migrated-*/MEMORY.md"))
    assert archived, "originals must be archived, not deleted"
    assert not (tmp_path / "memories" / "MEMORY.md").exists()


def test_rerun_is_idempotent(tmp_path):
    make_legacy(tmp_path)
    run_migration(tmp_path, dry_run=False)
    # restore a legacy file and re-run: dedupe must prevent duplicates
    (tmp_path / "memories").mkdir(exist_ok=True)
    (tmp_path / "memories" / "MEMORY.md").write_text("sky is blue\n")
    report = run_migration(tmp_path, dry_run=False)
    assert report["imported"] == 0 and report["skipped_duplicates"] == 1
    from store import UnifiedMemoryStore
    assert len(UnifiedMemoryStore(tmp_path / "memory").load("facts")) == 1
