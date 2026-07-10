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
    # max_retries=2: kütüphane varsayılanı (6) kalıcı hataları da (örn. kapatılmış
    # model 404'ü) körlemesine yeniden dener — çağrı başına ~1 dk israf. Geçici
    # hataların asıl savunması analyzer._call_structured'daki sınıflandırmalı
    # yeniden denemedir; buradaki 2, yalnız kısa süreli ağ hıçkırıkları için.
    return ChatGoogleGenerativeAI(
        model=settings.model_id,
        google_api_key=settings.gemini_api_key,
        temperature=settings.temperature,
        transport=settings.genai_transport,
        timeout=settings.llm_timeout_sec,
        max_retries=2,
    )
