"""UnifiedMemoryProvider — Hermes MemoryProvider over the structured topic store.

Modes (auto-detected from hermes config):
  mirror  — built-in memory enabled: prompt block is a short pointer, provider
            advertises no tools, on_memory_write mirrors built-in writes.
  unified — memory.memory_enabled: false: prompt block renders full recall,
            provider exposes its own `memory` tool.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.memory_provider import MemoryProvider

try:
    from .store import TOPICS, UnifiedMemoryStore
except ImportError:
    from store import TOPICS, UnifiedMemoryStore


logger = logging.getLogger(__name__)

_MIRROR_POINTER = (
    "Additional structured memory (decisions, patterns, corrections, facts) is "
    "maintained in the unified memory store and surfaced inline when relevant."
)

_TARGET_TO_TOPIC = {"user": "preferences", "memory": "facts"}

_TOOL_SCHEMA = {
    "name": "memory",
    "description": (
        "Read and write persistent structured memory. Topics: preferences, "
        "decisions, corrections, patterns, facts. Use action=add to store a "
        "durable fact, replace/remove to maintain it, list to review a topic."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["add", "replace", "remove", "list"]},
            "topic": {"type": "string", "enum": list(TOPICS)},
            "target": {"type": "string", "enum": ["memory", "user"],
                       "description": "Legacy alias: user→preferences, memory→facts."},
            "content": {"type": "string"},
            "old_content": {"type": "string",
                            "description": "Required for replace/remove."},
        },
        "required": ["action"],
    },
}


def _resolve_topic(args: Dict[str, Any]) -> str:
    if args.get("topic"):
        return args["topic"]
    return _TARGET_TO_TOPIC.get(args.get("target", "memory"), "facts")


class UnifiedMemoryProvider(MemoryProvider):
    name = "memory_unified"

    def __init__(self, root: Optional[str] = None):
        self._root_override = Path(root) if root else None
        self._store: Optional[UnifiedMemoryStore] = None
        self._session_id = ""
        self._agent_context = "primary"

    # -- config -------------------------------------------------------------
    def _builtin_enabled(self) -> bool:
        """True when the built-in flat memory is active (mirror mode)."""
        try:
            from hermes_cli.config import load_config, cfg_get
            return bool(cfg_get(load_config(), "memory", "memory_enabled", default=True))
        except Exception:
            return True  # safe default: mirror mode never shadows the built-in

    # -- lifecycle ----------------------------------------------------------
    def is_available(self) -> bool:
        return True  # local filesystem only; initialize() creates what it needs

    def initialize(self, session_id: str, **kwargs) -> None:
        self._session_id = session_id
        self._agent_context = kwargs.get("agent_context", "primary")
        hermes_home = kwargs.get("hermes_home")
        root = self._root_override or (Path(hermes_home) / "memory" if hermes_home
                                       else Path.home() / ".hermes" / "memory")
        self._store = UnifiedMemoryStore(root)
        logger.info("memory_unified initialized (mode=%s, root=%s)",
                    "mirror" if self._builtin_enabled() else "unified", root)

    def shutdown(self) -> None:
        self._store = None

    # -- recall ---------------------------------------------------------------
    def system_prompt_block(self) -> str:
        if not self._store:
            return ""
        if self._builtin_enabled():
            return _MIRROR_POINTER
        return self._store.recall_block(budget=2000)

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        if not self._store:
            return ""
        hits = self._store.search(query, limit=5)
        if not hits:
            return ""
        lines = [f"- [{topic}] {e.text}" for topic, e in hits]
        return "Relevant structured memory:\n" + "\n".join(lines)

    def sync_turn(self, user_content: str, assistant_content: str, **kwargs) -> None:
        return None  # deliberate no-op: durable writes flow through the tool path

    def on_pre_compress(self, messages) -> str:
        return ""

    def get_config_schema(self):
        return []

    def backup_paths(self):
        return []  # store lives inside HERMES_HOME — already covered by hermes backup

    # -- tool integration ----------------------------------------------------
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        if self._builtin_enabled():
            return []  # mirror mode: built-in owns the `memory` tool name
        return [_TOOL_SCHEMA]

    def handle_tool_call(self, tool_name: str, args: Dict[str, Any], **kwargs) -> str:
        if tool_name != "memory" or not self._store:
            return json.dumps({"success": False, "error": f"unknown tool {tool_name!r}"})
        action = args.get("action")
        try:
            if action == "list":
                entries = self._store.load(_resolve_topic(args))
                return json.dumps({"success": True,
                                   "entries": [e.render() for e in entries]})
            if self._agent_context != "primary":
                return json.dumps({"success": False,
                                   "error": "writes disabled outside primary context"})
            topic = _resolve_topic(args)
            content = (args.get("content") or "").strip()
            if action in ("add", "replace"):
                findings = self._scan(content)
                if findings:
                    return json.dumps({"success": False,
                                       "error": f"threat pattern rejected: {findings[0]}"})
            if action == "add":
                e = self._store.add(topic, content,
                                    source=f"session {self._session_id}",
                                    confidence="medium")
                return json.dumps({"success": True, "entry": e.render()})
            if action == "replace":
                ok = self._store.replace(topic, args.get("old_content", ""), content)
                return json.dumps({"success": ok,
                                   "error": None if ok else "entry not found"})
            if action == "remove":
                ok = self._store.remove(topic, args.get("old_content", ""))
                return json.dumps({"success": ok,
                                   "error": None if ok else "entry not found"})
            return json.dumps({"success": False, "error": f"unknown action {action!r}"})
        except Exception as exc:  # fail open: tool errors must not kill the turn
            logger.warning("memory_unified tool error: %s", exc)
            return json.dumps({"success": False, "error": str(exc)})

    @staticmethod
    def _scan(content: str) -> list:
        try:
            from tools.threat_patterns import scan_for_threats
            return scan_for_threats(content, scope="strict")
        except Exception:
            return []  # scanner unavailable → allow (same fail-open as init)

    # -- mirror mode listener ------------------------------------------------
    def on_memory_write(self, action: str, target: str, content: str,
                        metadata: Optional[Dict[str, Any]] = None) -> None:
        """Mirror built-in flat-memory writes into the structured store."""
        if not self._store or not content.strip():
            return
        topic = _TARGET_TO_TOPIC.get(target, "facts")
        meta = metadata or {}
        source = meta.get("write_origin", "builtin")
        try:
            if action == "add":
                self._store.add(topic, content, source=source, confidence="medium")
            elif action in ("replace", "remove"):
                self._store.remove(topic, content)
        except Exception as exc:
            logger.warning("memory_unified mirror failed (%s/%s): %s",
                           action, target, exc)
