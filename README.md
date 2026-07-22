# Hermes Memory Unified 🧠

> Unified structured memory provider plugin for [Hermes Agent](https://github.com/nousresearch/hermes-agent).
> Плъгин за обединена структурирана памет за Hermes Agent.

---

## English (EN)

### Overview
Hermes Memory Unified resolves Hermes's split-brain memory architecture by consolidating built-in flat memory (`~/.hermes/memories/`) and dream consolidation memory (`~/.hermes/memory/`) into a single, structured topic-file store.

#### The Split-Brain Problem Solved
- **Built-in flat memory**: Wrote to `~/.hermes/memories/` using flat, `§`-delimited files (`MEMORY.md` and `USER.md`).
- **Dream consolidation skill**: Read and wrote structured topic files at `~/.hermes/memory/` (`preferences.md`, `decisions.md`, `corrections.md`, `patterns.md`, `facts.md`).

Neither system referenced the other. **Hermes Memory Unified** unifies them into a single canonical store powered by standard Markdown files with `fcntl` concurrency control, atomic file swaps, corruption quarantining, and budget-based overflow archiving.

### Installation
1. **Symlink this repository into your Hermes plugins directory**:
   ```bash
   ln -s ~/hermes-memory-unified ~/.hermes/plugins/memory_unified
   ```

2. **Run the legacy flat-memory migration tool**:
   ```bash
   hermes memory_unified migrate --apply
   ```

3. **Enable unified mode in Hermes configuration**:
   ```bash
   hermes config set memory.memory_enabled false
   hermes config set memory.provider memory_unified
   ```

### Operating Modes

| Mode | Trigger | Tool Owner | Prompt Block | Memory Writes |
| :--- | :--- | :--- | :--- | :--- |
| **Mirror Mode** | `memory.memory_enabled: true` | Built-in memory tool | Short structured memory pointer | Built-in flat writes mirrored into topic files via `on_memory_write` |
| **Unified Mode** | `memory.memory_enabled: false` | Provider (`memory_unified`) | Full structured recall digest or `MEMORY.md` | Direct writes into topic files with threat scanning and context locks |

### CLI Commands
```bash
hermes memory_unified status    # View entry counts per topic, root path, and active mode
hermes memory_unified migrate   # Dry-run migration (add --apply to perform)
hermes memory_unified verify    # Verify health of topic files and index
hermes memory_unified mode      # Print current mode and transition instructions
```

### Rollback
To return to standard flat memory:
```bash
hermes config set memory.memory_enabled true
hermes config set memory.provider memory_unified  # (or remove memory.provider)
```
Migration is additive; original flat files are archived under `~/.hermes/memories/.migrated-<date>/` and never deleted.

---

## Български (BG)

### Преглед
Hermes Memory Unified решава проблема с разделението в архитектурата на паметта на Hermes (split-brain architecture), като обединява вградената плоска памет (`~/.hermes/memories/`) и консолидираната памет от умението dream (`~/.hermes/memory/`) в единно, структурирано хранилище по теми.

#### Разрешаване на проблема с разделението
- **Вградена плоска памет**: Записваше в `~/.hermes/memories/` чрез плоски файлове, разделени със символа `§` (`MEMORY.md` и `USER.md`).
- **Умение за консолидация dream**: Четеше и записваше структурирани тематични файлове в `~/.hermes/memory/` (`preferences.md`, `decisions.md`, `corrections.md`, `patterns.md`, `facts.md`).

Системите не се реферираха взаимно. **Hermes Memory Unified** ги обединява в едно канонично хранилище, базирано на стандартни Markdown файлове с `fcntl` управление на съвместния достъп, атомарна замяна на файлове, карантиниране на повредени данни и автоматично архивиране при превишаване на лимитите.

### Инсталация
1. **Създайте символна връзка към директорията с плъгини на Hermes**:
   ```bash
   ln -s ~/hermes-memory-unified ~/.hermes/plugins/memory_unified
   ```

2. **Стартирайте инструмента за миграция на наследената памет**:
   ```bash
   hermes memory_unified migrate --apply
   ```

3. **Активирайте обединения режим в конфигурацията на Hermes**:
   ```bash
   hermes config set memory.memory_enabled false
   hermes config set memory.provider memory_unified
   ```

### Режими на работа

| Режим | Активатор | Собственик на инструмента | Блок в промпта | Записи в паметта |
| :--- | :--- | :--- | :--- | :--- |
| **Mirror Mode** | `memory.memory_enabled: true` | Вграден инструмент | Кратък указател към структурираната памет | Огледален запис на вградените записи чрез `on_memory_write` |
| **Unified Mode** | `memory.memory_enabled: false` | Плъгин (`memory_unified`) | Пълен структуриран извлечен блок или `MEMORY.md` | Директен запис в тематичните файлове със проверка за сигурност |

### Команди на CLI
```bash
hermes memory_unified status    # Преглед на брой записи по теми, път до хранилището и режим
hermes memory_unified migrate   # Симулация на миграция (добавете --apply за изпълнение)
hermes memory_unified verify    # Проверка на целостта на тематичните файлове и индекса
hermes memory_unified mode      # Извеждане на текущия режим и инструкции за превключване
```

### Възстановяване (Rollback)
За връщане към стандартната плоска памет:
```bash
hermes config set memory.memory_enabled true
hermes config set memory.provider memory_unified
```
Миграцията е адитивна; оригиналните плоски файлове се архивират в `~/.hermes/memories/.migrated-<date>/` и никога не се изтриват.

---

## Testing & Verification / Тестване и верификация

Run unit and integration tests / Стартиране на тестовете:
```bash
~/.hermes/hermes-agent/venv/bin/python -m pytest -v
```

For detailed specifications, see [docs/API.md](docs/API.md).
За подробни спецификации вижте [docs/API.md](docs/API.md).
