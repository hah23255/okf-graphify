# Hermes Memory Unified — Design

Date: 2026-07-21
Status: Approved (all sections confirmed by user)
Approach: **A — MemoryProvider plugin** (selected over tool-override and sidecar-sync)

## Problem

Hermes Agent has a split-brain memory system:

- **Built-in memory tool** (`tools/memory_tool.py:55-57`) reads/writes `~/.hermes/memories/` — flat, §-delimited `MEMORY.md` (2,200 chars) + `USER.md` (1,375 chars), drift-guarded, threat-scanned, with a frozen-snapshot system-prompt injection.
- **Dream skill** (`~/.hermes/skills/note-taking/dream/`, cron job `46af7939e430` at 03:00) reads/writes `~/.hermes/memory/` — structured topic files (`MEMORY.md` index + `preferences.md`, `decisions.md`, `corrections.md`, `patterns.md`, `facts.md`).

Neither system references the other. Gateway-written memory is invisible to dream consolidation; the consolidated bundle is invisible to the gateway at runtime. No upstream initiative exists to unify them; upstream policy directs new memory backends to standalone plugins (`hermes-agent` repo `AGENTS.md:763-800`).

## Decisions (locked with user)

| Question | Decision |
|---|---|
| End state | **Full unification** — one store, one format; `memories/` migrated once and retired |
| Canonical format | **Structured topic files** (the existing `~/.hermes/memory/` layout) |
| Scope | **Unification only** — no graph indexing, no NetworkX, no new runtime dependencies |
| Project home | **Standalone plugin repo** (`~/hermes-memory-unified`), symlinked into `~/.hermes/plugins/hermes-memory-unified/` |
| Approach | **MemoryProvider plugin** implementing `agent/memory_provider.py:43` |

## Architecture

A user-installed plugin activated via `memory.provider: hermes-memory-unified` in `~/.hermes/config.yaml`. Unification proceeds through two modes:

### Mirror mode (transition; default at first)

The built-in flat store stays enabled. The provider:

- mirrors every built-in memory write into the unified store via `on_memory_write(action, target, content, metadata)`;
- injects structured recall via `system_prompt_block()` and `prefetch()`.

Zero change to existing behavior while the store and recall are validated in production.

### Unified mode (end state)

`memory.memory_enabled: false` retires the built-in flat store. The provider exposes its own memory tool via `get_tool_schemas()` / `handle_tool_call()`, so all agent memory writes land directly in the unified store. One store, one format. The dream skill is untouched — it already maintains exactly this directory.

Providers run alongside the built-in (`agent_init.py:1447`); providers supplying their own tool schemas is the supported path to full replacement without a core patch or the `allow_tool_override` trust gate.

## Components

| Component | Purpose |
|---|---|
| `unified_store.py` | Pure-Python store library (no hermes imports, independently testable). Entry model (date, statement, source, confidence). Topic-file CRUD. Char budgets. Atomic temp-file writes with `fcntl` locks (semantics mirrored from `tools/memory_tool.py:253-288, 769-798`). Merge-on-read so dream's direct file edits never trip a drift guard. |
| `provider.py` | `UnifiedMemoryProvider(MemoryProvider)` — full lifecycle: `initialize`, `system_prompt_block`, `prefetch`/`queue_prefetch`, `sync_turn`, `get_tool_schemas`, `handle_tool_call`, `on_memory_write`, `on_session_end`, `on_pre_compress`, `backup_paths`. |
| `migrate.py` | One-time importer: parses §-delimited `memories/MEMORY.md` + `USER.md`, classifies entries into topic files with provenance metadata, dedupes against existing content, archives originals (never deletes). Dry-run by default. |
| `cli.py` | `hermes memory-unified status\|migrate\|verify\|mode` via `register_cli_command`. |
| `plugin.yaml` | Manifest; `kind: exclusive` (memory-provider convention; user-installed memory providers are auto-coerced, `plugins.py:1594`). |

## Data flow

- **Recall:** session start → `system_prompt_block()` renders the `MEMORY.md` index + top entries within char budgets. Each turn → `prefetch()` returns keyword-scored excerpts from topic files (stdlib scoring, no embeddings).
- **Write (mirror mode):** built-in `memory` tool writes flat files → `on_memory_write` mirrors into topic files.
- **Write (unified mode):** agent calls the provider's memory tool → store writes topic files directly → dream reads the same files at 03:00. Single write path end-to-end.
- **Migration:** one-shot CLI; dry-run, review, apply with backup.

## Error handling & safety

- **Fail open:** provider init errors log a warning and Hermes continues without a provider (mirrors `agent_init.py:1510-1514`); gateway boot is never blocked.
- **Corruption:** an unparseable topic file is quarantined to `memory/.corrupt/<timestamp>/`; the store rebuilds from remaining files and logs a warning.
- **Concurrency (dream 03:00 vs live session):** `fcntl` locking + re-read-before-write + entry-level merge; superseded versions are archived, never silently dropped.
- **Threat scanning:** all writes pass through Hermes's own `tools.threat_patterns` (in-process import, same as the built-in).
- **Overflow:** entries past char budget roll into `archive.md` — the same convention dream already uses.
- **Backups:** `backup_paths()` includes `~/.hermes/memory/` so `hermes backup` covers the store.
- **Rollback:** set `memory_enabled: true`, remove `memory.provider`; migration is additive (originals archived, not deleted).

## Testing

- **Unit (pytest):** store CRUD, budgets, locking under threaded races, merge semantics, migration idempotency (re-run = no duplicates), dry-run purity.
- **Contract:** provider passes the ABC lifecycle driven against Hermes's own interfaces (import `MemoryProvider`, exercise all hooks).
- **Integration:** sandboxed `HERMES_HOME` against the real checkout — session start injects the block; tool write lands in topic files; dream's `hermes-dream.sh` + skill workflow runs against the same store without conflict; gateway boots with the provider enabled.
- **Regression:** `hermes doctor`, web UI memory status (reads the retired `memories/` — documented behavior), fallback-model path untouched.

## Open verification points (for the implementation plan)

1. Exact behavior of `memory_enabled: false` — confirm the built-in memory tool is removed and background_review's tool whitelist picks up provider-supplied tools (otherwise the periodic memory flush loses its write path).
2. Whether `on_memory_write` fires for all built-in write shapes (add/replace/remove/batch) — mirror-mode fidelity depends on it.
3. Doctor/web-UI memory status behavior in unified mode (expected: reads retired `memories/`; document, don't patch).

## Out of scope

- Graph indexing / NetworkX / okf-graphify integration (phase 2 candidate; dependency analysis 2026-07-21: okf-graphify itself is stdlib+pyyaml only).
- OKF conformance hardening of the store format (frontmatter, `index.md`, `log.md`) — deferred; the current dream-compatible layout is canonical for now.
- Semantic/embedding recall.
