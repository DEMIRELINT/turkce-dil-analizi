"""Uzun metni anlamlı parçalara böler (Faz 3 — MVP).

Parçalama DETERMİNİSTİK koddur (AI değil). Birim PARAGRAF'tır: boş satırla
ayrılmış bloklar atomik kabul edilir, böylece cümle asla ortadan kesilmez.
Paragraflar bir karakter bütçesine (`max_chars`) kadar gruplanır. Bütçeyi tek
başına aşan bir paragraf ise cümle sınırından (kısaltma/sayı/baş-harf korumalı)
parçalara inilir; güvenli bölünemeyen tek bir cümle son çare olarak bütün kalır.

Her parça, kaynak metindeki başlangıç offsetiyle (`start`) döner. `text` daima
kaynağın birebir dilimidir (`source[start:start+len(text)]`); böylece parça-içi
bulgu offsetleri kaynak metne geri taşınabilir (rebasing — bkz. analyzer).

İleride (bu MVP'de değil): başlık (örn. ``1.4``, ``3.2``) farkındalıklı bölme.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Paragraf ayıracı: en az bir boş satır (arada yalnız boşluk olabilir).
_BLANK_LINE = re.compile(r"\n\s*\n")
# Boş olmayan bir blok: ilk boş-olmayan karakterden, sonraki boş satıra (ya da
# metin sonuna) kadar. DOTALL ile blok içi tek satır sonlarını da kapsar.
_PARAGRAPH = re.compile(r"\S.*?(?=\n\s*\n|\Z)", re.DOTALL)

# Varsayılan parça bütçesi (karakter). Modelin odağını koruyacak kadar küçük,
# çağrı sayısını şişirmeyecek kadar büyük; çağrı tarafında ayarlanabilir.
DEFAULT_MAX_CHARS = 3000

# Cümle sonu adayı: bir kelime + ., !, ? + boşluk; SONRASINDA Türkçe büyük harf.
# "Sonraki büyük harf" şartı sayıları korur ("15.30" boşluksuz; "2. kez" küçük
# harfle devam eder → ikisi de sınır sayılmaz). Türkçe büyük harf sınıfı İ/Ş/Ğ/Ç/
# Ö/Ü içerir (naif [A-Z] bunları kaçırır).
_SENTENCE_BOUNDARY = re.compile(r"(\w+)[.!?]+\s+(?=[A-ZÇĞİÖŞÜ])")

# Noktadan önceki kelime bunlardan biriyse cümle sonu sayma (yanlış bölmeyi önler).
# Küçük harfle tutulur; karşılaştırma casefold ile yapılır.
_ABBREVIATIONS = frozenset({
    "prof", "doç", "doc", "dr", "yrd", "av", "sn", "no", "nu", "vb", "vs",
    "bkz", "örn", "age", "çev", "haz", "ed", "md", "müh", "ltd", "şti",
    "cad", "sok", "mah", "apt", "blv", "bld", "tel", "faks", "tic", "san",
})


@dataclass(frozen=True)
class Chunk:
    """Kaynak metnin bir parçası ve onun kaynaktaki başlangıç offseti."""

    text: str
    start: int

    @property
    def end(self) -> int:
        return self.start + len(self.text)


def _paragraph_spans(source: str) -> list[tuple[int, int]]:
    """Boş-olmayan paragraf bloklarının (başlangıç, bitiş) offsetleri."""
    return [(m.start(), m.end()) for m in _PARAGRAPH.finditer(source)]


def _sentence_spans(source: str, start: int, end: int) -> list[tuple[int, int]]:
    """`source[start:end]` paragrafını cümle sınırlarından (start, bitiş) offsetlerine böler.

    Kısaltma ("Dr."), sayı ("15.30") ve tek-harf baş harf ("Ahmet B. Yılmaz")
    yanlış-bölmeleri elenir. Dönen span'ler BİTİŞİKTİR ve `[start, end)` aralığını
    EKSİKSİZ kaplar; böylece her parça hâlâ kaynağın birebir dilimidir.
    """
    segment = source[start:end]
    spans: list[tuple[int, int]] = []
    cut = 0  # segment-yerel kesim noktası
    for m in _SENTENCE_BOUNDARY.finditer(segment):
        word = m.group(1)
        if word.casefold() in _ABBREVIATIONS or word.isdigit() or len(word) == 1:
            continue
        boundary = m.end()  # lookahead sıfır-genişlik → büyük harften hemen önce
        spans.append((start + cut, start + boundary))
        cut = boundary
    spans.append((start + cut, end))  # kalan (sınır yoksa: paragrafın tamamı)
    return spans


def _atomic_spans(source: str, max_chars: int) -> list[tuple[int, int]]:
    """Gruplanacak en küçük birimler: normalde paragraf; bütçeyi aşan paragraf
    cümle span'lerine inilir."""
    spans: list[tuple[int, int]] = []
    for start, end in _paragraph_spans(source):
        if end - start > max_chars:
            spans.extend(_sentence_spans(source, start, end))
        else:
            spans.append((start, end))
    return spans


def chunk_text(source: str, max_chars: int = DEFAULT_MAX_CHARS) -> list[Chunk]:
    """Metni paragraf/cümle sınırından, `max_chars` bütçesine göre parçalara böler.

    Birim PARAGRAF'tır; bütçeyi tek başına aşan paragraf önce cümle span'lerine
    inilir (`_atomic_spans`). İlk span her parçaya daima dahil edilir (tek başına
    bütçeyi aşsa bile — güvenli bölünemeyen tek cümle bütün kalır). Sonra toplam
    boyut bütçeyi aşmadığı sürece sonraki span'ler eklenir. Parça metni span
    aralarındaki ayıraçları da içerir (kaynağın birebir dilimi), offsetler bozulmaz.
    """
    if max_chars <= 0:
        raise ValueError("max_chars pozitif olmalı")

    spans = _atomic_spans(source, max_chars)
    chunks: list[Chunk] = []
    i = 0
    while i < len(spans):
        start, end = spans[i]
        i += 1
        while i < len(spans):
            nxt_end = spans[i][1]
            if nxt_end - start > max_chars:
                break
            end = nxt_end
            i += 1
        chunks.append(Chunk(text=source[start:end], start=start))
    return chunks
