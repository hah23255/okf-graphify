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
