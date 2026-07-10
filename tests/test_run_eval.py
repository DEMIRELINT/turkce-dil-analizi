"""`eval/run_eval._analyze_with_retry` — örnek-bazlı retry/atla kararı (API'siz).

Sözleşme: geçici hata örnek içinde yeniden denenir, tükenirse (None, hata)
döner (çağıran örneği atlar, koşu sürer); KALICI hata (kapatılmış model)
yeniden denenmez, yukarı fırlar (tüm koşu durur — devam anlamsız).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# eval/ bir paket değil; run_eval modülünü yoluyla içe aktar.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "eval"))

from run_eval import _analyze_with_retry  # noqa: E402

from dilanaliz.analyzer import LLMCallError  # noqa: E402


class _FlakyAnalyzer:
    """İlk `fail_count` çağrıda verilen hatayı atan, sonra "ok" dönen sahte."""

    def __init__(self, exc: Exception, fail_count: int = 10**9) -> None:
        self._exc = exc
        self._fail_count = fail_count
        self.calls = 0

    def analyze(self, text):  # noqa: ARG002
        self.calls += 1
        if self.calls <= self._fail_count:
            raise self._exc
        return "ok"

    def analyze_document(self, text):
        return self.analyze(text)


def test_transient_error_is_retried_then_succeeds():
    analyzer = _FlakyAnalyzer(LLMCallError("zaman aşımı"), fail_count=2)
    result, err = _analyze_with_retry(analyzer, {"text": "m"}, attempts=3)
    assert result == "ok"
    assert err is None
    assert analyzer.calls == 3


def test_transient_error_exhausts_attempts_and_returns_error():
    analyzer = _FlakyAnalyzer(LLMCallError("zaman aşımı"))
    result, err = _analyze_with_retry(analyzer, {"text": "m"}, attempts=3)
    assert result is None
    assert isinstance(err, LLMCallError)
    assert analyzer.calls == 3  # koşu ölmedi, örnek atlanacak


def test_permanent_error_raises_immediately_without_retry():
    analyzer = _FlakyAnalyzer(LLMCallError("model kapalı", permanent=True))
    with pytest.raises(LLMCallError):
        _analyze_with_retry(analyzer, {"text": "m"}, attempts=3)
    assert analyzer.calls == 1  # kalıcı: tek deneme, anında yukarı


def test_non_llm_exception_treated_as_transient():
    # Kota (429) gibi kütüphane istisnaları da geçici sayılır.
    analyzer = _FlakyAnalyzer(RuntimeError("429 quota"), fail_count=1)
    result, err = _analyze_with_retry(analyzer, {"text": "m"}, attempts=3)
    assert result == "ok"
    assert err is None


def test_document_mode_routes_to_analyze_document():
    class _DocAnalyzer:
        def __init__(self):
            self.doc_calls = 0

        def analyze(self, text):  # noqa: ARG002
            raise AssertionError("document modunda analyze çağrılmamalı")

        def analyze_document(self, text):  # noqa: ARG002
            self.doc_calls += 1
            return "doc-ok"

    analyzer = _DocAnalyzer()
    result, err = _analyze_with_retry(analyzer, {"text": "m", "mode": "document"})
    assert result == "doc-ok"
    assert err is None
    assert analyzer.doc_calls == 1
