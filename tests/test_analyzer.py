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
    LLMTermExtraction,
    Observation,
    TermEntry,
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
    def get_context(self, text: str, purpose: str = "all") -> str:
        return "KURALLAR"


class _PassFakeStructured:
    """Geçiş-farkında sahte yapı: sistem promptuna göre ilgili analizi döndürür.

    Böylece yerel/ton/tutarlılık geçişleri ayrı ayrı taklit edilebilir. Terim
    çıkarımı (map) ayrı şemaya (LLMTermExtraction) bağlandığı için önce şemaya
    bakılır: term çağrısı `by_pass["terms"]` (kullanıcı mesajını alan bir
    callable) ile taklit edilir. Tutarlılık reduce çağrısı da sistem promptunda
    "tutarlilik" geçtiği için "consistency" dalına düşer (aynı LLMAnalysis).
    """

    def __init__(self, by_pass: dict, schema=LLMAnalysis) -> None:
        self._by_pass = by_pass
        self._schema = schema

    def invoke(self, messages):
        system = messages[0].content
        user = messages[1].content if len(messages) > 1 else ""
        if self._schema is LLMTermExtraction:
            terms = self._by_pass.get("terms")
            if callable(terms):
                return terms(user)
            return terms or LLMTermExtraction()
        if "CÜMLE CÜMLE" in system:
            return self._by_pass.get("local", _EMPTY)
        if "TON/ÜSLUP" in system:
            return self._by_pass.get("tone", _EMPTY)
        if "tutarlilik" in system:
            cons = self._by_pass.get("consistency", _EMPTY)
            return cons(user) if callable(cons) else cons
        return _EMPTY


class _FakeModel:
    def __init__(self, by_pass: dict) -> None:
        self._by_pass = by_pass

    def with_structured_output(self, schema):
        return _PassFakeStructured(self._by_pass, schema)


