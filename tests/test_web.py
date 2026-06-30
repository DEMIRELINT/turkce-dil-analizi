"""Web backend'in saf yardımcıları (sunucu başlatmadan, API'siz)."""

import importlib.util
from pathlib import Path

# web/ bir paket değil; modülü dosyadan yükle.
_SERVER = Path(__file__).resolve().parent.parent / "web" / "server.py"
_spec = importlib.util.spec_from_file_location("web_server", _SERVER)
server = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(server)


def test_sse_format_single_line():
    out = server.sse_format("progress", '{"a":1}')
    assert out == b'event: progress\ndata: {"a":1}\n\n'


def test_sse_format_multiline_prefixes_each_line():
    out = server.sse_format("result", "x\ny").decode("utf-8")
    # Çok satırlı veri her satırda 'data:' ile gönderilmeli (SSE kuralı).
    assert out == "event: result\ndata: x\ndata: y\n\n"


def test_jobstore_add_and_pop_is_single_use():
    store = server.JobStore()
    job_id = store.add("text", text="merhaba")
    job = store.pop(job_id)
    assert job == {"kind": "text", "text": "merhaba", "path": None, "title": None}
    # Tek kullanımlık: ikinci pop None döner.
    assert store.pop(job_id) is None


def test_jobstore_unknown_id_returns_none():
    assert server.JobStore().pop("yok") is None


# --- Geçmiş (log) yardımcıları -------------------------------------------

def test_make_title_uses_first_nonempty_line_and_truncates():
    assert server.make_title("\n  Merhaba dünya  \nikinci") == "Merhaba dünya"
    assert server.make_title("") == "(boş)"
    long = "x" * 100
    title = server.make_title(long, limit=60)
    assert len(title) == 60 and title.endswith("…")


def test_finding_counts_groups_by_axis():
    findings = [
        {"type": "imla"}, {"type": "imla"}, {"type": "ton"}, {"type": "bilinmeyen"},
    ]
    counts = server.finding_counts(findings)
    assert counts["toplam"] == 4
    assert counts["imla"] == 2
    assert counts["ton"] == 1
    assert counts["dil_bilgisi"] == 0
    assert counts["tutarlilik"] == 0


def test_build_history_record_shape():
    payload = {"source": "metin", "result": {"findings": [{"type": "imla"}]}}
    rec = server.build_history_record(payload, kind="text", title="başlık")
    assert rec["kind"] == "text"
    assert rec["title"] == "başlık"
    assert rec["counts"]["toplam"] == 1
    assert rec["payload"] is payload
    assert rec["extract"] is None
    assert isinstance(rec["id"], str) and rec["id"]
    assert rec["created_at"]  # ISO zaman damgası


def _record(server_mod, *, title="t", findings=None):
    payload = {"source": "s", "result": {"findings": findings or []}}
    return server_mod.build_history_record(payload, kind="text", title=title)


def test_historystore_save_list_get_delete_roundtrip(tmp_path):
    store = server.HistoryStore(tmp_path)
    assert store.list() == []  # boş dizinde sorunsuz

    rec = _record(server, title="ilk kayıt", findings=[{"type": "ton"}])
    rec_id = store.save(rec)

    # list() hafiftir: meta var, payload YOK.
    metas = store.list()
    assert len(metas) == 1
    meta = metas[0]
    assert meta["id"] == rec_id
    assert meta["title"] == "ilk kayıt"
    assert meta["counts"]["toplam"] == 1
    assert "payload" not in meta

    # get() tam kaydı döndürür (round-trip).
    full = store.get(rec_id)
    assert full == rec

    # delete() siler; sonra get None.
    assert store.delete(rec_id) is True
    assert store.get(rec_id) is None
    assert store.list() == []
    # Olmayan kaydı silmek False döner.
    assert store.delete(rec_id) is False


def test_historystore_list_is_newest_first(tmp_path):
    store = server.HistoryStore(tmp_path)
    older = _record(server, title="eski")
    older["created_at"] = "2026-06-01T10:00:00"
    newer = _record(server, title="yeni")
    newer["created_at"] = "2026-06-30T10:00:00"
    store.save(older)
    store.save(newer)
    titles = [m["title"] for m in store.list()]
    assert titles == ["yeni", "eski"]


def test_historystore_get_unknown_returns_none(tmp_path):
    assert server.HistoryStore(tmp_path).get("yok") is None
