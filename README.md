---
type: bilingual
languages: [en, bg]
version: 1.0.0
---

# OKF Graphify — Production Deployment Pack 🇬🇧🇧🇬

**Graphify ↔ Google Open Knowledge Format (OKF v0.1) — Bi-directional Integration Toolkit**

[![OKF v0.1](https://img.shields.io/badge/OKF-v0.1-blue)](https://google.github.io/okf/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-green)](https://python.org)
[![License MIT](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-5%2F5-brightgreen)](tests/)
![Status](https://img.shields.io/badge/status-production--ready-success)

> 🇧🇬 Инструментариум за двупосочна интеграция между Graphify и Google Open Knowledge Format (OKF v0.1). Конвертирайте графи на знания в LLM-четими каталози и обратно.

---

## What is this? / Какво е това?

**EN:** A production-ready Python toolkit that converts Graphify knowledge graphs (NetworkX node-link data) into Google OKF v0.1 bundles — and back. OKF bundles are structured Markdown catalogs designed for progressive disclosure: LLMs query individual concept files instead of loading monolithic JSON graphs.

**BG:** Production-ready Python инструментариум, който конвертира графи на знания от Graphify (NetworkX node-link данни) в Google OKF v0.1 пакети — и обратно. OKF пакетите са структурирани Markdown каталози, проектирани за прогресивно разкриване: LLM-ите зареждат отделни концептуални файлове вместо монолитни JSON графи.

---

## Quick Start / Бърз старт

```bash
# Install / Инсталация
pip install pyyaml
git clone https://github.com/hah23255/okf-graphify.git
cd okf-graphify

# Run tests / Пусни тестове
python tests/test_suite.py

# Export a graph / Експортирай граф
python src/graphify_okf_integration_poc.py export my_graph.json my_bundle/

# Validate the bundle / Валидирай пакета
python src/validate_okf.py my_bundle/

# Import back / Импортирай обратно
python src/graphify_okf_integration_poc.py extract my_bundle/ reconstructed.json
```

---

## Features / Функционалности

| Feature | Description |
|---|---|
| **Bi-directional** 🇬🇧 | Export Graphify graphs to OKF, import OKF bundles back to graphs. Двупосочна конверзия. |
| **OKF v0.1 Compliant** | Strict adherence to Google's Open Knowledge Format specification. Спазване на спецификацията. |
| **Progressive Disclosure** | Load individual concept files instead of entire graphs — context-efficient LLM queries. |
| **YAML Frontmatter** | Every concept file carries structured metadata (type, tags, graphify_id, timestamp). |
| **Cross-references** | Markdown-native links between concepts form a navigable knowledge graph. |
| **Validator Included** | Built-in conformance checker for OKF v0.1 bundles. Вграден валидатор. |
| **Round-trip Fidelity** | `graphify_id` preserved in frontmatter for lossless import/export. |
| **Git-Native** | Isolated concept files — zero merge conflicts. Нулеви конфликти при сливане. |

---

## Architecture / Архитектура

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│  graph.json  │ ────► │  OKF Bundle  │ ────► │  graph.json  │
│  (Graphify)  │       │  (concepts/) │       │  (imported)  │
└──────────────┘       └──────────────┘       └──────────────┘
      Export                  Validate              Extract
```

```
graph.json (10 nodes, 12 links)
    │  export_to_okf_bundle()
    ▼
OKF Bundle/
├── index.md          ← master catalog, no frontmatter
├── log.md            ← change history
└── concepts/
    ├── Core/
    │   ├── parse_config().md    ← YAML frontmatter + markdown body
    │   └── DatabaseConnection.md
    └── Data/
        └── UserModel.md
    │  validate_okf_bundle()  ← conformance check
    │  extract_okf_bundle_to_graph()
    ▼
graph.json (reconstructed)
```

---

## Performance / Производителност

OKF bundles improve LLM efficiency through progressive disclosure — queries target individual concept files (~1-2KB each) rather than loading entire graphs. See `docs/audit_report.md` for detailed analysis.

| Concept | Monolithic Graph | OKF Bundle | Benefit / Полза |
|---|---|---|---|
| Query granularity | Entire graph | Single concept file | Progressive disclosure |
| Load pattern | All-or-nothing | On-demand navigation | Context efficiency |
| File-level isolation | No (single JSON) | Yes (per-concept .md) | Git-native, zero merge conflicts |

---

## Project Structure / Структура

```
okf-graphify/
├── README.md                          ← This file
├── LICENSE                            ← MIT
├── pyproject.toml                     ← Package metadata
├── src/
│   ├── graphify_okf_integration_poc.py  ← Exporter + Extractor (490 lines)
│   └── validate_okf.py                  ← OKF v0.1 Validator (110 lines)
├── tests/
│   └── test_suite.py                    ← 5 integration tests
├── docs/
│   ├── audit_report.md                  ← Engineering audit
│   ├── production_roadmap.md            ← KPIs, gateways, maturity model
│   ├── deployment_guide.md              ← Step-by-step deployment
│   └── raw_roadmap.md                   ← Original planning document
└── examples/
    └── example_bundle/                  ← Working OKF v0.1 bundle
```

---

## Tags / Тагове

`okf` `open-knowledge-format` `graphify` `knowledge-graph` `llm` `token-optimization` `rag` `markdown` `progressive-disclosure` `yaml` `bidirectional` `python` `codebase-analysis` `context-window` `git-native` `google-okf`

---

## License / Лиценз

MIT — see [LICENSE](LICENSE).

---

## Author / Автор

HH 🇧🇬
