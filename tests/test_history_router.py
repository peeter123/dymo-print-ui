"""Router-level tests for print-history endpoints that don't need BLE."""

from __future__ import annotations

from fastapi.testclient import TestClient

from dymo_print_ui.app import create_app
from dymo_print_ui.history_store import HistoryStore
from dymo_print_ui.routers import history as history_router


def _client(tmp_path, monkeypatch) -> TestClient:
    store = HistoryStore(data_dir=tmp_path)
    monkeypatch.setattr(history_router, "history", store)
    return TestClient(create_app())


def _seed(tmp_path, monkeypatch):
    store = HistoryStore(data_dir=tmp_path)
    monkeypatch.setattr(history_router, "history", store)
    entry = store.add(
        png_bytes=b"fake-png",
        document={"elements": [], "marginLeft": 8, "marginRight": 8},
        width=100,
        height=30,
        stretch=2,
        dither=False,
        padding=0,
    )
    return TestClient(create_app()), entry


def test_list_empty(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    res = client.get("/api/history")
    assert res.status_code == 200
    assert res.json() == {"entries": []}


def test_get_entry_returns_document(tmp_path, monkeypatch) -> None:
    client, entry = _seed(tmp_path, monkeypatch)
    res = client.get(f"/api/history/{entry.id}")
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == entry.id
    assert body["document"] == entry.document


def test_get_unknown_entry_404(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    res = client.get("/api/history/does-not-exist")
    assert res.status_code == 404


def test_thumbnail_serves_png_bytes(tmp_path, monkeypatch) -> None:
    client, entry = _seed(tmp_path, monkeypatch)
    res = client.get(f"/api/history/{entry.id}/thumbnail.png")
    assert res.status_code == 200
    assert res.content == b"fake-png"


def test_delete_entry(tmp_path, monkeypatch) -> None:
    client, entry = _seed(tmp_path, monkeypatch)
    res = client.delete(f"/api/history/{entry.id}")
    assert res.status_code == 200
    assert client.get(f"/api/history/{entry.id}").status_code == 404


def test_delete_unknown_entry_404(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    res = client.delete("/api/history/does-not-exist")
    assert res.status_code == 404
