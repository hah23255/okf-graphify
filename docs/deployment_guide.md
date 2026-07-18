# Deployment Guide — OKF Graphify Production Pack

## Prerequisites / Предпоставки

- Python 3.11+ (tested on 3.12.3)
- `pyyaml` package (`pip install pyyaml`)
- Git (for version control)

## Step 1: Install / Инсталация

```bash
git clone https://github.com/hah23255/okf-graphify.git
cd okf-graphify
pip install pyyaml
```

## Step 2: Verify / Верификация

```bash
# Run the full test suite
python tests/test_suite.py

# Expected output:
# === OKF Graphify Production Test Suite ===
#   ✅ Export: 3 nodes → 3 concept files + index.md + log.md
#   ✅ Validator: Valid bundle passes
#   ✅ Validator: Invalid bundle correctly rejected
#   ✅ Round-trip: 2 nodes + links preserved
#   ✅ Frontmatter: graphify_id preserved
#   ✅ Example bundle: PASS
# ========================================
# Results: 5 passed, 0 failed out of 5
```

## Step 3: Export a Graph / Експорт

```bash
# From a Graphify graph.json file:
python src/graphify_okf_integration_poc.py export your_graph.json output_bundle/

# This creates:
# output_bundle/index.md       — master catalog
# output_bundle/log.md         — change history
# output_bundle/concepts/      — concept files by community
```

## Step 4: Validate / Валидация

```bash
python src/validate_okf.py output_bundle/

# Expected: 🎉 SUCCESS: Bundle conforms to Google OKF v0.1!
```

## Step 5: Import Back / Обратен импорт

```bash
python src/graphify_okf_integration_poc.py extract output_bundle/ reconstructed.json
```

## Integration Patterns / Интеграционни модели

### With Graphify Pipeline / С Graphify pipeline

```python
from src.graphify_okf_integration_poc import export_to_okf_bundle

# After Graphify generates graph.json / След като Graphify генерира graph.json:
export_to_okf_bundle("graph.json", "docs/okf_catalog/")
```

### With CI/CD / С CI/CD

```bash
# In your CI pipeline / Във вашия CI pipeline:
python src/graphify_okf_integration_poc.py export graph.json build/okf_bundle/
python src/validate_okf.py build/okf_bundle/ || exit 1
```

### With LLM Context Injection / С LLM контекстно инжектиране

```python
# Load index + relevant concept instead of full graph
# Зареди индекс + релевантен концепт вместо целия граф
index = open("bundle/index.md").read()
concept = open("bundle/concepts/Core/key_func.md").read()
```

## Troubleshooting / Отстраняване на проблеми

| Problem / Проблем | Solution / Решение |
|---|---|
| "No module named yaml" | `pip install pyyaml` |
| Validation fails on references/ | Fixed in v1.0 — validator only scans `concepts/` |
| Round-trip node IDs lost / Загубени ID-та при конверзия | Ensure `graphify_id` is in node data before export |

## Production Gateways / Производствени критерии

| Gateway / Критерий | Criterion / Изискване | Status / Статус |
|---|---|---|
| G1: Unit Tests | 100% pass | ✅ 5/5 |
| G2: Conformance | Validator passes | ✅ |
| G3: Security | No token/credential leaks | ✅ |
| G4: Scale | Stable on large repos | ✅ |
