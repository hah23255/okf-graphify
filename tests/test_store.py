from store import Entry, parse_entries, render_topic


def test_entry_render_full_metadata():
    e = Entry(date="2026-07-21", text="User prefers dark mode",
              source="session 2026-07-21", confidence="high")
    assert e.render() == ("* **[2026-07-21]** User prefers dark mode "
                          "*(source: session 2026-07-21, confidence: high)*")


def test_entry_render_no_metadata():
    assert Entry(date="2026-07-21", text="plain").render() == "* **[2026-07-21]** plain"


def test_parse_entries_roundtrip():
    text = ("# Preferences\n\n"
            "* **[2026-07-20]** likes tea *(source: dream, confidence: high)*\n"
            "* **[2026-07-21]** likes coffee\n")
    entries = parse_entries(text)
    assert len(entries) == 2
    assert entries[0].source == "dream" and entries[0].confidence == "high"
    assert entries[1].source == "" and entries[1].confidence == ""
    assert parse_entries(render_topic("preferences", entries)) == entries


def test_parse_entries_skips_non_entry_lines():
    assert parse_entries("# Title\n\nsome prose\n- not an entry\n") == []


def test_entry_key_normalizes_for_dedupe():
    a = Entry(date="2026-07-20", text="Likes  Tea!")
    b = Entry(date="2026-07-21", text="likes tea")
    assert a.key() == b.key()


def test_add_creates_topic_file(store):
    e = store.add("preferences", "likes tea", source="test", confidence="high")
    assert e.date and e.text == "likes tea"
    loaded = store.load("preferences")
    assert [x.text for x in loaded] == ["likes tea"]


def test_add_appends_in_order(store):
    store.add("facts", "first")
    store.add("facts", "second")
    assert [e.text for e in store.load("facts")] == ["first", "second"]


def test_unknown_topic_raises(store):
    import pytest
    from store import StoreError
    with pytest.raises(StoreError):
        store.add("nonsense", "x")


def test_concurrent_adds_lose_nothing(store):
    import threading
    def worker(i):
        for j in range(5):
            store.add("facts", f"w{i}-{j}")
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert len(store.load("facts")) == 20


def test_quarantine_on_invalid_bytes(store):
    (store.root / "facts.md").write_bytes(b"\xff\xfe garbage")
    assert store.load("facts") == []
    quarantined = list((store.root / ".corrupt").iterdir())
    assert len(quarantined) == 1
    assert quarantined[0].read_bytes() == b"\xff\xfe garbage"


def test_quarantine_on_unparseable_content(store):
    original = "# Facts\n\nsome prose line that is not an entry\n"
    (store.root / "facts.md").write_text(original, encoding="utf-8")
    store.add("facts", "x")
    quarantined = list((store.root / ".corrupt").iterdir())
    assert len(quarantined) == 1
    assert quarantined[0].read_text(encoding="utf-8") == original
    assert [e.text for e in store.load("facts")] == ["x"]


def test_quarantine_names_unique_same_day(store):
    qdir = store.root / ".corrupt"
    (store.root / "facts.md").write_bytes(b"\xff\xfe first")
    store.load("facts")
    (store.root / "facts.md").write_bytes(b"\xff\xfe second")
    store.load("facts")
    assert len(list(qdir.iterdir())) == 2


def test_add_sanitizes_multiline_text(store):
    e = store.add("facts", "line one\nline two")
    assert "\n" not in e.text
    assert [x.text for x in store.load("facts")] == ["line one line two"]


def test_replace_swaps_text(store):
    store.add("facts", "sky is green")
    assert store.replace("facts", "sky is green", "sky is blue") is True
    assert [e.text for e in store.load("facts")] == ["sky is blue"]


def test_replace_missing_returns_false(store):
    store.add("facts", "something")
    assert store.replace("facts", "absent", "new") is False


def test_replace_preserves_metadata(store):
    store.add("facts", "old", source="s", confidence="high")
    store.replace("facts", "old", "new")
    e = store.load("facts")[0]
    assert e.source == "s" and e.confidence == "high"


def test_remove_deletes_matching_entry(store):
    store.add("facts", "keep")
    store.add("facts", "drop")
    assert store.remove("facts", "drop") is True
    assert [e.text for e in store.load("facts")] == ["keep"]


def test_remove_missing_returns_false(store):
    assert store.remove("facts", "nothing") is False


def test_overflow_rolls_oldest_into_archive(store, monkeypatch):
    import store as store_mod
    monkeypatch.setitem(store_mod.TOPIC_BUDGETS, "facts", 120)
    for i in range(6):
        store.add("facts", f"entry number {i} with some padding text")
    active = store.load("facts")
    assert sum(len(e.render()) for e in active) <= 200  # budget + slack
    archive = (store.root / "archive.md").read_text()
    assert "entry number 0" in archive


def test_budget_not_enforced_when_under(store):
    store.add("facts", "tiny")
    assert not (store.root / "archive.md").exists()


def test_search_ranks_by_term_hits(store):
    store.add("facts", "python is a language")
    store.add("facts", "python snakes are large reptiles with scales")
    store.add("decisions", "chose postgres for the database")
    hits = store.search("python reptiles")
    assert hits[0][1].text.startswith("python snakes")
    assert all(topic in ("facts", "decisions") for topic, _ in hits)


def test_search_no_match_returns_empty(store):
    store.add("facts", "something")
    assert store.search("zzz qqq") == []


def test_recall_block_renders_index_within_budget(store):
    store.add("preferences", "likes tea")
    block = store.recall_block(budget=500)
    assert "likes tea" in block
    assert len(block) <= 500


def test_recall_block_prefers_existing_index(store):
    (store.root / "MEMORY.md").write_text("# Memory Index\n\nCUSTOM INDEX CONTENT\n")
    store.add("facts", "not in index")
    block = store.recall_block(budget=2000)
    assert "CUSTOM INDEX CONTENT" in block


