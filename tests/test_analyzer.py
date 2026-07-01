"""Analyzer'ın aday→düzeltme birleştirme mantığı (API gerektirmez)."""

from dilanaliz.analyzer import Analyzer
from dilanaliz.prompt import build_user_message
from dilanaliz.schema import (
    Finding,
    FindingType,
    LLMAnalysis,
    LLMFinding,
    LLMSpellingDecision,
)


def _candidate(excerpt: str, start: int, suggestion: str = "(öneri yok)") -> Finding:
    return Finding(
        type=FindingType.IMLA,
        excerpt=excerpt,
        explanation="Sözlükte yok.",
        suggestion=suggestion,
        rule_id="HUNSPELL",
        start=start,
        end=start + len(excerpt),
    )


def test_real_error_gets_context_correction():
    cands = [_candidate("gonderecegim", 0, suggestion="gönderecekler")]
    decisions = [
        LLMSpellingDecision(word="gonderecegim", is_error=True, correction="göndereceğim")
    ]
    out = Analyzer._resolve_spelling(cands, decisions)
    assert len(out) == 1
    assert out[0].suggestion == "göndereceğim"  # Gemini önerisi Hunspell'inkini ezdi


def test_valid_word_is_dropped():
    cands = [_candidate("Acme", 0)]
    decisions = [LLMSpellingDecision(word="Acme", is_error=False, correction="")]
    out = Analyzer._resolve_spelling(cands, decisions)
    assert out == []  # özel ad → elendi


def test_missing_decision_falls_back_to_hunspell():
    cands = [_candidate("yanlız", 0, suggestion="yalnız")]
    out = Analyzer._resolve_spelling(cands, [])  # Gemini karar vermedi
    assert len(out) == 1
    assert out[0].suggestion == "yalnız"  # tespit korundu


def test_error_without_correction_keeps_existing_suggestion():
    cands = [_candidate("herkez", 0, suggestion="herke")]
    decisions = [LLMSpellingDecision(word="herkez", is_error=True, correction="")]
    out = Analyzer._resolve_spelling(cands, decisions)
    assert len(out) == 1
    assert out[0].suggestion == "herke"  # boş düzeltme → mevcut öneri kalır


def test_casefold_variants_each_get_their_own_correction():
    # Regresyon: "Herşey" (cümle başı) ve "herşey" (cümle içi) SADECE büyük/
    # küçük harfle ayrılan iki AYRI candidate. Her biri kendi kararını almalı;
    # "Herşey"in kararı, "herşey" candidate'ının kararını GÖLGELEMEMELİ
    # (bkz. eski tek-geçişli by_word doldurma hatası).
    cands = [
        _candidate("Herşey", 0, suggestion="(öneri yok)"),
        _candidate("herşey", 40, suggestion="(öneri yok)"),
        _candidate("herşey", 90, suggestion="(öneri yok)"),
    ]
    decisions = [
        LLMSpellingDecision(word="Herşey", is_error=True, correction="Her şey"),
        LLMSpellingDecision(word="herşey", is_error=True, correction="her şey"),
    ]
    out = Analyzer._resolve_spelling(cands, decisions)
    assert len(out) == 3
    assert out[0].suggestion == "Her şey"  # cümle başı → büyük harf korunur
    assert out[1].suggestion == "her şey"  # cümle içi → küçük harf, GÖLGELENMEMELİ
    assert out[2].suggestion == "her şey"


def test_user_message_lists_candidates():
    msg = build_user_message("KURALLAR", "metin", ["yanlız", "herkez"])
    assert "ŞÜPHELİ KELİMELER" in msg
    assert "yanlız" in msg and "herkez" in msg


def test_user_message_without_candidates():
    msg = build_user_message("KURALLAR", "metin", [])
    assert "hiçbir kelime işaretlemedi" in msg


# --- Çok geçişli analyze_document (geçiş-farkında sahte model, API yok) --------

_EMPTY = LLMAnalysis(findings=[], spelling=[])


class _FakeRules:
    def get_context(self, text: str) -> str:
        return "KURALLAR"


class _PassFakeStructured:
    """Geçiş-farkında sahte yapı: sistem promptuna göre ilgili analizi döndürür.

    Böylece yerel/ton/tutarlılık geçişleri ayrı ayrı taklit edilebilir.
    """

    def __init__(self, by_pass: dict[str, LLMAnalysis]) -> None:
        self._by_pass = by_pass

    def invoke(self, messages):
        system = messages[0].content
        if "CÜMLE CÜMLE" in system:
            return self._by_pass.get("local", _EMPTY)
        if "TON/ÜSLUP" in system:
            return self._by_pass.get("tone", _EMPTY)
        if "tutarlilik" in system:
            return self._by_pass.get("consistency", _EMPTY)
        return _EMPTY


class _FakeModel:
    def __init__(self, by_pass: dict[str, LLMAnalysis]) -> None:
        self._by_pass = by_pass

    def with_structured_output(self, schema):  # noqa: ARG002
        return _PassFakeStructured(self._by_pass)


def _build_analyzer(by_pass: dict[str, LLMAnalysis]) -> Analyzer:
    return Analyzer(
        chat_model=_FakeModel(by_pass),
        rules_provider=_FakeRules(),
        model_id="test-model",
        cache=None,
        speller=None,
    )


def _llm_finding(excerpt: str, type_: FindingType) -> LLMFinding:
    return LLMFinding(
        type=type_, excerpt=excerpt, explanation="x", suggestion="düzeltme"
    )


def test_analyze_document_rebases_local_offsets_to_source():
    # İki parça: "aaaa" (start 0) ve "XXXX" (start 6). Yerel geçiş her parçada
    # "XXXX" bulgusu döndürür; yalnız ikinci parçada konumlanır ve offset parça
    # başlangıcı (6) kadar kaydırılarak kaynağa taşınır.
    by_pass = {"local": LLMAnalysis(findings=[_llm_finding("XXXX", FindingType.DIL_BILGISI)])}
    analyzer = _build_analyzer(by_pass)
    source = "aaaa\n\nXXXX"

    result = analyzer.analyze_document(source, max_chars=5)

    located = [f for f in result.findings if f.start is not None]
    assert len(located) == 1
    assert (located[0].start, located[0].end) == (6, 10)
    assert source[located[0].start : located[0].end] == "XXXX"
    assert result.text_len == len(source)
    assert result.model_id == "test-model"


def test_analyze_document_consistency_pass_runs_on_whole_text():
    # Tutarlılık geçişi bütün belgede tek kez çalışır; offset global (rebase yok).
    by_pass = {
        "consistency": LLMAnalysis(
            findings=[_llm_finding("XXXX", FindingType.TUTARLILIK)]
        )
    }
    analyzer = _build_analyzer(by_pass)
    source = "aaaa\n\nXXXX"

    result = analyzer.analyze_document(source, max_chars=5)

    tutarlilik = [f for f in result.findings if f.type == FindingType.TUTARLILIK]
    assert len(tutarlilik) == 1
    assert (tutarlilik[0].start, tutarlilik[0].end) == (6, 10)


def test_analyze_document_empty_when_all_passes_empty():
    analyzer = _build_analyzer({})  # tüm geçişler boş döner
    result = analyzer.analyze_document("Kısa tek paragraf.")
    assert result.findings == []
    assert result.text_len == len("Kısa tek paragraf.")
