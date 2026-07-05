"""Kural kaynağı arayüzü.

`get_context(text, purpose)` verilen metin ve GEÇİŞ için modele verilecek
kural bağlamını döndürür. `purpose` hangi geçişin istediğini söyler:
"local" (imla + dil bilgisi), "tone" (ton/üslup), "all" (hepsi). Sağlayıcı
yalnız o geçişin işine yarayan bölümleri döndürebilir — gereksiz bölüm hem
token israfıdır hem de halüsinasyon kaynağıdır (başka eksenin "Yanlış:"
örnekleri). Faz 2'de aynı imza ile retrieval sonucu döner (purpose, eksene
göre süzmeyi kolaylaştırır); bu seam sayesinde RAG'e geçişte analyzer değişmez.
"""

from __future__ import annotations

from typing import Protocol


class RulesProvider(Protocol):
    def get_context(self, text: str, purpose: str = "all") -> str:
        """Metne ve geçişe ilişkin kural bağlamını (modele verilecek) döndürür."""
        ...
