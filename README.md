# OKF Graphify — Production Deployment Pack

**Graphify ↔ Google Open Knowledge Format (OKF v0.1) — Bi-directional Integration Toolkit**

[![OKF v0.1](https://img.shields.io/badge/OKF-v0.1-blue)](https://google.github.io/okf/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-green)](https://python.org)
[![License MIT](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-5%2F5-brightgreen)](tests/)

---

## 🇬🇧 English

A production-ready Python toolkit that converts Graphify knowledge graphs (NetworkX node-link data) into Google OKF v0.1 bundles — and back. OKF bundles are structured Markdown catalogs designed for progressive disclosure: LLMs query individual concept files instead of loading monolithic JSON graphs.

### Quick Start

```bash
pip install pyyaml
git clone https://github.com/hah23255/okf-graphify.git
cd okf-graphify
python tests/test_suite.py
```

```bash
# Export a graph
python src/graphify_okf_integration_poc.py export my_graph.json my_bundle/

# Validate the bundle
python src/validate_okf.py my_bundle/

# Import back
python src/graphify_okf_integration_poc.py extract my_bundle/ reconstructed.json
```

### Features

| Feature | Description |
|---|---|
| **Bi-directional** | Export Graphify graphs to OKF, import OKF bundles back to graphs |
| **OKF v0.1 Compliant** | Strict adherence to Google's Open Knowledge Format specification |
| **Progressive Disclosure** | Load individual concept files instead of entire graphs |
| **YAML Frontmatter** | Every concept file carries structured metadata (type, tags, graphify_id, timestamp) |
| **Cross-references** | Markdown-native links between concepts form a navigable knowledge graph |
| **Validator Included** | Built-in conformance checker for OKF v0.1 bundles |
| **Round-trip Fidelity** | `graphify_id` preserved in frontmatter for lossless import/export |
| **Git-Native** | Isolated concept files — zero merge conflicts |

### Architecture

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│  graph.json  │ ────► │  OKF Bundle  │ ────► │  graph.json  │
│  (Graphify)  │       │  (concepts/) │       │  (imported)  │
└──────────────┘       └──────────────┘       └──────────────┘
      Export                  Validate              Extract

OKF Bundle/
├── index.md          ← master catalog, no frontmatter
├── log.md            ← change history
└── concepts/
    ├── Core/
    │   ├── parse_config().md
    │   └── DatabaseConnection.md
    └── Data/
        └── UserModel.md
```

### Project Structure

```
okf-graphify/
├── README.md
├── LICENSE
├── pyproject.toml
├── src/
│   ├── graphify_okf_integration_poc.py   Exporter + Extractor
│   └── validate_okf.py                   OKF v0.1 Validator
├── tests/
│   └── test_suite.py                     5 integration tests
├── docs/
│   ├── audit_report.md                   Engineering audit
│   ├── production_roadmap.md             KPIs, gateways, maturity model
│   ├── deployment_guide.md               Step-by-step deployment
│   └── raw_roadmap.md                    Original planning document
└── examples/
    └── example_bundle/                   Working OKF v0.1 bundle
```

---

## 🇧🇬 Български

Production-ready Python инструментариум за двупосочна конверзия между графи на знания от Graphify (NetworkX node-link данни) и Google OKF v0.1 пакети. OKF пакетите са структурирани Markdown каталози, проектирани за прогресивно разкриване: LLM-ите зареждат отделни концептуални файлове вместо монолитни JSON графи.

### Бърз старт

```bash
pip install pyyaml
git clone https://github.com/hah23255/okf-graphify.git
cd okf-graphify
python tests/test_suite.py
```

```bash
# Експортиране на граф
python src/graphify_okf_integration_poc.py export my_graph.json my_bundle/

# Валидиране на пакета
python src/validate_okf.py my_bundle/

# Обратен импорт
python src/graphify_okf_integration_poc.py extract my_bundle/ reconstructed.json
```

### Функционалности

| Функция | Описание |
|---|---|
| **Двупосочна конверзия** | Експорт от Graphify графи към OKF и обратен импорт |
| **OKF v0.1 съвместимост** | Стриктно спазване на спецификацията на Google Open Knowledge Format |
| **Прогресивно разкриване** | Зареждане на отделни концептуални файлове вместо цели графи |
| **YAML Frontmatter** | Всеки концептуален файл съдържа структурирани метаданни (тип, тагове, graphify_id, времеви печат) |
| **Кръстосани референции** | Markdown линкове между концептите формират навигационен граф на знанието |
| **Вграден валидатор** | Инструмент за проверка на съответствието с OKF v0.1 |
| **Точност при двупосочна конверзия** | `graphify_id` се запазва във frontmatter-а за точност при импорт/експорт |
| **Git-съвместимост** | Изолирани концептуални файлове — нулеви конфликти при сливане |

### Архитектура

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│  graph.json  │ ────► │  OKF Bundle  │ ────► │  graph.json  │
│  (Graphify)  │       │  (concepts/) │       │  (импортиран) │
└──────────────┘       └──────────────┘       └──────────────┘
     Експорт                Валидация              Извличане

OKF Bundle/
├── index.md          ← главен каталог, без frontmatter
├── log.md            ← хронология на промените
└── concepts/
    ├── Core/
    │   ├── parse_config().md
    │   └── DatabaseConnection.md
    └── Data/
        └── UserModel.md
```

### Структура на проекта

```
okf-graphify/
├── README.md
├── LICENSE
├── pyproject.toml
├── src/
│   ├── graphify_okf_integration_poc.py   Експорт + Импорт
│   └── validate_okf.py                   OKF v0.1 Валидатор
├── tests/
│   └── test_suite.py                     5 интеграционни теста
├── docs/
│   ├── audit_report.md                   Инженерен одит
│   ├── production_roadmap.md             KPI, gateways, maturity модел
│   ├── deployment_guide.md               Ръководство за внедряване
│   └── raw_roadmap.md                    Оригинален план
└── examples/
    └── example_bundle/                   Работещ OKF v0.1 пакет
```

---

## Tags / Тагове

`okf` `open-knowledge-format` `graphify` `knowledge-graph` `llm` `python` `bidirectional` `markdown` `progressive-disclosure` `git-native` `google-okf` `codebase-analysis`

---

## License / Лиценз

MIT — see [LICENSE](LICENSE).

---

## Author / Автор

HH
