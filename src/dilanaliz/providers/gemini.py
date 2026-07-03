"""Gemini sağlayıcısı (geliştirme ortamı)."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI

from ..config import Settings


def build_gemini(settings: Settings) -> BaseChatModel:
    """`ChatGoogleGenerativeAI` örneği üretir (temperature=0).

    `timeout` verilmezse istemci sınırsız bekler; kurumsal ağda bağlantı
    yarıda tıkanırsa çağrı asılı kalabilir (bkz. `Settings.llm_timeout_sec`).
    """
    return ChatGoogleGenerativeAI(
        model=settings.model_id,
        google_api_key=settings.gemini_api_key,
        temperature=settings.temperature,
        transport=settings.genai_transport,
        timeout=settings.llm_timeout_sec,
    )
