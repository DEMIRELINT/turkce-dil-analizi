"""Kural kaynağı arayüzü.

`get_context(text)` verilen metin için modele verilecek kural bağlamını döndürür.
Faz 1'de metinden bağımsız olarak tüm kurallar döner; Faz 2'de aynı imza ile
retrieval sonucu döner. Bu seam sayesinde RAG'e geçişte analyzer değişmez.
"""

from __future__ import annotations

from typing import Protocol


class RulesProvider(Protocol):
    def get_context(self, text: str) -> str:
        """Metne ilişkin kural bağlamını (modele verilecek) döndürür."""
        ...
