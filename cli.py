"""CLI for the memory_unified provider: hermes memory_unified <cmd>.

Hermes calls register_cli(parser) with the already-created top-level parser
(hermes_cli/main.py:13754-13763) and dispatches to memory_unified_command.
"""
from __future__ import annotations

import json
from pathlib import Path

try:
    from .migrate import run_migration
    from .store import TOPICS, UnifiedMemoryStore
except ImportError:
    from migrate import run_migration
    from store import TOPICS, UnifiedMemoryStore


def register_cli(parser):
    sub = parser.add_subparsers(dest="memory_unified_subcommand")
    sub.add_parser("status", help="Store health: entry counts per topic, mode")
    mig = sub.add_parser("migrate", help="Import legacy memories/ (dry-run by default)")
    mig.add_argument("--apply", action="store_true", help="Actually perform the migration")
    sub.add_parser("verify", help="Parse-check all topic files and the index")
    sub.add_parser("mode", help="Print current mode and how to switch")


def _home() -> Path:
    try:
        from hermes_constants import get_hermes_home
        return Path(get_hermes_home())
    except ImportError:
        return Path.home() / ".hermes"


def _current_mode() -> str:
    try:
        from hermes_cli.config import load_config, cfg_get
        enabled = bool(cfg_get(load_config(), "memory", "memory_enabled", default=True))
        return "mirror" if enabled else "unified"
    except Exception:
        return "unknown"


def memory_unified_command(args):
    home = _home()
    cmd = getattr(args, "memory_unified_subcommand", None) or "status"
    if cmd == "status":
        store = UnifiedMemoryStore(home / "memory")
        counts = {t: len(store.load(t)) for t in TOPICS}
        print(json.dumps({"mode": _current_mode(), "root": str(store.root),
                          "entries": counts}, indent=2))
    elif cmd == "migrate":
        report = run_migration(home, dry_run=not getattr(args, "apply", False))
        print(json.dumps(report, indent=2))
        if report["dry_run"]:
            print("Dry run only — re-run with --apply to perform the migration.")
    elif cmd == "verify":
        store = UnifiedMemoryStore(home / "memory")
        ok = True
        for t in TOPICS:
            n = len(store.load(t))
            print(f"{t}: {n} entries OK")
        index = home / "memory" / "MEMORY.md"
        print(f"index: {'present' if index.exists() else 'MISSING'}")
        raise SystemExit(0 if ok else 1)
    elif cmd == "mode":
        mode = _current_mode()
        print(f"current mode: {mode}")
        if mode == "mirror":
            print("To switch to unified mode after a successful migration:")
            print("  hermes config set memory.memory_enabled false")
            print("  hermes config set memory.provider memory_unified")
        elif mode == "unified":
            print("To roll back to mirror mode:")
            print("  hermes config set memory.memory_enabled true")
            print("  hermes config set memory.provider memory_unified")
