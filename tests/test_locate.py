from dilanaliz.locate import enrich_with_offsets, find_spans
from dilanaliz.schema import AnalysisResult, Finding, FindingType


def _finding(excerpt: str) -> Finding:
    return Finding(
        type=FindingType.IMLA,
        excerpt=excerpt,
        explanation="x",
        suggestion="y",
    )


def test_exact_match():
    source = "Bu cümlede yanlız yazılmış."
    assert find_spans(source, "yanlız") == [(11, 17)]


def test_whitespace_normalized_match():
    source = "Ben de\ngeldim buraya."
    # excerpt'te tek boşluk var ama kaynakta satır sonu — normalize yakalamalı
    spans = find_spans(source, "Ben de geldim")
    assert spans and source[spans[0][0]:spans[0][1]] == "Ben de\ngeldim"


def test_not_found_returns_empty():
    assert find_spans("merhaba dünya", "bulunmayan") == []


def test_duplicate_excerpts_get_distinct_spans():
    source = "ki ... ki"
    result = AnalysisResult(findings=[_finding("ki"), _finding("ki")])
    enrich_with_offsets(result, source)
    spans = {(f.start, f.end) for f in result.findings}
    assert spans == {(0, 2), (7, 9)}


def test_overlapping_different_excerpts_both_located():
    # imla "herkez" ile ton "herkez görsün." çakışır ama ikisi de konumlanmalı
    source = "Bu raporu yanlız ben hazırladım, herkez görsün."
    result = AnalysisResult(
        findings=[_finding("herkez"), _finding("herkez görsün.")]
    )
    enrich_with_offsets(result, source)
    assert result.findings[0].start == 33
    assert result.findings[1].start == 33
    assert result.findings[1].end == 47


def test_quote_variant_match():
    # Kaynak "akıllı kesme" (’) taşır, LLM alıntısı düz kesme (') döndürür;
    # eşleştirme tırnak biçiminden bağımsız olmalı (yoksa bulgu konumsuz kalır).
    source = "Telsizi “Tarama Modu”na alın; Pil’i çıkarmayın."
    spans = find_spans(source, "Pil'i")
    assert spans and source[spans[0][0]:spans[0][1]] == "Pil’i"
    spans2 = find_spans(source, '"Tarama Modu"na')
    assert spans2 and source[spans2[0][0]:spans2[0][1]] == "“Tarama Modu”na"


def test_unlocatable_excerpt_left_none():
    source = "tertemiz bir cümle"
    result = AnalysisResult(findings=[_finding("olmayan alıntı")])
    enrich_with_offsets(result, source)
    assert result.findings[0].start is None
    assert result.findings[0].end is None
