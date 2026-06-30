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
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Paket src/ altında; sunucu repo kökünden çalıştırılır.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from dilanaliz.analyzer import build_default_analyzer  # noqa: E402
from dilanaliz.extract import extract_docx_with_report  # noqa: E402
from dilanaliz.progress import ProgressEvent  # noqa: E402

HOST = "127.0.0.1"
PORT = int(os.environ.get("PORT", "8765"))
MAX_UPLOAD = 25 * 1024 * 1024  # 25 MB — kötü niyetli/yanlış yüklemeye karşı sınır
INDEX_HTML = Path(__file__).resolve().parent / "index.html"
# Analiz geçmişi: her kayıt ayrı bir <id>.json. Varsayılan <repo>/history;
# air-gap dostu (yerel disk, ağ yok). Kullanıcı verisi → .gitignore'da.
HISTORY_DIR = Path(
    os.environ.get("HISTORY_DIR", str(Path(__file__).resolve().parent.parent / "history"))
)


def sse_format(event: str, data: str) -> bytes:
    """Bir SSE olayını tel-üstü biçime çevirir (test edilebilir saf fonksiyon)."""
    # Çok satırlı veriyi her satır 'data:' ile gönder; olay '\n\n' ile biter.
    lines = "".join(f"data: {line}\n" for line in data.split("\n"))
    return f"event: {event}\n{lines}\n".encode("utf-8")


# Geçmiş kaydının başlık/sayım türetme: arayüzden bağımsız, test edilebilir saf
# fonksiyonlar. Eksen anahtarları schema.Finding.type ile ve index.html'deki
# TYPES dizisiyle aynı olmalı.
_FINDING_TYPES = ("imla", "dil_bilgisi", "ton", "tutarlilik")


def make_title(source: str, limit: int = 60) -> str:
    """Metin girişi için başlık: ilk dolu satırın ilk ~limit karakteri."""
    first = next((ln.strip() for ln in source.splitlines() if ln.strip()), "")
    if not first:
        return "(boş)"
    return first if len(first) <= limit else first[: limit - 1].rstrip() + "…"


def finding_counts(findings: list[dict]) -> dict:
    """Bulguları eksene göre sayar: {'toplam': N, 'imla': .., ...}."""
    counts = {"toplam": len(findings)}
    for t in _FINDING_TYPES:
        counts[t] = sum(1 for f in findings if f.get("type") == t)
    return counts


def build_history_record(
    payload: dict,
    *,
    kind: str,
    title: str,
    extract: dict | None = None,
) -> dict:
    """Tam bir geçmiş kaydı dict'i kurar (HistoryStore.save'in beklediği şekil)."""
    findings = (payload.get("result") or {}).get("findings") or []
    return {
        "id": uuid.uuid4().hex,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "kind": kind,
        "title": title,
        "counts": finding_counts(findings),
        "extract": extract,
        "payload": payload,
    }


class JobStore:
    """Yükleme ile akış arasında küçük, iş-parçacığı-güvenli köprü.

    Yükleme ham baytı/metni saklar ve bir kimlik döndürür; akış o kimlikle işi
    alıp tüketir (tek kullanımlık).
    """

    def __init__(self) -> None:
        self._jobs: dict[str, dict] = {}
        self._lock = threading.Lock()

    def add(
        self,
        kind: str,
        *,
        text: str | None = None,
        path: str | None = None,
        title: str | None = None,
    ) -> str:
        job_id = uuid.uuid4().hex
        with self._lock:
            self._jobs[job_id] = {"kind": kind, "text": text, "path": path, "title": title}
        return job_id

    def pop(self, job_id: str) -> dict | None:
        with self._lock:
            return self._jobs.pop(job_id, None)


# Bir kaydın listede gösterilen hafif alanları (payload hariç — liste küçük kalsın).
_META_FIELDS = ("id", "created_at", "kind", "title", "counts")


