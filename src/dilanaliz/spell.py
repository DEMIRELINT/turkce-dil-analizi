"""Deterministik imla denetimi (Hunspell / spylls — saf Python).

Sözlük temelli olduğu için UYDURMA yapmaz: yalnız sözlükte olmayan kelimeleri
işaretler. Tamamen yerel çalışır (air-gap dostu). Offsetleri doğrudan üretir,
locate'e ihtiyaç duymaz.

GÖREV AYRIMI: Bu katman yalnız TESPİT eder ("sözlükte yok"); düzeltme ÖNERİSİ
üretmez. Öneri, bağlamı gören LLM'den gelir (analyzer._resolve_spelling) — LLM
karar vermezse bulgu "öneri yok" notuyla kalır. Hunspell'in kendi `suggest()`
çıktısı bilinçli olarak KULLANILMAZ: bağlamdan habersizdir ve kopuk kelime
parçalarına anlamsız öneri üretir (örn. "nde" → "ned"); ayrıca spylls'in en
yavaş işlemidir.

Bilinen sınırlar:
- Sözlükte olmayan özel ad / yabancı kelime / kısaltma yanlış-pozitif üretebilir;
  bunun için opsiyonel beyaz liste desteklenir ve LLM kararı eler.
- 4 harften kısa kelimeler denetlenmez: bunlar pratikte hep belge dönüştürme
  artığı kopuk ek parçalarıdır ("nde", "nda"); gerçek 2-3 harfli Türkçe kelime
  hatası kayda değer değildir.
"""

from __future__ import annotations

import re
from pathlib import Path

from spylls.hunspell import Dictionary

from .schema import Finding, FindingType

# Harf dizileri (rakam/alt çizgi hariç), Unicode — Türkçe harfleri kapsar.
_WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)

# Denetlenecek en kısa kelime uzunluğu (altı: kopuk ek parçası varsayılır).
_MIN_WORD_LEN = 4

# Hunspell bulgusunda LLM'den düzeltme gelmezse gösterilecek yer tutucu.
NO_SUGGESTION = "(öneri yok — kelimeyi bağlamda kontrol edin)"


# --- Türkçe harf-duyarlı büyük/küçük dönüşümleri -----------------------------
# Python'un yerleşik lower/upper'ı Türkçe İ/I ayrımını bilmez ("I".lower() → "i",
# doğrusu "ı"; "i".upper() → "I", doğrusu "İ"). Bu yardımcılar önce noktalı/
# noktasız I'ları elle eşler, kalanını yerleşik dönüşüme bırakır.

def tr_lower(s: str) -> str:
    """Türkçe kurallara göre küçük harfe çevirir (I→ı, İ→i)."""
    return s.replace("I", "ı").replace("İ", "i").lower()


def tr_upper(s: str) -> str:
    """Türkçe kurallara göre büyük harfe çevirir (ı→I, i→İ)."""
    return s.replace("ı", "I").replace("i", "İ").upper()


def tr_capitalize(s: str) -> str:
    """Yalnız ilk harfi Türkçe kurala göre büyütür, kalanı olduğu gibi bırakır."""
    if not s:
        return s
    return tr_upper(s[0]) + s[1:]


def match_case(reference: str, s: str) -> str:
    """`s`'yi `reference`'ın harf düzenine (case) giydirir.

    LLM düzeltmeleri çoğu kez küçük harfle gelir; alıntı TAMAMI BÜYÜK ise öneri
    de büyük olmalı ("SEÇENEKLERI" için "seçenekleri" değil "SEÇENEKLERİ").
    """
    if not s or not reference:
        return s
    if reference.isupper() and len(reference) > 1:
        return tr_upper(s)
    if reference[0].isupper() and s[0].islower():
        return tr_capitalize(s)
    return s


class HunspellChecker:
    """spylls (Hunspell) ile sözlük temelli imla denetçisi (yalnız tespit)."""

    def __init__(self, dict_base: str | Path, whitelist: set[str] | None = None) -> None:
        # dict_base: uzantısız taban yol (örn. "dicts/tr_TR" → .aff + .dic).
        self._dict = Dictionary.from_files(str(dict_base))
        self._whitelist = {w.casefold() for w in (whitelist or set())}

    def _known(self, word: str) -> bool:
        """Kelime (veya Türkçe-kurallı harf varyantları) sözlükte geçerli mi?

        spylls, BÜYÜK harfli Türkçe kelimeyi küçültürken ASCII kuralı uygular
        ("FREKANSINA" → "frekansina", noktasız ı kaybolur) ve sözlükte bulamaz.
        Bu yüzden Türkçe küçültme ve baş-harf-büyük varyantları da denenir
        (baş-harf varyantı özel adları kapsar: "İSTANBUL" → "İstanbul").
        """
        if self._dict.lookup(word):
            return True
        lowered = tr_lower(word)
        if lowered != word and self._dict.lookup(lowered):
            return True
        capitalized = tr_capitalize(lowered)
        if capitalized not in (word, lowered) and self._dict.lookup(capitalized):
            return True
        return False

    def check_text(self, text: str) -> list[Finding]:
        findings: list[Finding] = []
        for m in _WORD_RE.finditer(text):
            word = m.group(0)
            if len(word) < _MIN_WORD_LEN:
                continue  # kopuk ek parçası varsayılır (bkz. modül docstring'i)
            if word.casefold() in self._whitelist:
                continue
            if self._known(word):
                continue
            findings.append(
                Finding(
                    type=FindingType.IMLA,
                    excerpt=word,
                    explanation="Sözlükte bulunmayan kelime; yazım hatası olabilir.",
                    suggestion=NO_SUGGESTION,  # öneri LLM'den gelir (bkz. analyzer)
                    rule_id="HUNSPELL",
                    start=m.start(),
                    end=m.end(),
                )
            )
        return findings
