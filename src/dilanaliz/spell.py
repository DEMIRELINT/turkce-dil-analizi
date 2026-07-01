"""Deterministik imla denetimi (Hunspell / spylls — saf Python).

Sözlük temelli olduğu için UYDURMA yapmaz: yalnız sözlükte olmayan kelimeleri
işaretler. Tamamen yerel çalışır (air-gap dostu). Offsetleri doğrudan üretir,
locate'e ihtiyaç duymaz.

Bilinen sınır: sözlükte olmayan özel ad / yabancı kelime / kısaltma yanlış-pozitif
üretebilir (rapordaki "deterministik yanlış pozitif" riski). Bunun için opsiyonel
bir beyaz liste desteklenir.
"""

from __future__ import annotations

import re
from pathlib import Path

from spylls.hunspell import Dictionary

from .schema import Finding, FindingType

# Harf dizileri (rakam/alt çizgi hariç), Unicode — Türkçe harfleri kapsar.
_WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)


class HunspellChecker:
    """spylls (Hunspell) ile sözlük temelli imla denetçisi."""

    def __init__(self, dict_base: str | Path, whitelist: set[str] | None = None) -> None:
        # dict_base: uzantısız taban yol (örn. "dicts/tr_TR" → .aff + .dic).
        self._dict = Dictionary.from_files(str(dict_base))
        self._whitelist = {w.casefold() for w in (whitelist or set())}

    def check_text(self, text: str) -> list[Finding]:
        findings: list[Finding] = []
        for m in _WORD_RE.finditer(text):
            word = m.group(0)
            if len(word) < 2:
                continue
            if word.casefold() in self._whitelist:
                continue
            if self._dict.lookup(word):
                continue
            suggestions = list(self._dict.suggest(word))
            suggestion = suggestions[0] if suggestions else "(sözlükte öneri yok)"
            findings.append(
                Finding(
                    type=FindingType.IMLA,
                    excerpt=word,
                    explanation="Sözlükte bulunmayan kelime; yazım hatası olabilir.",
                    suggestion=suggestion,
                    rule_id="HUNSPELL",
                    start=m.start(),
                    end=m.end(),
                )
            )
        return findings
