from dilanaliz.postprocess import (
    drop_noop_findings,
    is_noop_suggestion,
    merge_findings,
    validate_suggestions,
)
from dilanaliz.schema import AnalysisResult, Finding, FindingType


def _f(excerpt: str, suggestion: str) -> Finding:
    return Finding(
        type=FindingType.IMLA, excerpt=excerpt, explanation="x", suggestion=suggestion
    )


def _span(excerpt: str, start: int, type_: FindingType = FindingType.IMLA) -> Finding:
    return Finding(
        type=type_, excerpt=excerpt, explanation="x", suggestion="y",
        start=start, end=start + len(excerpt),
    )


def test_identical_is_noop():
    assert is_noop_suggestion("Ben de", "Ben de") is True


def test_whitespace_only_diff_is_noop():
    assert is_noop_suggestion("Ben  de", " Ben de ") is True


def test_punctuation_diff_is_real_correction():
    # "?" eklenmesi gerçek bir düzeltmedir, elenmemeli
    assert is_noop_suggestion("yalnız mı", "yalnız mı?") is False


def test_real_correction_kept():
    assert is_noop_suggestion("yanlız", "yalnız") is False


def test_curly_vs_straight_quote_is_noop():
    # Word "akıllı kesme" (’) üretir, LLM düz kesme (') döndürür; ikisi aynı
    # işlevi görür — hiçbir şey değiştirmeyen öneri noop sayılıp elenmelidir.
    assert is_noop_suggestion("ALKALINE’den", "ALKALINE'den") is True
    assert is_noop_suggestion("“Kanal” ayarı", '"Kanal" ayarı') is True


def test_quote_normalization_keeps_real_corrections():
    # Tırnak normalize edilse de gerçek fark (kesmenin KALDIRILMASI) korunmalı.
    assert is_noop_suggestion("Pil’i", "Pili") is False


def test_nfc_nfd_diff_is_noop():
    # "resmî" iki farklı Unicode biçiminde gelebilir: NFC (tek kod noktası "î")
    # ve NFD ("i" + bileşik inceltme işareti). Görsel olarak aynıdır ama
    # normalize edilmeden karşılaştırılırsa eşit sayılmaz — bu yüzden LLM
    # alıntı/öneriyi farklı biçimde üretirse gerçek bir no-op kaçabilir.
    import unicodedata

    nfc = unicodedata.normalize("NFC", "resmî")
    nfd = unicodedata.normalize("NFD", "resmî")
    assert nfc != nfd  # ön koşul: gerçekten farklı bayt dizileri
    assert is_noop_suggestion(nfc, nfd) is True


def test_drop_filters_only_noops():
    result = AnalysisResult(
        findings=[
            _f("Ben de", "Ben de"),       # no-op → atılır
            _f("yanlız", "yalnız"),       # gerçek → kalır
            _f("yarınki", "yarınki"),     # no-op → atılır
            _f("herşey", "her şey"),      # gerçek → kalır
        ]
    )
    drop_noop_findings(result)
    excerpts = [f.excerpt for f in result.findings]
    assert excerpts == ["yanlız", "herşey"]


def test_merge_keeps_all_deterministic_and_nonoverlapping_llm():
    det = [_span("yanlız", 0)]
    llm = [_span("geldiler", 20, FindingType.DIL_BILGISI)]
    merged = merge_findings(det, llm)
    assert [f.excerpt for f in merged] == ["yanlız", "geldiler"]


def test_merge_drops_overlapping_llm_prefers_deterministic():
    det = [_span("yanlız", 10)]  # 10..16
    llm = [_span("yanlız ben", 10, FindingType.IMLA)]  # 10..20 çakışır
    merged = merge_findings(det, llm)
    assert len(merged) == 1
    assert merged[0].rule_id == det[0].rule_id  # deterministik korunur


def test_merge_keeps_unlocated_llm_findings():
    det = [_span("yanlız", 0)]
    floating = _f("bir şey", "başka şey")  # offset yok
    merged = merge_findings(det, [floating])
    assert floating in merged


def test_validate_drops_corrupt_suggestion():
    # "birçok" → "birchoq": öneride alıntıda olmayan q var → bozuk, elenir.
    result = AnalysisResult(
        findings=[
            _f("bir çok", "birchoq"),     # bozuk → atılır
            _f("yanlız", "yalnız"),       # temiz → kalır
        ]
    )
    validate_suggestions(result)
    assert [f.excerpt for f in result.findings] == ["yanlız"]


def test_validate_keeps_non_turkish_letter_when_in_excerpt():
    # Marka adı: q/w/x alıntıda da varsa öneri bozuk sayılmaz, korunur.
    result = AnalysisResult(findings=[_f("Linux'da", "Linux'ta")])
    validate_suggestions(result)
    assert len(result.findings) == 1
