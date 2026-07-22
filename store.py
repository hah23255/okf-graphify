"""Unified structured memory store for Hermes.

Reads/writes the topic-file layout at $HERMES_HOME/memory/:
MEMORY.md (index) + preferences/decisions/corrections/patterns/facts.md.
Pure stdlib, no hermes imports — independently testable.

Entry line format (dream-compatible):
    * **[YYYY-MM-DD]** statement *(source: X, confidence: Y)*
"""
from __future__ import annotations

import fcntl
import os
import re
import shutil
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date as _date
from pathlib import Path
from typing import Callable, Optional

TOPICS = ("preferences", "decisions", "corrections", "patterns", "facts")
TOPIC_BUDGETS = {
    "preferences": 3000,
    "decisions": 8000,
    "corrections": 4000,
    "patterns": 5000,
    "facts": 8000,
}
INDEX_NAME = "MEMORY.md"
ARCHIVE_NAME = "archive.md"

# Known failure mode: entry text ending in a metadata-shaped fragment
# `*(source: X, confidence: Y)*` is always parsed as metadata, so such
# text is not roundtrip-stable (the fragment is split off on re-parse).
ENTRY_RE = re.compile(
    r"^\* \*\*\[(?P<date>\d{4}-\d{2}-\d{2})\]\*\* (?P<text>.*?)"
    r"(?: \*\(source: (?P<source>.*?), confidence: (?P<confidence>[^)]*)\)\*)?\s*$"
)


class StoreError(Exception):
    """Raised for invalid operations (unknown topic, missing entry)."""


@dataclass
class Entry:
    date: str
    text: str
    source: str = ""
    confidence: str = ""

    def render(self) -> str:
        if self.source or self.confidence:
            return (f"* **[{self.date}]** {self.text} "
                    f"*(source: {self.source}, confidence: {self.confidence})*")
        return f"* **[{self.date}]** {self.text}"

    def key(self) -> str:
        """Normalized text used for dedupe (ignores date/metadata/case/space/punct)."""
        return re.sub(r"[\W_]+", " ", self.text.lower()).strip()


def parse_entries(text: str) -> list[Entry]:
    entries = []
    for line in text.splitlines():
        m = ENTRY_RE.match(line.strip())
        if m:
            entries.append(Entry(
                date=m.group("date"), text=m.group("text").strip(),
                source=(m.group("source") or "").strip(),
                confidence=(m.group("confidence") or "").strip()))
    return entries


def render_topic(topic: str, entries: list[Entry]) -> str:
    title = topic.capitalize()
    body = "\n".join(e.render() for e in entries)
    return f"# {title}\n\n{body}\n" if body else f"# {title}\n"


@contextmanager
def _file_lock(lock_path: Path):
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "a") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


class UnifiedMemoryStore:
    """Topic-file memory store. All writes: flock + re-read + merge + atomic replace."""

    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _topic_path(self, topic: str) -> Path:
        if topic not in TOPICS:
            raise StoreError(f"unknown topic {topic!r}; valid: {', '.join(TOPICS)}")
        return self.root / f"{topic}.md"

    def _read_entries(self, path: Path) -> list[Entry]:
        if not path.exists():
            return []
        try:
            return parse_entries(path.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            quarantine = self.root / ".corrupt"
            quarantine.mkdir(exist_ok=True)
            shutil.move(str(path), quarantine / f"{path.name}.{_date.today()}")
            return []

    def load(self, topic: str) -> list[Entry]:
        return self._read_entries(self._topic_path(topic))

    def _update(self, topic: str, fn: Callable[[list[Entry]], tuple[list[Entry], object]],
                entry_date: Optional[str] = None):
        """Lock, re-read, apply fn(entries)->(new_entries, result), write, budget-check."""
        path = self._topic_path(topic)
        with _file_lock(path.with_suffix(path.suffix + ".lock")):
            entries = self._read_entries(path)
            new_entries, result = fn(entries)
            kept, archived = self._enforce_budget(topic, new_entries)
            _atomic_write(path, render_topic(topic, kept))
            if archived:
                self._append_archive(topic, archived)
        return result

    def add(self, topic: str, text: str, source: str = "",
            confidence: str = "", entry_date: Optional[str] = None) -> Entry:
        entry = Entry(date=entry_date or str(_date.today()), text=text,
                      source=source, confidence=confidence)

        def fn(entries):
            if any(e.key() == entry.key() for e in entries):
                return entries, next(e for e in entries if e.key() == entry.key())
            return entries + [entry], entry

        return self._update(topic, fn)

    # --- budget / archive (Task 5 fills these in) ---
    def _enforce_budget(self, topic, entries):
        return entries, []

    def _append_archive(self, topic, archived):
        pass
