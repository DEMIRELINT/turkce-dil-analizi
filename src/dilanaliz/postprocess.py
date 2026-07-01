"""Bulgu son-işleme (deterministik temizlik).

LLM bazen "hata var" deyip `suggestion`'ı `excerpt` ile birebir aynı veriyor
(örn. "Ben de" → "Ben de"). Bu, değiştirilecek bir şey olmadığı anlamına gelir:
gerçek bir düzeltme değil, yanlış pozitiftir. Bu tür bulguları deterministik
olarak eleriz. Bu, özellikle de/da ve ki üzerindeki aşırı tetiklenmeyi azaltır.

Normalleştirme HAFİF tutulur (baş/son boşluk + iç boşluk daraltma); noktalama
KORUNUR, çünkü "yalnız mı" → "yalnız mı?" gerçek bir düzeltmedir.
"""

from __future__ import annotations

import unicodedata

from .schema import AnalysisResult, Finding

# Türkçe alfabede bulunmayan harfler. Öneride bunlar varken ALINTIDA yoksa, öneri
# büyük olasılıkla bozulmuştur (örn. "birçok" → "birchoq") → güvenilmez sayılır.
_NON_TURKISH = set("qwxQWX")


def _norm(s: str) -> str:
    # NFC normalizasyonu: Türkçe "î/â/ê" gibi harfler tek kod noktası (NFC)
    # veya harf+bileşik-işaret (NFD) olarak gelebilir; ikisi görsel olarak
    # aynıdır ama normalize edilmeden karşılaştırılırsa eşit sayılmaz.
    return " ".join(unicodedata.normalize("NFC", s).split())


def is_noop_suggestion(excerpt: str, suggestion: str) -> bool:
    """Öneri, alıntıyla anlamlı bir fark taşımıyorsa True."""
    return _norm(excerpt) == _norm(suggestion)


def drop_noop_findings(result: AnalysisResult) -> AnalysisResult:
    """Önerisi alıntıyla aynı olan bulguları çıkarır (yerinde)."""
    result.findings = [
        f for f in result.findings if not is_noop_suggestion(f.excerpt, f.suggestion)
    ]
    return result


def _suggestion_is_corrupt(excerpt: str, suggestion: str) -> bool:
    """Öneri, alıntıda olmayan Türkçe-dışı harf (q/w/x) içeriyorsa True."""
    return bool((set(suggestion) & _NON_TURKISH) - set(excerpt))


def validate_suggestions(result: AnalysisResult) -> AnalysisResult:
    """Bozuk öneri içeren bulguları eler (yerinde).

    Model bazen yakaladığı bir hataya geçersiz/ASCII'leştirilmiş öneri üretir
    (örn. "birçok" yerine "birchoq"). Böyle bir öneri otomatik uygulanırsa metni
    bozar; kaçırmaktan daha tehlikelidir. Bu yüzden güvenilmez kabul edilip atılır.
    """
    result.findings = [
        f
        for f in result.findings
        if not _suggestion_is_corrupt(f.excerpt, f.suggestion)
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
