"""Bulgu son-işleme (deterministik temizlik).

LLM bazen "hata var" deyip `suggestion`'ı `excerpt` ile birebir aynı veriyor
(örn. "Ben de" → "Ben de"). Bu, değiştirilecek bir şey olmadığı anlamına gelir:
gerçek bir düzeltme değil, yanlış pozitiftir. Bu tür bulguları deterministik
olarak eleriz. Bu, özellikle de/da ve ki üzerindeki aşırı tetiklenmeyi azaltır.

Normalleştirme HAFİF tutulur (baş/son boşluk + iç boşluk daraltma); noktalama
KORUNUR, çünkü "yalnız mı" → "yalnız mı?" gerçek bir düzeltmedir.
"""

from __future__ import annotations

from .schema import AnalysisResult


def _norm(s: str) -> str:
    return " ".join(s.split())


def is_noop_suggestion(excerpt: str, suggestion: str) -> bool:
    """Öneri, alıntıyla anlamlı bir fark taşımıyorsa True."""
    return _norm(excerpt) == _norm(suggestion)


def drop_noop_findings(result: AnalysisResult) -> AnalysisResult:
    """Önerisi alıntıyla aynı olan bulguları çıkarır (yerinde)."""
    result.findings = [
        f for f in result.findings if not is_noop_suggestion(f.excerpt, f.suggestion)
    ]
    return result


def _spans_overlap(a: Finding, b: Finding) -> bool:
    if None in (a.start, a.end, b.start, b.end):
        return False
    return a.start < b.end and b.start < a.end


def merge_findings(
    deterministic: list[Finding], llm: list[Finding]
) -> list[Finding]:
    """Deterministik (Hunspell) ve LLM bulgularını birleştirir.

    Deterministik bulgular her zaman korunur (sözlük temelli, uydurma yok). Aynı
    bölgeye denk gelen (çakışan) LLM bulguları elenir — deterministik olan tercih
    edilir. Konumsuz LLM bulguları (offset yok) karşılaştırılamaz, korunur.
    Sonuç başlangıç offsetine göre sıralanır (konumsuzlar sona).
    """
    merged = list(deterministic)
    for f in llm:
        if any(_spans_overlap(f, d) for d in deterministic):
            continue
        merged.append(f)
    merged.sort(key=lambda x: (x.start is None, x.start if x.start is not None else 0))
    return merged
