"""Shared fixtures: make the plugin dir and hermes-agent importable."""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HERMES_AGENT = Path.home() / ".hermes" / "hermes-agent"

for p in (str(REPO_ROOT), str(HERMES_AGENT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from store import UnifiedMemoryStore  # noqa: E402


@pytest.fixture()
def store(tmp_path):
    return UnifiedMemoryStore(tmp_path / "memory")
