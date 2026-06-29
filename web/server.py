"""Yerel web paneli — saf stdlib (sıfır yeni bağımlılık).

Amaç: terminal yerine, analiz adımlarını CANLI gösteren bir arayüz. Tarayıcı bir
docx yükler ya da metin yapıştırır; sunucu analizi çalıştırırken her adımı (parça
parça yazım/ton, tutarlılık, sonuç) Server-Sent Events (SSE) ile akıtır.

Güvenlik / air-gap:
- Yalnız 127.0.0.1'e bağlanır; dışarı açılmaz.
- GEMINI_API_KEY sunucuda kalır, tarayıcıya asla gönderilmez.
- Harici CDN/script/font yok (index.html tamamen yerel).
- Sıfır yeni Python bağımlılığı (stdlib http.server).

Çalıştırma:
    python web/server.py            # tarayıcı otomatik açılır
    PORT=9000 python web/server.py  # farklı port
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Paket src/ altında; sunucu repo kökünden çalıştırılır.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from dilanaliz.analyzer import build_default_analyzer  # noqa: E402
from dilanaliz.extract import extract_docx  # noqa: E402
from dilanaliz.progress import ProgressEvent  # noqa: E402

HOST = "127.0.0.1"
PORT = int(os.environ.get("PORT", "8765"))
MAX_UPLOAD = 25 * 1024 * 1024  # 25 MB — kötü niyetli/yanlış yüklemeye karşı sınır
INDEX_HTML = Path(__file__).resolve().parent / "index.html"


def sse_format(event: str, data: str) -> bytes:
    """Bir SSE olayını tel-üstü biçime çevirir (test edilebilir saf fonksiyon)."""
    # Çok satırlı veriyi her satır 'data:' ile gönder; olay '\n\n' ile biter.
    lines = "".join(f"data: {line}\n" for line in data.split("\n"))
    return f"event: {event}\n{lines}\n".encode("utf-8")


class JobStore:
    """Yükleme ile akış arasında küçük, iş-parçacığı-güvenli köprü.

    Yükleme ham baytı/metni saklar ve bir kimlik döndürür; akış o kimlikle işi
    alıp tüketir (tek kullanımlık).
    """

    def __init__(self) -> None:
        self._jobs: dict[str, dict] = {}
        self._lock = threading.Lock()

    def add(self, kind: str, *, text: str | None = None, path: str | None = None) -> str:
        job_id = uuid.uuid4().hex
        with self._lock:
            self._jobs[job_id] = {"kind": kind, "text": text, "path": path}
        return job_id

    def pop(self, job_id: str) -> dict | None:
        with self._lock:
            return self._jobs.pop(job_id, None)


# Analyzer pahalı (model + sözlük + önbellek); bir kez kurup paylaşırız.
# Tembel kurulum: GEMINI_API_KEY yoksa sunucu yine açılır, hata akışta bildirilir.
_analyzer = None
_analyzer_lock = threading.Lock()


def get_analyzer():
    global _analyzer
    with _analyzer_lock:
        if _analyzer is None:
            _analyzer = build_default_analyzer()
        return _analyzer


class Handler(BaseHTTPRequestHandler):
    jobs = JobStore()

    # Konsolu sessiz tut (her istek için satır basma).
    def log_message(self, *args) -> None:  # noqa: ANN002, D102
        pass

    # --- yardımcılar -------------------------------------------------------
    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _sse(self, event: str, data: str) -> None:
        self.wfile.write(sse_format(event, data))
        self.wfile.flush()

    # --- yönlendirme -------------------------------------------------------
    def do_GET(self) -> None:
        route = urlparse(self.path)
        if route.path == "/":
            self._serve_index()
        elif route.path == "/logo.png":
            self._serve_logo()
        elif route.path == "/stream":
            self._serve_stream(parse_qs(route.query))
        else:
            self._send(404, b"yok", "text/plain; charset=utf-8")

    def do_POST(self) -> None:
        route = urlparse(self.path)
        if route.path == "/upload":
            self._serve_upload(parse_qs(route.query))
        else:
            self._send(404, b"yok", "text/plain; charset=utf-8")

    # --- uç noktalar -------------------------------------------------------
    def _serve_index(self) -> None:
        try:
            body = INDEX_HTML.read_bytes()
        except OSError:
            self._send(500, b"index.html bulunamadi", "text/plain; charset=utf-8")
            return
        self._send(200, body, "text/html; charset=utf-8")

    def _serve_logo(self) -> None:
        # Yalnız web/logo.png — sabit yol (path traversal yok).
        logo = INDEX_HTML.parent / "logo.png"
        try:
            body = logo.read_bytes()
        except OSError:
            self._send(404, b"logo yok", "text/plain; charset=utf-8")
            return
        self._send(200, body, "image/png")

    def _serve_upload(self, query: dict) -> None:
        kind = (query.get("kind") or ["text"])[0]
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_UPLOAD:
            self._send(400, b'{"error":"gecersiz boyut"}', "application/json")
            return
        raw = self.rfile.read(length)

        if kind == "docx":
            # Geçici .docx'e yaz; akış sonunda silinir.
            fd, path = tempfile.mkstemp(suffix=".docx")
            with os.fdopen(fd, "wb") as fh:
                fh.write(raw)
            job_id = self.jobs.add("docx", path=path)
        else:
            job_id = self.jobs.add("text", text=raw.decode("utf-8", errors="replace"))

        body = json.dumps({"job": job_id}).encode("utf-8")
        self._send(200, body, "application/json")

    def _serve_stream(self, query: dict) -> None:
        job_id = (query.get("job") or [""])[0]
        job = self.jobs.pop(job_id)
        if job is None:
            self._send(404, b'{"error":"is bulunamadi"}', "application/json")
            return

        # SSE başlıkları
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()

        try:
            self._run_analysis(job)
        except BrokenPipeError:
            pass  # tarayıcı sekmeyi kapattı — sessizce bırak
        except Exception as exc:  # noqa: BLE001 — kullanıcıya okunur hata göster
            self._sse("error", json.dumps({"message": f"{type(exc).__name__}: {exc}"}))
        finally:
            if job.get("kind") == "docx" and job.get("path"):
                try:
                    os.unlink(job["path"])
                except OSError:
                    pass

    def _run_analysis(self, job: dict) -> None:
        if job["kind"] == "docx":
            self._sse("progress", json.dumps(
                {"stage": "extract", "message": "Belge metni çıkarılıyor", "current": 0, "total": 0}))
            text = extract_docx(job["path"])
        else:
            text = job["text"] or ""

        if not text.strip():
            self._sse("error", json.dumps({"message": "Analiz edilecek metin yok."}))
            return

        def on_progress(ev: ProgressEvent) -> None:
            self._sse("progress", json.dumps({
                "stage": ev.stage, "message": ev.message,
                "current": ev.current, "total": ev.total,
            }))

        analyzer = get_analyzer()
        result = analyzer.analyze_document(text, progress=on_progress)

        payload = {
            "source": text,
            "result": result.model_dump(mode="json"),
        }
        self._sse("result", json.dumps(payload, ensure_ascii=False))
        self._sse("done", "{}")


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}"
    print(f"Dil analiz paneli: {url}  (durdurmak için Ctrl+C)")
    try:
        webbrowser.open(url)
    except Exception:  # noqa: BLE001 — tarayıcı açılamazsa URL'yi elle aç
        pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nKapatılıyor.")
        server.shutdown()


if __name__ == "__main__":
    main()
