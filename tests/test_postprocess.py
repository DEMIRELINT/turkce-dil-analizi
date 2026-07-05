from dilanaliz.postprocess import (
    drop_context_satisfied_findings,
    drop_cross_pass_duplicates,
    drop_noop_findings,
    drop_unlocated_findings,
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


def _span_sug(
    excerpt: str, suggestion: str, start: int, type_: FindingType = FindingType.IMLA
) -> Finding:
    """`_span` gibi ama gerçek bir `suggestion` verir (atomik-düzeltme testleri için)."""
    return Finding(
        type=type_, excerpt=excerpt, explanation="x", suggestion=suggestion,
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


def test_drop_unlocated_removes_none_offset_findings():
    # Halüsinasyon savunması: kaynakta bulunamayan (start/end=None) bulgular
    # _finalize öncesi burada elenir (bkz. merge_findings'in bilerek koruduğu
    # "floating" bulgular — nihai raporda kalmamalı).
    located = _span("yanlız", 0)
    floating = _f("olmayan alıntı", "düzeltme")  # start/end None
    result = drop_unlocated_findings([located, floating])
    assert result == [located]


def test_drop_context_satisfied_removes_already_present_suffix():
    # "sunuyoruz." zaten kaynakta — model alıntıyı noktadan önce kesip
    # "eksik nokta" öneriyor; bu sahte bir düzeltme, elenmeli.
    source = "ilgili belgeyi ekte bilginize sunuyoruz. Saygılarımızla."
    start = source.index("sunuyoruz")
    finding = Finding(
        type=FindingType.IMLA, excerpt="sunuyoruz", explanation="x",
        suggestion="sunuyoruz.", start=start, end=start + len("sunuyoruz"),
    )
    assert drop_context_satisfied_findings([finding], source) == []


def test_drop_context_satisfied_keeps_real_correction():
    # Öneri, alıntı + kaynakta HEMEN ARDINDAN gelenle aynı biçimde eşleşmiyorsa
    # (gerçek bir eksiklikse) korunmalı — burada virgül kaynakta YOK.
    source = "Merhaba dünya, hoş geldiniz."
    start = source.index("Merhaba")
    finding = Finding(
        type=FindingType.IMLA, excerpt="Merhaba", explanation="x",
        suggestion="Merhaba,", start=start, end=start + len("Merhaba"),
    )
    assert drop_context_satisfied_findings([finding], source) == [finding]


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


# --- Çapraz-geçiş tip-kopyası tekilleştirme ----------------------------------

def test_cross_pass_duplicate_keeps_higher_priority_type():
    # Aynı konum + aynı alıntı, iki geçişten iki tiple gelirse (dil_bilgisi +
    # ton) daha somut eksen (dil_bilgisi) kalır, ton kopyası elenir.
    a = _span("zamanı aşınır", 100, FindingType.DIL_BILGISI)
    b = _span("zamanı aşınır", 100, FindingType.TON)
    out = drop_cross_pass_duplicates([a, b])
    assert out == [a]
    # Girdi sırası değişse de sonuç aynı (determinizm).
    assert drop_cross_pass_duplicates([b, a]) == [a]


def test_cross_pass_different_excerpts_are_kept():
    # Konum örtüşse bile alıntı FARKLIYSA iki bulgu iki ayrı iddiadır — ikisi
    # de korunur (farklı-alıntılı çelişkiler bilinen sınır olarak kalır).
    a = _span("hands-free (VOX) işleviyle çalıştırabilir", 200, FindingType.DIL_BILGISI)
    b = _span("hands-free", 200, FindingType.TON)
    out = drop_cross_pass_duplicates([a, b])
    assert len(out) == 2


def test_cross_pass_consistency_type_is_untouched():
    # tutarlilik tipi ne eler ne elenir: belge-geneli iddia yerel bulgunun
    # kopyası değildir.
    a = _span("Khz", 300, FindingType.IMLA)
    b = _span("Khz", 300, FindingType.TUTARLILIK)
    out = drop_cross_pass_duplicates([a, b])
    assert len(out) == 2


def test_cross_pass_same_type_untouched():
    # Aynı tip birebir kopyalar bu fonksiyonun işi değil (_dedup halleder).
    a = _span("hata", 10, FindingType.IMLA)
    b = _span("hata", 10, FindingType.IMLA)
    assert len(drop_cross_pass_duplicates([a, b])) == 2


def test_cross_pass_same_atomic_correction_different_excerpt_collapses():
    # dil_bilgisi TÜM CÜMLEyi alıntılayıp "sundular"→"sunuldu" öneriyor; ton
    # yalnız "sundular" kelimesini alıntılayıp AYNI düzeltmeyi öneriyor —
    # alıntılar farklı ama atomik düzeltme (tek kelime farkı) aynı, teke iner.
    a = _span_sug(
        "Rapor hazırlandı ve yönetime sundular.",
        "Rapor hazırlandı ve yönetime sunuldu.",
        100, FindingType.DIL_BILGISI,
    )
    b = _span_sug("sundular", "sunuldu", 130, FindingType.TON)
    out = drop_cross_pass_duplicates([a, b])
    assert out == [a]
    assert drop_cross_pass_duplicates([b, a]) == [a]


def test_cross_pass_multi_word_rewrite_without_atomic_match_keeps_both():
    # Öneri serbest/çok-kelimeli yeniden yazımsa (tek kelime farkı çıkarılamaz)
    # atomik-düzeltme yolu devre dışı kalır; yalnız tam-alıntı eşleşmesi
    # geçerlidir — burada o da yok, ikisi de farklı iddia olarak korunur.
    a = _span_sug(
        "Verdiğiniz bilgi yannış çıktı",
        "Verdiğiniz bilgi hatalı çıktı",
        200, FindingType.IMLA,
    )
    b = _span_sug(
        "Verdiğiniz bilgi yannış çıktı, tekrar kontrol edeceğiz.",
        "Verdiğiniz bilginin hatalı olduğunu tespit ettik.",
        200, FindingType.TON,
    )
    out = drop_cross_pass_duplicates([a, b])
    assert len(out) == 2
