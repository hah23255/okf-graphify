"""End-to-end: sandbox HERMES_HOME, real hermes loader, full provider lifecycle."""
import os
import sys
from pathlib import Path

import pytest

HERMES_AGENT = Path.home() / ".hermes" / "hermes-agent"
REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture()
def sandbox_home(tmp_path, monkeypatch):
    home = tmp_path / "hermes"
    (home / "plugins").mkdir(parents=True)
    (home / "plugins" / "memory_unified").symlink_to(REPO_ROOT)
    monkeypatch.setenv("HERMES_HOME", str(home))
    for mod in list(sys.modules):
        if mod.startswith(("hermes_constants", "plugins.memory")):
            monkeypatch.delitem(sys.modules, mod, raising=False)
    if str(HERMES_AGENT) not in sys.path:
        monkeypatch.syspath_prepend(str(HERMES_AGENT))
    return home


def test_loader_discovers_and_runs_provider(sandbox_home):
    try:
        from plugins.memory import load_memory_provider
    except ImportError:
        pytest.skip("hermes-agent not installed at ~/.hermes/hermes-agent")

    p = load_memory_provider("memory_unified")
    assert p is not None and p.name == "memory_unified"
    p.initialize("itest", hermes_home=str(sandbox_home), platform="cli",
                 agent_context="primary")
    import json
    r = json.loads(p.handle_tool_call("memory", {
        "action": "add", "topic": "facts", "content": "integration fact"}))
    assert r["success"] is True
    assert "integration fact" in (sandbox_home / "memory" / "facts.md").read_text()
    assert p.prefetch("integration") != ""
    p.shutdown()
