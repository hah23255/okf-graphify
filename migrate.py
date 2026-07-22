"""One-time migration: flat §-delimited memories/ → structured memory/ store.

Dry-run by default. Idempotent (store-level key dedupe). Originals are moved
to memories/.migrated-<date>/ — never deleted.
"""
from __future__ import annotations

import logging
import shutil
from datetime import date as _date
from pathlib import Path
from typing import Optional

try:
    from .store import Entry, UnifiedMemoryStore
except ImportError:
    from store import Entry, UnifiedMemoryStore


logger = logging.getLogger(__name__)

_RULES = [
    ("corrections", ("wrong", "mistake", "instead", "fix", "error")),
    ("decisions", ("decided", "decision", "chose", "chosen", "we use", "switched")),
    ("patterns", ("always", "usually", "pattern", "tends to", "every time")),
    ("preferences", ("prefer", "likes", "dislikes", "favorite", "wants")),
]
_DEFAULT_BY_TARGET = {"user": "preferences", "memory": "facts"}


def parse_flat(path: Path) -> list[str]:
    """Split a built-in flat memory file on the § delimiter."""
    if not path.exists():
        return []
    return [chunk.strip() for chunk in
            path.read_text(encoding="utf-8").split("\n§\n") if chunk.strip()]


def classify(text: str, target: str) -> str:
    low = text.lower()
    for topic, keywords in _RULES:
        if any(k in low for k in keywords):
            return topic
    return _DEFAULT_BY_TARGET.get(target, "facts")


def run_migration(hermes_home: Path, dry_run: bool = True,
                  migration_date: Optional[str] = None) -> dict:
    hermes_home = Path(hermes_home)
    legacy = hermes_home / "memories"
    store = UnifiedMemoryStore(hermes_home / "memory")
    stamp = migration_date or str(_date.today())
    report = {"imported": 0, "skipped_duplicates": 0, "by_topic": {}, "dry_run": dry_run}

    candidates = []  # (topic, text, src_file)
    for filename, target in (("MEMORY.md", "memory"), ("USER.md", "user")):
        for chunk in parse_flat(legacy / filename):
            candidates.append((classify(chunk, target), chunk, filename))

    existing_keys = set()
    for topic in {t for t, _, _ in candidates}:
        existing_keys |= {e.key() for e in store.load(topic)}

    for topic, text, filename in candidates:
        key = Entry(date=stamp, text=text).key()
        if key in existing_keys:
            report["skipped_duplicates"] += 1
            continue
        report["imported"] += 1
        report["by_topic"][topic] = report["by_topic"].get(topic, 0) + 1
        existing_keys.add(key)
        if not dry_run:
            store.add(topic, text, source=f"migration {stamp} ({filename})",
                      confidence="medium", entry_date=stamp)

    if not dry_run and legacy.exists():
        archive_dir = legacy / f".migrated-{stamp}"
        archive_dir.mkdir(exist_ok=True)
        for name in ("MEMORY.md", "USER.md"):
            src = legacy / name
            if src.exists():
                shutil.move(str(src), archive_dir / name)
    return report
