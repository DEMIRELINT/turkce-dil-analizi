"""Uzun metni anlamlı parçalara böler (Faz 3 — MVP).

Parçalama DETERMİNİSTİK koddur (AI değil). MVP'de birim PARAGRAF'tır: boş satırla
ayrılmış bloklar atomik kabul edilir, böylece cümle asla ortadan kesilmez.
Paragraflar bir karakter bütçesine (`max_chars`) kadar gruplanır; bütçeyi tek
başına aşan bir paragraf kendi parçası olur (MVP'de cümleye inilmez).

Her parça, kaynak metindeki başlangıç offsetiyle (`start`) döner. `text` daima
kaynağın birebir dilimidir (`source[start:start+len(text)]`); böylece parça-içi
bulgu offsetleri kaynak metne geri taşınabilir (rebasing — bkz. analyzer).

İleride (bu MVP'de değil): başlık (örn. ``1.4``, ``3.2``) farkındalıklı bölme ve
çok büyük paragrafların cümleye inilerek bölünmesi.
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


def chunk_text(source: str, max_chars: int = DEFAULT_MAX_CHARS) -> list[Chunk]:
    """Metni paragraf sınırından, `max_chars` bütçesine göre parçalara böler.

    İlk paragraf her parçaya daima dahil edilir (tek başına bütçeyi aşsa bile).
    Sonra, toplam boyut bütçeyi aşmadığı sürece sonraki paragraflar eklenir.
    Parça metni paragraf aralarındaki ayıraçları da içerir (kaynağın birebir
    dilimi olması için), bu yüzden offsetler bozulmaz.
    """
    if max_chars <= 0:
        raise ValueError("max_chars pozitif olmalı")

    paras = _paragraph_spans(source)
    chunks: list[Chunk] = []
    i = 0
    while i < len(paras):
        start, end = paras[i]
        i += 1
        while i < len(paras):
            nxt_end = paras[i][1]
            if nxt_end - start > max_chars:
                break
            end = nxt_end
            i += 1
        chunks.append(Chunk(text=source[start:end], start=start))
    return chunks
