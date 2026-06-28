"""Bulgu alıntılarını kaynak metinde konumlama.

LLM `excerpt`'i çoğu zaman birebir döndürür; ama bazen boşluk/satır farkı olur.
Bu yüzden önce birebir, sonra boşluk-normalize eşleştirme deneriz. Bulunamazsa
offset None kalır (bulgu atılmaz — "konumsuz" olarak durur).

Aynı alıntı metinde birden çok geçiyorsa, daha önce atanmış konumların üstüne
yazmamak için kullanılmış aralıklar takip edilir.
"""

from __future__ import annotations

import re

from .schema import AnalysisResult


def _exact_matches(source: str, excerpt: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    start = source.find(excerpt)
    while start != -1:
        spans.append((start, start + len(excerpt)))
        start = source.find(excerpt, start + 1)
    return spans


def _normalized_matches(source: str, excerpt: str) -> list[tuple[int, int]]:
    """Boşluk farklarını tolere ederek eşleştirir (\\s+ esnek)."""
    tokens = excerpt.split()
    if not tokens:
        return []
    pattern = r"\s+".join(re.escape(tok) for tok in tokens)
    return [(m.start(), m.end()) for m in re.finditer(pattern, source)]


def find_spans(source: str, excerpt: str) -> list[tuple[int, int]]:
    """Önce birebir, yoksa boşluk-normalize eşleşmeleri döndürür."""
    spans = _exact_matches(source, excerpt)
    if spans:
        return spans
    return _normalized_matches(source, excerpt)


def enrich_with_offsets(result: AnalysisResult, source: str) -> AnalysisResult:
    """Her bulguya kaynak metindeki start/end offsetini ekler (yerinde).

    Çakışma engelleme yalnız AYNI alıntı birden çok bulguda geçtiğinde uygulanır:
    n'inci tekrar, metindeki n'inci eşleşmeye atanır. Farklı alıntılar bağımsızdır;
    aynı bölgede çakışabilirler (örn. imla "herkez" ile ton "herkez görsün.").
    """
    seen: dict[str, int] = {}
    for finding in result.findings:
        spans = find_spans(source, finding.excerpt)
        idx = seen.get(finding.excerpt, 0)
        if idx < len(spans):
            finding.start, finding.end = spans[idx]
            seen[finding.excerpt] = idx + 1
        else:
            # Hiç (veya artık) eşleşme yoksa konumsuz bırak (bulgu atılmaz).
            finding.start, finding.end = None, None
    return result
