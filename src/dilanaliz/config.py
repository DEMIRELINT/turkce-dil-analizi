"""Ortam tabanlı ayarlar.

Tek bir `Settings` nesnesi; sağlayıcı katmanı ve analyzer buradan beslenir.
Üretime (Faz 8) geçişte yalnız değerler değişir, kod değişmez.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# .env varsa yükle (yoksa sessiz geçer); ortam değişkenleri her zaman önceliklidir.
load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on", "evet"}


@dataclass(frozen=True)
class Settings:
    """Çalışma zamanı ayarları."""

    gemini_api_key: str
    model_id: str
    temperature: float
    langsmith_tracing: bool
    rules_path: str | None
    dict_path: str | None

    @classmethod
    def from_env(cls) -> "Settings":
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY tanımlı değil. .env dosyasını .env.example'dan "
                "oluşturup anahtarı girin."
            )
        rules_path = os.getenv("RULES_PATH", "").strip() or None
        # Hunspell sözlük taban yolu (uzantısız). Boşsa varsayılan dicts/tr_TR.
        dict_path = os.getenv("DICT_PATH", "dicts/tr_TR").strip() or None
        return cls(
            gemini_api_key=api_key,
            model_id=os.getenv("MODEL_ID", "gemini-2.5-flash-lite").strip(),
            temperature=float(os.getenv("TEMPERATURE", "0")),
            langsmith_tracing=_env_bool("LANGSMITH_TRACING", False),
            rules_path=rules_path,
            dict_path=dict_path,
        )