class HistoryStore:
    """Analiz çıktılarını diske JSON olarak saklayan kalıcı geçmiş deposu.

    Her kayıt ``<dir>/<id>.json`` dosyasıdır; böylece listeleme/silme dosya
    bazında basit ve sunucu yeniden başlasa da kayıtlar korunur. Tüm dosya
    işlemleri tek bir kilitle korunur (ThreadingHTTPServer çok iş parçacıklıdır).
    """

    def __init__(self, directory: Path) -> None:
        self._dir = Path(directory)
        self._lock = threading.Lock()

    def _path(self, rec_id: str) -> Path:
        # Kimlik yalnız uuid4 hex (32 onaltılık) ürettiğimizden güvenli; yine de
        # dışarıdan gelen id'lerde yol kaçışını engellemek için sadece dosya adını al.
        return self._dir / f"{Path(rec_id).name}.json"

    def save(self, record: dict) -> str:
        """Tam kaydı diske yazar ve id'sini döner."""
        rec_id = record["id"]
        with self._lock:
            self._dir.mkdir(parents=True, exist_ok=True)
            path = self._path(rec_id)
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
            tmp.replace(path)  # atomik: yarım yazılmış dosya görünmesin
        return rec_id

    def list(self) -> list[dict]:
        """Kayıtların hafif meta listesi (payload'sız), en yeni en üstte."""
        with self._lock:
            if not self._dir.exists():
                return []
            metas: list[dict] = []
            for file in self._dir.glob("*.json"):
                try:
                    rec = json.loads(file.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue  # bozuk/yarım dosyayı atla, listeyi düşürme
                metas.append({k: rec.get(k) for k in _META_FIELDS})
        metas.sort(key=lambda m: m.get("created_at") or "", reverse=True)
        return metas

    def get(self, rec_id: str) -> dict | None:
        """Tek kaydın tamamını döner (payload dahil); yoksa None."""
        with self._lock:
            try:
                return json.loads(self._path(rec_id).read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return None

    def delete(self, rec_id: str) -> bool:
        """Kaydı siler; varsa True, yoksa False."""
        with self._lock:
            try:
                self._path(rec_id).unlink()
                return True
            except OSError:
                return False


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
    history = HistoryStore(HISTORY_DIR)

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
        elif route.path == "/history":
            self._serve_history_list()
        elif route.path == "/history/get":
            self._serve_history_get(parse_qs(route.query))
        else:
            self._send(404, b"yok", "text/plain; charset=utf-8")

    def do_POST(self) -> None:
        route = urlparse(self.path)
        if route.path == "/upload":
            self._serve_upload(parse_qs(route.query))
        elif route.path == "/history/delete":
            self._serve_history_delete(parse_qs(route.query))
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
        # docx'te dosya adı geçmiş kaydının başlığı olur (metinde başlık sonradan
        # kaynağın ilk satırından türetilir).
        name = (query.get("name") or [""])[0] or None
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
            job_id = self.jobs.add("docx", path=path, title=name)
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
        extract_info: dict | None = None
        if job["kind"] == "docx":
            self._sse("progress", json.dumps(
                {"stage": "extract", "message": "Belge metni çıkarılıyor", "current": 0, "total": 0}))
            text, report = extract_docx_with_report(job["path"])
            # Kapsam özeti + okunamayan içerik uyarıları (ör. görsel içi yazı).
            extract_info = {"summary": report.describe(), "warnings": report.warnings}
            self._sse("extract", json.dumps(extract_info))
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

        # Geçmişe kaydet (token harcamadan sonradan birebir görüntülemek için).
        record = build_history_record(
            payload,
            kind=job["kind"],
            title=job.get("title") or make_title(text),
            extract=extract_info,
        )
        try:
            self.history.save(record)
        except OSError:
            pass  # disk yazılamazsa analiz akışını bozma; sonuç yine gösterilir

        self._sse("result", json.dumps({**payload, "id": record["id"]}, ensure_ascii=False))
        self._sse("done", "{}")

    # --- geçmiş (log) uç noktaları ----------------------------------------
    def _serve_history_list(self) -> None:
        body = json.dumps(self.history.list(), ensure_ascii=False).encode("utf-8")
        self._send(200, body, "application/json; charset=utf-8")

    def _serve_history_get(self, query: dict) -> None:
        rec_id = (query.get("id") or [""])[0]
        record = self.history.get(rec_id) if rec_id else None
        if record is None:
            self._send(404, b'{"error":"kayit bulunamadi"}', "application/json")
            return
        body = json.dumps(record, ensure_ascii=False).encode("utf-8")
        self._send(200, body, "application/json; charset=utf-8")

    def _serve_history_delete(self, query: dict) -> None:
        rec_id = (query.get("id") or [""])[0]
        ok = self.history.delete(rec_id) if rec_id else False
        body = json.dumps({"ok": ok}).encode("utf-8")
        self._send(200 if ok else 404, body, "application/json")


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
