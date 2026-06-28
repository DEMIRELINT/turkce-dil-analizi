"""Analyzer'ın aday→düzeltme birleştirme mantığı (API gerektirmez)."""

from dilanaliz.analyzer import Analyzer
from dilanaliz.prompt import build_user_message
from dilanaliz.schema import Finding, FindingType, LLMSpellingDecision


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
