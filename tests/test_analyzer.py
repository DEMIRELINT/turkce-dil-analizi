"""Analyzer'ın aday→düzeltme birleştirme mantığı (API gerektirmez)."""

import pytest

from dilanaliz.analyzer import Analyzer, LLMCallError
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


def test_missing_decision_keeps_detection_with_placeholder():
    # Hunspell artık kendi önerisini üretmez; LLM karar vermezse tespit
    # "öneri yok" yer tutucusuyla korunur (uydurma öneri gösterilmez).
    from dilanaliz.spell import NO_SUGGESTION

    cands = [_candidate("yanlız", 0, suggestion=NO_SUGGESTION)]
    out = Analyzer._resolve_spelling(cands, [])  # Gemini karar vermedi
    assert len(out) == 1
    assert out[0].suggestion == NO_SUGGESTION  # tespit korundu, öneri uydurulmadı


def test_error_without_correction_keeps_existing_suggestion():
    from dilanaliz.spell import NO_SUGGESTION

    cands = [_candidate("herkez", 0, suggestion=NO_SUGGESTION)]
    decisions = [LLMSpellingDecision(word="herkez", is_error=True, correction="")]
    out = Analyzer._resolve_spelling(cands, decisions)
    assert len(out) == 1
    assert out[0].suggestion == NO_SUGGESTION  # boş düzeltme → yer tutucu kalır


def test_correction_is_dressed_in_excerpt_case():
    # LLM düzeltmesi küçük harfle gelse de alıntı TAMAMI BÜYÜK ise öneri de
    # Türkçe kurala göre büyütülür (İ/I doğru): "SEÇENEKLERI" → "SEÇENEKLERİ".
    cands = [_candidate("SEÇENEKLERI", 0)]
    decisions = [
        LLMSpellingDecision(word="SEÇENEKLERI", is_error=True, correction="seçenekleri")
    ]
    out = Analyzer._resolve_spelling(cands, decisions)
    assert out[0].suggestion == "SEÇENEKLERİ"  # noktalı büyük İ — "SEÇENEKLERI" değil


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


class _BrokenModel:
    """`invoke` her çağrıda patlayan sahte model — hata sarmalamayı test eder."""

    def with_structured_output(self, schema):  # noqa: ARG002
        return self

    def invoke(self, messages):  # noqa: ARG002
        raise TimeoutError("bağlantı zaman aşımına uğradı")


def test_invoke_cached_wraps_transient_errors_in_llm_call_error():
    analyzer = Analyzer(
        chat_model=_BrokenModel(),
        rules_provider=_FakeRules(),
        model_id="test-model",
        cache=None,
        speller=None,
    )
    with pytest.raises(LLMCallError) as exc_info:
        analyzer._invoke_cached("SYSTEM", "USER")
    assert "bağlantı zaman aşımına uğradı" in str(exc_info.value)
    assert "GOOGLE_GENAI_TRANSPORT" in str(exc_info.value)


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


# --- Etiketli blok (span) farkında süzme ---------------------------------------

from dilanaliz.extract import BlockSpan  # noqa: E402


def _spans_for(source: str, kinds: dict[str, str]) -> list[BlockSpan]:
    """Bloğu metnine göre türleyen yardımcı: kinds = {blok metni: tür}."""
    spans: list[BlockSpan] = []
    offset = 0
    for block in source.split("\n\n"):
        spans.append(BlockSpan(offset, offset + len(block), kinds.get(block, "paragraf")))
        offset += len(block) + 2
    return spans


def test_table_span_findings_are_dropped_and_summarized():
    # Tablo hücrelerindeki imla bulguları elenir; 3+ ondalık nokta TEK
    # tutarlılık özetine iner. Düzyazı bulgusu korunur.
    source = "Gerçek bir cümle var.\n\n446.00625\n\n446.01875\n\n446.03125"
    spans = _spans_for(source, {
        "446.00625": "tablo_hucresi",
        "446.01875": "tablo_hucresi",
        "446.03125": "tablo_hucresi",
    })
    by_pass = {"local": LLMAnalysis(findings=[
        _llm_finding("446.00625", FindingType.IMLA),   # tabloda → elenir
        _llm_finding("cümle", FindingType.DIL_BILGISI),  # düzyazıda → kalır
    ])}
    analyzer = _build_analyzer(by_pass)

    result = analyzer.analyze_document(source, spans=spans)

    imla = [f for f in result.findings if f.type == FindingType.IMLA]
    assert imla == []  # tablo hücresindeki tek tek imla bulgusu yok
    summary = [f for f in result.findings if f.type == FindingType.TUTARLILIK]
    assert len(summary) == 1
    assert "3 yerde" in summary[0].explanation
    assert summary[0].suggestion == "446,00625"
    kept = [f for f in result.findings if f.type == FindingType.DIL_BILGISI]
    assert len(kept) == 1  # düzyazı bulgusu süzmeden etkilenmedi


def test_fewer_than_three_decimals_produce_no_summary():
    source = "Cümle.\n\n12.5"
    spans = _spans_for(source, {"12.5": "tablo_hucresi"})
    analyzer = _build_analyzer({})
    result = analyzer.analyze_document(source, spans=spans)
    assert result.findings == []  # 1 ondalık < 3 → özet üretilmez


def test_heading_span_drops_only_structural_rules():
    # Başlıkta GRAMER-TEKRAR/IMLA-NOKTALAMA elenir; başka bulgular kalır.
    source = "BAŞLIK SATIRI\n\nNormal cümle burada."
    spans = _spans_for(source, {"BAŞLIK SATIRI": "baslik"})
    tekrar = LLMFinding(
        type=FindingType.DIL_BILGISI, excerpt="BAŞLIK SATIRI",
        explanation="x", suggestion="BAŞLIK", rule_id="GRAMER-TEKRAR",
    )
    gercek = LLMFinding(
        type=FindingType.DIL_BILGISI, excerpt="Normal cümle",
        explanation="x", suggestion="düzeltme", rule_id="GRAMER-ANLATIM",
    )
    analyzer = _build_analyzer({"local": LLMAnalysis(findings=[tekrar, gercek])})

    result = analyzer.analyze_document(source, spans=spans)

    rule_ids = [f.rule_id for f in result.findings]
    assert "GRAMER-TEKRAR" not in rule_ids  # başlık tekrarı elendi
    assert "GRAMER-ANLATIM" in rule_ids     # gerçek bulgu korundu


def test_table_only_chunk_skips_llm_passes():
    # Parça tamamen tablo verisiyse yerel/ton geçişine hiç gönderilmez:
    # sahte model bulgu döndürse bile sonuçta görünmemeli.
    source = "446.00625\n\n446.01875"
    spans = _spans_for(source, {
        "446.00625": "tablo_hucresi",
        "446.01875": "tablo_hucresi",
    })
    by_pass = {"local": LLMAnalysis(findings=[
        _llm_finding("446.00625", FindingType.IMLA)
    ])}
    analyzer = _build_analyzer(by_pass)

    result = analyzer.analyze_document(source, spans=spans)

    # 2 ondalık < 3 → özet de yok; sonuç tamamen boş.
    assert result.findings == []


def test_no_spans_means_no_filtering():
    # spans verilmezse (düz metin girdisi) eski davranış: hiçbir süzme yok.
    source = "Cümle.\n\n446.00625"
    by_pass = {"local": LLMAnalysis(findings=[
        _llm_finding("446.00625", FindingType.IMLA)
    ])}
    analyzer = _build_analyzer(by_pass)
    result = analyzer.analyze_document(source)
    assert [f.excerpt for f in result.findings] == ["446.00625"]
