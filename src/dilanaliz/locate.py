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


# Tırnak/kesme eşdeğer sınıfları: kaynak Word "akıllı tırnak" (’ “ ”) taşır,
# LLM excerpt'i çoğu kez düz ASCII (' ") döndürür. Eşleştirmede iki biçim de
# aynı sayılmalı; yoksa bulgu haksız yere "konumsuz" kalır.
_QUOTE_CLASSES = {
    "'": "['’‘‚ʼ]", "’": "['’‘‚ʼ]", "‘": "['’‘‚ʼ]", "‚": "['’‘‚ʼ]", "ʼ": "['’‘‚ʼ]",
    '"': '["“”„]', "“": '["“”„]', "”": '["“”„]', "„": '["“”„]',
}


def _normalized_matches(source: str, excerpt: str) -> list[tuple[int, int]]:
    """Boşluk VE tırnak-biçimi farklarını tolere ederek eşleştirir.

    Boşluk dizileri `\\s+` ile esnek; tırnak/kesme karakterleri eşdeğer
    sınıfıyla ([’'] gibi) aranır. Kalan karakterler birebirdir.
    """
    excerpt = excerpt.strip()
    if not excerpt:
        return []
    parts: list[str] = []
    in_space = False
    for ch in excerpt:
        if ch.isspace():
            if not in_space:
                parts.append(r"\s+")
                in_space = True
            continue
        in_space = False
        parts.append(_QUOTE_CLASSES.get(ch) or re.escape(ch))
    pattern = "".join(parts)
    return [(m.start(), m.end()) for m in re.finditer(pattern, source)]


def find_spans(source: str, excerpt: str) -> list[tuple[int, int]]:
    """Önce birebir, yoksa boşluk/tırnak-normalize eşleşmeleri döndürür."""
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
