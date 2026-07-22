# Hermes Memory Unified — API & Architecture Documentation / Документация на API и архитектурата

---

## English (EN)

### 1. Entry Format & Storage Specification

Active memory entries are stored across topic files inside `$HERMES_HOME/memory/`:
- `preferences.md` (budget: 3,000 chars)
- `decisions.md` (budget: 8,000 chars)
- `corrections.md` (budget: 4,000 chars)
- `patterns.md` (budget: 5,000 chars)
- `facts.md` (budget: 8,000 chars)

#### Line Grammar
```markdown
* **[YYYY-MM-DD]** Statement text *(source: X, confidence: Y)*
```
If metadata is omitted:
```markdown
* **[YYYY-MM-DD]** Statement text
```

#### Overflow & Archiving
When an active topic file exceeds its allocated budget, the oldest entries (by date, FIFO) are archived automatically to `archive.md` under section headers:
```markdown
## From <topic> (<date>)
```

---

### 2. Store API (`UnifiedMemoryStore`)

Located in `store.py`. Pure Python standard library implementation with zero external dependencies.

```python
class UnifiedMemoryStore:
    def __init__(self, root: str | Path): ...
    def load(self, topic: str) -> list[Entry]: ...
    def add(self, topic: str, text: str, source: str = "", confidence: str = "", entry_date: str | None = None) -> Entry: ...
    def replace(self, topic: str, old_text: str, new_text: str) -> bool: ...
    def remove(self, topic: str, text: str) -> bool: ...
    def search(self, query: str, limit: int = 8) -> list[tuple[str, Entry]]: ...
    def recall_block(self, budget: int = 2000) -> str: ...
```

#### Storage Guarantees
- **Concurrency**: POSIX `fcntl.flock` exclusive locking on `.lock` sidecar files.
- **Atomicity**: Atomic file replacement via `tempfile.mkstemp` and `os.replace` within the same directory.
- **Quarantine**: Malformed or unparseable topic files are isolated to `.corrupt/<name>.<timestamp>` and logged.

---

### 3. Provider Specification (`UnifiedMemoryProvider`)

Located in `provider.py`. Implements `agent.memory_provider.MemoryProvider`.

#### Target Mapping Alias
- `user` $\rightarrow$ `preferences`
- `memory` $\rightarrow$ `facts`

#### Tool Result Schema
`handle_tool_call()` returns JSON strings:
- Success: `{"success": true, "entry": "..."}` or `{"success": true, "entries": [...]}`
- Failure: `{"success": false, "error": "<reason>"}`

---

### 4. Migration Specification (`migrate.py`)

Parses legacy `~/.hermes/memories/` (`MEMORY.md` and `USER.md` split on `\n§\n`). Classifies entries into topics via keyword heuristics:
- `corrections`: wrong, mistake, instead, fix, error
- `decisions`: decided, decision, chose, chosen, we use, switched
- `patterns`: always, usually, pattern, tends to, every time
- `preferences`: prefer, likes, dislikes, favorite, wants
- Default fallback: `user` $\rightarrow$ `preferences`, `memory` $\rightarrow$ `facts`

Original files are moved to `memories/.migrated-<date>/` to preserve legacy state.

---

## Български (BG)

### 1. Формат на записите и спецификация на съхранението

Активните записи на паметта се съхраняват в тематични файлове в `$HERMES_HOME/memory/`:
- `preferences.md` (лимит: 3,000 символа)
- `decisions.md` (лимит: 8,000 символа)
- `corrections.md` (лимит: 4,000 символа)
- `patterns.md` (лимит: 5,000 символа)
- `facts.md` (лимит: 8,000 символа)

#### Граматика на реда
```markdown
* **[YYYY-MM-DD]** Текст на твърдението *(source: X, confidence: Y)*
```

#### Архивиране при препълване
Когато активният файл надвиши лимита си, най-старите записи се преместват автоматично в `archive.md`.

---

### 2. API на хранилището (`UnifiedMemoryStore`)

Реализиран в `store.py`. Чист Python стандартна библиотека без външни зависимости.

#### Гаранции за съхранение
- **Конкурентност**: POSIX `fcntl.flock` ексклузивно заключване на `.lock` файлове.
- **Атомарност**: Атомарна замяна на файлове с `tempfile.mkstemp` и `os.replace`.
- **Карантина**: Повредени файлове се изолират в `.corrupt/<име>.<времево_клеймо>`.

---

### 3. Спецификация на доставчика (`UnifiedMemoryProvider`)

Реализиран в `provider.py`. Внедрява `agent.memory_provider.MemoryProvider`.
Поддържа пълна съвместимост с режимите Mirror и Unified.
