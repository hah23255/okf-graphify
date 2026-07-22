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
