"""Tests for the print-history disk store (no hardware required)."""

from __future__ import annotations

from dymo_print_ui.history_store import HistoryStore


def _add(store: HistoryStore, *, png: bytes = b"fake-png"):
    return store.add(
        png_bytes=png,
        document={"elements": [], "marginLeft": 8, "marginRight": 8},
        width=100,
        height=30,
        stretch=2,
        dither=False,
        padding=0,
    )


def test_add_creates_entry_and_png_file(tmp_path) -> None:
    store = HistoryStore(data_dir=tmp_path)
    entry = _add(store)
    assert (tmp_path / "history" / f"{entry.id}.png").read_bytes() == b"fake-png"
    assert store.get(entry.id) == entry


def test_list_returns_newest_first(tmp_path) -> None:
    store = HistoryStore(data_dir=tmp_path)
    older = _add(store)
    newer = _add(store)
    older.timestamp = "2020-01-01T00:00:00+00:00"
    newer.timestamp = "2021-01-01T00:00:00+00:00"
    store._entries = [older, newer]
    entries = store.list()
    assert [e.id for e in entries] == [newer.id, older.id]


def test_get_unknown_id_returns_none(tmp_path) -> None:
    store = HistoryStore(data_dir=tmp_path)
    assert store.get("does-not-exist") is None


def test_delete_removes_entry_and_png(tmp_path) -> None:
    store = HistoryStore(data_dir=tmp_path)
    entry = _add(store)
    png_path = tmp_path / "history" / f"{entry.id}.png"
    assert png_path.exists()
    assert store.delete(entry.id) is True
    assert store.get(entry.id) is None
    assert not png_path.exists()


def test_delete_unknown_id_returns_false(tmp_path) -> None:
    store = HistoryStore(data_dir=tmp_path)
    assert store.delete("does-not-exist") is False


def test_png_path_rejects_path_traversal(tmp_path) -> None:
    store = HistoryStore(data_dir=tmp_path)
    assert store.png_path("../../etc/passwd") is None
    assert store.png_path("not-a-valid-id") is None


def test_index_survives_reload(tmp_path) -> None:
    store = HistoryStore(data_dir=tmp_path)
    entry = _add(store)
    reloaded = HistoryStore(data_dir=tmp_path)
    assert reloaded.get(entry.id) == entry


def test_corrupt_index_falls_back_gracefully(tmp_path) -> None:
    (tmp_path / "history.json").write_text("not json", encoding="utf-8")
    store = HistoryStore(data_dir=tmp_path)
    assert store.list() == []
