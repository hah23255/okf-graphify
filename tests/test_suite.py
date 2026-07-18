#!/usr/bin/env python3
"""Test suite for OKF Graphify Integration — production deployment validation."""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from validate_okf import validate_okf_bundle
from graphify_okf_integration_poc import export_to_okf_bundle, extract_okf_bundle_to_graph


def test_export_okf_bundle():
    """Test: Export graph.json → OKF v0.1 bundle, verify all concept files created."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test graph
        graph = {
            "directed": True,
            "multigraph": False,
            "graph": {},
            "nodes": [
                {"id": "node_a", "label": "Function A", "file_type": "code",
                 "source_file": "main.py", "source_location": "L10",
                 "community": 1, "community_name": "Core"},
                {"id": "node_b", "label": "Class B", "file_type": "code",
                 "source_file": "models.py", "source_location": "L25",
                 "community": 2, "community_name": "Data"},
                {"id": "node_c", "label": "Utility C", "file_type": "code",
                 "source_file": "utils.py", "source_location": "L5",
                 "community": 1, "community_name": "Core"},
            ],
            "links": [
                {"source": "node_a", "target": "node_b", "relation": "calls", "confidence": "HIGH"},
                {"source": "node_b", "target": "node_c", "relation": "imports", "confidence": "HIGH"},
            ]
        }
        
        graph_path = os.path.join(tmpdir, "test_graph.json")
        bundle_path = os.path.join(tmpdir, "test_bundle")
        
        with open(graph_path, "w") as f:
            json.dump(graph, f)
        
        export_to_okf_bundle(graph_path, bundle_path)
        
        # Verify structure
        assert os.path.exists(os.path.join(bundle_path, "index.md")), "Missing index.md"
        assert os.path.exists(os.path.join(bundle_path, "log.md")), "Missing log.md"
        
        concepts = list(Path(bundle_path).glob("concepts/**/*.md"))
        assert len(concepts) == 3, f"Expected 3 concept files, got {len(concepts)}"
        
        print("  ✅ Export: 3 nodes → 3 concept files + index.md + log.md")


def test_okf_validator():
    """Test: OKF v0.1 validator passes on valid bundle, rejects invalid."""
    with tempfile.TemporaryDirectory() as tmpdir:
        bundle = Path(tmpdir)
        (bundle / "concepts").mkdir()
        (bundle / "log.md").write_text("# Log\n\n## 2026-01-01\n- Created")
        (bundle / "index.md").write_text("# Index\n\nWelcome")
        
        # Valid concept
        (bundle / "concepts" / "test.md").write_text(
            "---\ntype: test\ntitle: Test Concept\ntags: [test]\n---\n\n# Test\nBody"
        )
        
        ok, issues = validate_okf_bundle(str(bundle))
        assert ok, f"Valid bundle should pass: {issues}"
        print("  ✅ Validator: Valid bundle passes")
        
        # Invalid concept (no frontmatter)
        (bundle / "concepts" / "bad.md").write_text("# No frontmatter here")
        ok, issues = validate_okf_bundle(str(bundle))
        assert not ok, "Invalid bundle should fail"
        print("  ✅ Validator: Invalid bundle correctly rejected")


def test_extract_round_trip():
    """Test: Export → Extract round-trip preserves structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create graph with graphify_id-compatible data
        graph = {
            "directed": True, "multigraph": False, "graph": {},
            "nodes": [
                {"id": "alpha", "label": "Alpha Component", "file_type": "code",
                 "source_file": "alpha.py", "source_location": "L1",
                 "community": 1, "community_name": "Alpha"},
                {"id": "beta", "label": "Beta Component", "file_type": "code",
                 "source_file": "beta.py", "source_location": "L1",
                 "community": 1, "community_name": "Alpha"},
            ],
            "links": [
                {"source": "alpha", "target": "beta", "relation": "uses", "confidence": "HIGH"},
            ]
        }
        
        graph_path = os.path.join(tmpdir, "test_graph.json")
        bundle_path = os.path.join(tmpdir, "test_bundle")
        roundtrip_path = os.path.join(tmpdir, "roundtrip.json")
        
        with open(graph_path, "w") as f:
            json.dump(graph, f)
        
        export_to_okf_bundle(graph_path, bundle_path)
        extract_okf_bundle_to_graph(bundle_path, roundtrip_path)
        
        with open(roundtrip_path) as f:
            rt = json.load(f)
        
        assert len(rt["nodes"]) == 2, f"Expected 2 nodes in round-trip, got {len(rt['nodes'])}"
        assert len(rt["links"]) >= 1, f"Expected >=1 links, got {len(rt['links'])}"
        
        print("  ✅ Round-trip: 2 nodes + links preserved")


def test_frontmatter_graphify_id():
    """Test: Exported frontmatter contains graphify_id for round-trip fidelity."""
    with tempfile.TemporaryDirectory() as tmpdir:
        graph = {
            "directed": True, "multigraph": False, "graph": {},
            "nodes": [
                {"id": "test_id_42", "label": "Test Function", "file_type": "code",
                 "source_file": "test.py", "source_location": "L42",
                 "community": 1, "community_name": "Test"},
            ],
            "links": []
        }
        
        graph_path = os.path.join(tmpdir, "test_graph.json")
        bundle_path = os.path.join(tmpdir, "test_bundle")
        
        with open(graph_path, "w") as f:
            json.dump(graph, f)
        
        export_to_okf_bundle(graph_path, bundle_path)
        
        # Read concept file and check for graphify_id in frontmatter
        concept_files = list(Path(bundle_path).glob("concepts/**/*.md"))
        assert len(concept_files) >= 1
        
        content = concept_files[0].read_text()
        assert "graphify_id: test_id_42" in content, "Missing graphify_id in frontmatter"
        
        print("  ✅ Frontmatter: graphify_id preserved")


def test_smoke_real_bundle():
    """Smoke-test: Validate the included example bundle."""
    example_dir = Path(__file__).parent.parent / "examples" / "example_bundle"
    if example_dir.exists():
        ok, issues = validate_okf_bundle(str(example_dir))
        print(f"  {'✅' if ok else '❌'} Example bundle: {'PASS' if ok else 'FAIL'}")
        if issues:
            for i in issues[:3]:
                print(f"     {i}")
    else:
        print("  ⚠️ Example bundle not found (skipped)")


if __name__ == "__main__":
    print("=== OKF Graphify Production Test Suite ===\n")
    tests = [
        test_export_okf_bundle,
        test_okf_validator,
        test_extract_round_trip,
        test_frontmatter_graphify_id,
        test_smoke_real_bundle,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ❌ {test.__name__}: {e}")
            failed += 1
    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)}")
    sys.exit(0 if failed == 0 else 1)
