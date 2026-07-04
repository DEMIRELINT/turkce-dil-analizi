"""Paralel vs sıralı analiz: ÇIKTI BİREBİR AYNI olmalı; paralel daha HIZLI olmalı.

Bu testin amacı planın çekirdek sözleşmesini güvenceye almak: parçaları
eşzamanlı işlemek bulgu sayısını/sırasını/içeriğini DEĞİŞTİRMEZ — yalnız süreyi
kısaltır. API gerektirmez: geçiş-farkında, küçük yapay gecikmeli sahte model.
"""

from __future__ import annotations

import time

from dilanaliz.analyzer import Analyzer
from dilanaliz.schema import FindingType, LLMAnalysis, LLMFinding

# Her sahte LLM çağrısına eklenen yapay gecikme: paralelliğin etkisini ölçülebilir
# kılar (gerçek ağ çağrısını taklit eder). time.sleep GIL'i bıraktığından
# iş parçacıkları gerçekten örtüşür.
_CALL_DELAY = 0.02


def _llm_finding(excerpt: str, type_: FindingType) -> LLMFinding:
    return LLMFinding(type=type_, excerpt=excerpt, explanation="x", suggestion="düzeltme")


class _FakeRules:
    def get_context(self, text: str) -> str:
        return "KURALLAR"


class _SlowPassFakeStructured:
    """Sistem promptuna göre ilgili geçişin bulgusunu döndürür; her çağrıda bekler."""

    def invoke(self, messages):
        time.sleep(_CALL_DELAY)
        system = messages[0].content
        if "CÜMLE CÜMLE" in system:  # yerel geçiş
            return LLMAnalysis(findings=[_llm_finding("XX", FindingType.DIL_BILGISI)])
        if "TON/ÜSLUP" in system:  # ton geçişi
            return LLMAnalysis(findings=[_llm_finding("XX", FindingType.TON)])
        if "tutarlilik" in system:  # belge-geneli tutarlılık
            return LLMAnalysis(findings=[_llm_finding("delta", FindingType.TUTARLILIK)])
        return LLMAnalysis(findings=[], spelling=[])


class _SlowFakeModel:
    def with_structured_output(self, schema):  # noqa: ARG002
        return _SlowPassFakeStructured()


def _analyzer(max_workers: int) -> Analyzer:
    return Analyzer(
        chat_model=_SlowFakeModel(),
        rules_provider=_FakeRules(),
        model_id="test-model",
        cache=None,
        speller=None,
        max_workers=max_workers,
    )


# Dört paragraf; her birinde "XX" (yerel+ton burada konumlanır) ve sonda "delta"
# (tutarlılık geçişi global konumlar). Küçük bütçe → dört ayrı parça.
_SOURCE = "XX alfa\n\nXX beta\n\nXX gama\n\nXX delta"
_MAX_CHARS = 8


def _run(max_workers: int):
    analyzer = _analyzer(max_workers)
    t0 = time.perf_counter()
    result = analyzer.analyze_document(_SOURCE, max_chars=_MAX_CHARS)
    return result, time.perf_counter() - t0


def test_parallel_output_is_identical_to_sequential():
    seq, _ = _run(max_workers=1)
    par, _ = _run(max_workers=4)
    # Birebir aynı: bulgular, sıra, offsetler, üstveri.
    assert seq.model_dump() == par.model_dump()
    # Anlamlı bir çıktı ürettiğimizden emin ol (boş eşitlik tuzağına düşme):
    # sahte model her parçada AYNI "XX" alıntısını hem dil_bilgisi hem ton
    # tipiyle üretir — çapraz-geçiş tip-kopyası tekilleştirmesi ton kopyasını
    # eler (imla > dil_bilgisi > ton). Kalan: 4 parça × 1 dil_bilgisi + 1
    # tutarlılık = 5 bulgu; ton kopyası kalmamalı.
    assert len(seq.findings) == 5
    assert not [f for f in seq.findings if f.type == FindingType.TON]


def test_parallel_is_faster_than_sequential():
    _, seq_time = _run(max_workers=1)
    _, par_time = _run(max_workers=4)
    # Gevşek sınır (CI flakiness'ine karşı): paralel, sıralının %80'inden kısa.
    assert par_time < seq_time * 0.8, f"paralel={par_time:.3f}s sıralı={seq_time:.3f}s"
