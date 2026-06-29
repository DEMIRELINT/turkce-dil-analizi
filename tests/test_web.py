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
    assert job == {"kind": "text", "text": "merhaba", "path": None}
    # Tek kullanımlık: ikinci pop None döner.
    assert store.pop(job_id) is None


def test_jobstore_unknown_id_returns_none():
    assert server.JobStore().pop("yok") is None
