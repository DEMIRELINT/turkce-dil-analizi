"""Sağlayıcı soyutlaması.

Soyutlama LangChain'in `BaseChatModel` arayüzüdür: analyzer somut sağlayıcıyı
(Gemini, vLLM, ...) bilmez. Faz 8'de yerel vLLM eklemek için yeni bir dal eklemek
yeterli; analyzer değişmez.
"""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel

from ..config import Settings


def build_chat_model(settings: Settings) -> BaseChatModel:
    """Ayarlara göre uygun chat modelini üretir.

    Şu an yalnız Gemini (geliştirme). İlerideki sağlayıcılar buraya eklenir.
    """
    from .gemini import build_gemini

    return build_gemini(settings)
