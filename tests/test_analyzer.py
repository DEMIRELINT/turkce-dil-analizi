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


def test_user_message_lists_candidates():
    msg = build_user_message("KURALLAR", "metin", ["yanlız", "herkez"])
    assert "ŞÜPHELİ KELİMELER" in msg
    assert "yanlız" in msg and "herkez" in msg


def test_user_message_without_candidates():
    msg = build_user_message("KURALLAR", "metin", [])
    assert "hiçbir kelime işaretlemedi" in msg


# --- analyze_document: parçalama + offset rebasing (sahte model, API yok) ------


class _FakeRules:
    def get_context(self, text: str) -> str:
        return "KURALLAR"


class _FakeStructured:
    """`with_structured_output` sonrası nesne: her çağrıda sabit analiz döner."""

    def __init__(self, analysis: LLMAnalysis) -> None:
        self._analysis = analysis

    def invoke(self, messages):  # noqa: ARG002 — mesaj içeriği önemsiz
        return self._analysis


class _FakeModel:
    def __init__(self, analysis: LLMAnalysis) -> None:
        self._analysis = analysis

    def with_structured_output(self, schema):  # noqa: ARG002
        return _FakeStructured(self._analysis)


def _build_analyzer(analysis: LLMAnalysis) -> Analyzer:
    return Analyzer(
        chat_model=_FakeModel(analysis),
        rules_provider=_FakeRules(),
        model_id="test-model",
        cache=None,
        speller=None,
    )


def test_analyze_document_rebases_offsets_to_source():
    # İki parça olacak: "aaaa" (start 0) ve "XXXX" (start 6). Sahte model her
    # parçada "XXXX" bulgusu döndürür; yalnız ikinci parçada konumlanır ve offset
    # parça başlangıcı (6) kadar kaydırılarak kaynağa taşınır.
    analysis = LLMAnalysis(
        findings=[
            LLMFinding(
                type=FindingType.DIL_BILGISI,
                excerpt="XXXX",
                explanation="x",
                suggestion="düzeltme",
            )
        ],
        spelling=[],
    )
    analyzer = _build_analyzer(analysis)
    source = "aaaa\n\nXXXX"

    result = analyzer.analyze_document(source, max_chars=5)

    located = [f for f in result.findings if f.start is not None]
    assert len(located) == 1
    assert (located[0].start, located[0].end) == (6, 10)
    assert source[located[0].start : located[0].end] == "XXXX"
    assert result.text_len == len(source)
    assert result.model_id == "test-model"


def test_analyze_document_single_chunk_matches_analyze():
    analysis = LLMAnalysis(findings=[], spelling=[])
    analyzer = _build_analyzer(analysis)
    result = analyzer.analyze_document("Kısa tek paragraf.")
    assert result.findings == []
    assert result.text_len == len("Kısa tek paragraf.")