def _build_analyzer(
    by_pass: dict, consistency_map_reduce_chars: int = 16000, max_workers: int = 1
) -> Analyzer:
    return Analyzer(
        chat_model=_FakeModel(by_pass),
        rules_provider=_FakeRules(),
        model_id="test-model",
        cache=None,
        speller=None,
        max_workers=max_workers,
        consistency_map_reduce_chars=consistency_map_reduce_chars,
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


def test_consistency_below_threshold_uses_single_call_not_map_reduce():
    # Eşik ALTINDA: mevcut tek-çağrı yolu; terim çıkarımı (map) HİÇ çağrılmamalı.
    def _terms_must_not_be_called(_user):
        raise AssertionError("Eşik altında map (terim çıkarımı) çağrılmamalı")

    by_pass = {
        "terms": _terms_must_not_be_called,
        "consistency": LLMAnalysis(findings=[_llm_finding("XXXX", FindingType.TUTARLILIK)]),
    }
    analyzer = _build_analyzer(by_pass, consistency_map_reduce_chars=16000)
    source = "aaaa\n\nXXXX"  # kısa → eşik altı

    result = analyzer.analyze_document(source, max_chars=5)

    tutarlilik = [f for f in result.findings if f.type == FindingType.TUTARLILIK]
    assert len(tutarlilik) == 1
    assert source[tutarlilik[0].start : tutarlilik[0].end] == "XXXX"


def _cross_chunk_terms(user: str) -> LLMTermExtraction:
    """Map sahtesi: parçada hangi terim geçiyorsa onu çıkarır (aynı kavram)."""
    terms = []
    if "PTT" in user:
        terms.append(TermEntry(surface="PTT", concept="posta idaresi"))
    if "BK" in user:
        terms.append(TermEntry(surface="BK", concept="posta idaresi"))
    return LLMTermExtraction(terms=terms)


def test_consistency_above_threshold_uses_map_reduce_cross_chunk():
    # Eşik ÜSTÜnde map-reduce: "PTT" ilk parçada, "BK" ayrı parçada. Map her
    # parçadan terimi çıkarır; reduce belge-geneli indeksi görüp çakışmayı bulur.
    captured: dict[str, str] = {}

    def _reduce(user: str) -> LLMAnalysis:
        captured["index"] = user
        # Reduce, indeksteki sapan biçimi (BK) baskın biçime (PTT) önerir.
        return LLMAnalysis(findings=[
            LLMFinding(
                type=FindingType.TUTARLILIK,
                excerpt="BK",
                explanation="Aynı kurum iki farklı kısaltmayla yazılmış.",
                suggestion="PTT",
            )
        ])

    by_pass = {"terms": _cross_chunk_terms, "consistency": _reduce}
    analyzer = _build_analyzer(by_pass, consistency_map_reduce_chars=20)
    source = "Gonderi PTT ile yollanir.\n\nAncak BK subesi kapalidir."

    result = analyzer.analyze_document(source, max_chars=30)

    # Reduce ham metni DEĞİL, aday kümeleri gördü (PTT ve BK aynı kavram → kümede).
    assert "PTT" in captured["index"] and "BK" in captured["index"]
    assert "Küme" in captured["index"]
    # Çakışma tek tutarlilik bulgusuna indi ve "BK" kaynakta konumlandı.
    tutarlilik = [f for f in result.findings if f.type == FindingType.TUTARLILIK]
    assert len(tutarlilik) == 1
    assert source[tutarlilik[0].start : tutarlilik[0].end] == "BK"
    assert tutarlilik[0].suggestion == "PTT"


def test_consistency_map_reduce_deterministic_across_workers():
    # Map paralel çalışsa da çıktı işlenme sırasından bağımsız (indeks sıralı).
    def _reduce(user: str) -> LLMAnalysis:
        return LLMAnalysis(findings=[
            LLMFinding(type=FindingType.TUTARLILIK, excerpt="BK",
                       explanation="x", suggestion="PTT")
        ])

    by_pass = {"terms": _cross_chunk_terms, "consistency": _reduce}
    source = "Gonderi PTT ile yollanir.\n\nAncak BK subesi kapalidir."

    seq = _build_analyzer(by_pass, consistency_map_reduce_chars=20, max_workers=1)
    par = _build_analyzer(by_pass, consistency_map_reduce_chars=20, max_workers=4)
    r_seq = seq.analyze_document(source, max_chars=30)
    r_par = par.analyze_document(source, max_chars=30)

    key = lambda r: [(f.type, f.start, f.end, f.excerpt, f.suggestion) for f in r.findings]
    assert key(r_seq) == key(r_par)


def test_term_index_drops_numeric_noise_and_single_form_terms():
    from dilanaliz.analyzer import _build_term_index
    # Sayısal/değer yüzeyler elenir; tek biçimde geçen terim adaya girmez.
    entries = [
        TermEntry(surface="0", concept="sayı"),
        TermEntry(surface="1,5 metre", concept="uzunluk"),
        TermEntry(surface="%90", concept="oran"),
        TermEntry(surface="PTT", concept="posta idaresi"),  # tek biçim → aday değil
    ]
    assert _build_term_index(entries) == ""


def test_term_index_clusters_quote_variants():
    from dilanaliz.analyzer import _build_term_index
    # Tırnak farkı (casefold sonrası HÂLÂ farklı) → gerçek varyant, aday küme.
    entries = [
        TermEntry(surface="'Programlama Modu'", concept="mod"),
        TermEntry(surface="Programlama Modu", concept="mod"),
    ]
    idx = _build_term_index(entries)
    assert "Küme" in idx
    assert "'Programlama Modu'" in idx and "Programlama Modu" in idx


def test_term_index_drops_case_only_clusters():
    from dilanaliz.analyzer import _build_term_index
    # Salt büyük/küçük harf farkı = başlık/düzyazı doğal farkı, tutarsızlık DEĞİL.
    # "standart pil"↔"Standart Pil", "RX"↔"Rx", "Khz"↔"kHz" → hiçbiri bulgu olmaz.
    entries = [
        TermEntry(surface="standart pil", concept="pil"),
        TermEntry(surface="Standart Pil", concept="pil"),
        TermEntry(surface="RX", concept="alım"),
        TermEntry(surface="Rx", concept="alım"),
        TermEntry(surface="Khz", concept="birim"),
        TermEntry(surface="kHz", concept="birim"),
    ]
    assert _build_term_index(entries) == ""


def test_term_index_drops_generic_concept_buckets():
    from dilanaliz.analyzer import _build_term_index
    # Aynı jenerik kavrama bağlı ÇOK (>MAX) farklı yüzey = jenerik kova, atılır.
    entries = [
        TermEntry(surface=f"Başlık{i}", concept="bölüm başlığı") for i in range(6)
    ]
    assert _build_term_index(entries) == ""


def test_term_index_keeps_small_synonym_concept_cluster():
    from dilanaliz.analyzer import _build_term_index
    # Aynı kavrama bağlı 2 FARKLI yüzey (eşanlam) → küçük küme, aday.
    entries = [
        TermEntry(surface="PTT", concept="posta idaresi"),
        TermEntry(surface="BK", concept="posta idaresi"),
    ]
    idx = _build_term_index(entries)
    assert "PTT" in idx and "BK" in idx and "Küme" in idx


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


def test_toc_span_findings_are_dropped_but_consistency_kept():
    # İçindekiler satırına düşen imla/dil bilgisi/ton bulguları elenir (tablo
    # muamelesi); tutarlılık bulgusu KORUNUR. TOC-only parça LLM'e gitmese de
    # burada tek parça senaryosuyla süzme katmanı doğrudan test ediliyor.
    source = "Gerçek bir cümle var.\n\nGüvenlik Bilgileri\t6"
    spans = _spans_for(source, {"Güvenlik Bilgileri\t6": "icindekiler"})
    by_pass = {
        "local": LLMAnalysis(findings=[
            _llm_finding("Bilgileri", FindingType.IMLA),      # TOC'ta → elenir
            _llm_finding("cümle", FindingType.DIL_BILGISI),   # düzyazıda → kalır
        ]),
        "consistency": LLMAnalysis(findings=[
            _llm_finding("Güvenlik Bilgileri", FindingType.TUTARLILIK),  # korunur
        ]),
    }
    analyzer = _build_analyzer(by_pass)

    result = analyzer.analyze_document(source, spans=spans)

    assert [f.type for f in result.findings if f.type == FindingType.IMLA] == []
    assert len([f for f in result.findings if f.type == FindingType.DIL_BILGISI]) == 1
    assert len([f for f in result.findings if f.type == FindingType.TUTARLILIK]) == 1


def test_toc_only_chunk_skips_llm_passes():
    # Parça tamamen İçindekiler satırlarından oluşuyorsa yerel/ton geçişine
    # hiç gönderilmez (tablo-only parça ile aynı API tasarrufu yolu).
    source = "Güvenlik\t5\n\nMikrofon\t9"
    spans = _spans_for(source, {
        "Güvenlik\t5": "icindekiler",
        "Mikrofon\t9": "icindekiler",
    })
    by_pass = {"local": LLMAnalysis(findings=[
        _llm_finding("Güvenlik", FindingType.IMLA)
    ])}
    analyzer = _build_analyzer(by_pass)

    result = analyzer.analyze_document(source, spans=spans)

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


# --- Gözlem kanalı (observations) — findings'ten ayrı, düşük-güvenli -----------


def test_local_pass_observations_surface_in_result_not_findings():
    # Yerel geçişten gelen gözlem ayrı kanalda görünür; findings'e KARIŞMAZ.
    obs = Observation(excerpt="şüpheli ifade", note="kurala bağlanamadı")
    by_pass = {"local": LLMAnalysis(findings=[], observations=[obs])}
    analyzer = _build_analyzer(by_pass)

    result = analyzer.analyze("Bir cümle burada.")

    assert result.findings == []
    assert len(result.observations) == 1
    assert result.observations[0].excerpt == "şüpheli ifade"
    assert result.observations[0].note == "kurala bağlanamadı"


def test_observations_survive_without_source_offset():
    # Gözlem findings hattından (locate/drop_unlocated) MUAF: excerpt kaynakta
    # birebir geçmese bile ELENMEZ (bir bulgu olsaydı konumlanamadığı için atılırdı).
    obs = Observation(excerpt="kaynakta-olmayan-metin", note="şüphe")
    by_pass = {"local": LLMAnalysis(findings=[], observations=[obs])}
    analyzer = _build_analyzer(by_pass)

    result = analyzer.analyze("Tamamen farklı bir metin.")

    assert [o.excerpt for o in result.observations] == ["kaynakta-olmayan-metin"]


def test_tone_and_consistency_observations_are_ignored():
    # Gözlem YALNIZ yerel geçişten toplanır; ton/tutarlılık geçişi (kazara)
    # gözlem döndürse bile sonuçta görünmez.
    by_pass = {
        "tone": LLMAnalysis(observations=[Observation(excerpt="ton-g", note="x")]),
        "consistency": LLMAnalysis(observations=[Observation(excerpt="tut-g", note="x")]),
    }
    analyzer = _build_analyzer(by_pass)

    result = analyzer.analyze("Bir cümle.")

    assert result.observations == []


def test_observations_deduped_and_sorted_deterministically():
    # analyze_document: aynı gözlem birden çok parçadan gelebilir → tekilleşir;
    # sıra (excerpt, note) anahtarıyla deterministik (paralel toplamadan bağımsız).
    obs_b = Observation(excerpt="b-şüphe", note="n")
    obs_a = Observation(excerpt="a-şüphe", note="n")
    by_pass = {"local": LLMAnalysis(observations=[obs_b, obs_a, obs_b])}
    analyzer = _build_analyzer(by_pass)
    source = "aaaa\n\nbbbb"  # iki parça → yerel geçiş iki kez → gözlemler çoğalır

    result = analyzer.analyze_document(source, max_chars=5)

    assert [o.excerpt for o in result.observations] == ["a-şüphe", "b-şüphe"]
