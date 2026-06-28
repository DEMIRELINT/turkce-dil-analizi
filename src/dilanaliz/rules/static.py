"""Statik kural sağlayıcısı (Faz 1).

`rules.md` dosyasının tamamını döndürür. Korpus küçük olduğu sürece tüm kuralları
doğrudan prompt'a koymak retrieval hatası riskini sıfırlar. Korpus bağlam
bütçesini aşınca RetrievalRulesProvider'a geçilir.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_RULES_PATH = Path(__file__).with_name("rules.md")


@lru_cache(maxsize=1)
def _load_rules() -> str:
    return _RULES_PATH.read_text(encoding="utf-8")


class StaticRulesProvider:
    """Tüm kural metnini metinden bağımsız olarak döndürür."""

    def __init__(self, rules_path: Path | None = None) -> None:
        self._rules_path = rules_path

    def get_context(self, text: str) -> str:  # noqa: ARG002 — Faz 1'de metin kullanılmaz
        if self._rules_path is not None:
            return self._rules_path.read_text(encoding="utf-8")
        return _load_rules()
