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
