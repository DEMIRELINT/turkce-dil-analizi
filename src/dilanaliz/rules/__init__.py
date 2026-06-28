"""Kural bilgi kaynağı katmanı.

Bu katman, kuralların analiz motorundan bağımsız olmasını sağlar (en kritik seam).
Faz 1: StaticRulesProvider (tüm kuralları döndürür).
Faz 2: RetrievalRulesProvider (aynı imza, retrieval ile) — motor değişmez.
"""

from .base import RulesProvider
from .static import StaticRulesProvider

__all__ = ["RulesProvider", "StaticRulesProvider"]
