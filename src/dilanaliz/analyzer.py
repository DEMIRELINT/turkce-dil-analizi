"""Analiz orkestrasyonu (kademeli geçişler).

Her kontrol kendi bazında AYRI bir geçişte çalışır:
- Yerel geçiş (cümle)      : Hunspell adayları + noktalama/dil bilgisi/anlatım/
  bağlamsal imla. Uzun belgede parça parça (chunk) çalışır.
- Ton geçişi (paragraf)    : yalnız ton/üslup. Parça parça.
- Tutarlılık geçişi (belge): terim/birim/kısaltma tutarsızlığı. BÜTÜN belgede bir
  kez çalışır (tek parça göremez).

Parça-içi geçişlerin offsetleri parçanın kaynaktaki başlangıcı kadar kaydırılır
(rebasing); tutarlılık geçişi zaten bütün metinde çalıştığı için offsetleri global.

Sağlayıcı ve kural kaynağı dışarıdan enjekte edilir; böylece test edilebilir ve
ileride (RAG / self-host) bu parçalar değişse de orkestrasyon değişmez.
"""

from __future__ import annotations

from pathlib import Path

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from .cache import DiskCache, make_key
from .chunk import DEFAULT_MAX_CHARS, chunk_text
from .config import Settings
from .locate import enrich_with_offsets
from .postprocess import drop_noop_findings, merge_findings, validate_suggestions
from .progress import ProgressCallback, ProgressEvent, emit
from .prompt import (
    CONSISTENCY_SYSTEM_PROMPT,
    LOCAL_SYSTEM_PROMPT,
    TONE_SYSTEM_PROMPT,
    build_consistency_message,
    build_tone_message,
    build_user_message,
)
from .providers import build_chat_model
from .rules import RulesProvider, StaticRulesProvider
from .schema import AnalysisResult, Finding, LLMAnalysis, LLMSpellingDecision
from .spell import HunspellChecker


class Analyzer:
    """Metin analiz motoru (çok geçişli)."""

    def __init__(
        self,
        chat_model: BaseChatModel,
        rules_provider: RulesProvider,
        model_id: str | None = None,
        cache: DiskCache | None = None,
        speller: HunspellChecker | None = None,
    ) -> None:
        self._rules = rules_provider
        self._model_id = model_id
        self._cache = cache
        self._speller = speller
        # Yapılandırılmış çıktı: parse hatasını kaldırır. Tüm geçişler aynı şemayı
        # döndürür; yalnız sistem promptu değişir.
        self._structured = chat_model.with_structured_output(LLMAnalysis)

    def analyze(self, text: str) -> AnalysisResult:
        """Kısa metni TEK parça olarak üç geçişle inceler (chunk'lamadan)."""
        findings: list[Finding] = []
        findings += self._local_pass(text)
        findings += self._tone_pass(text)
        findings += self._consistency_pass(text)
        return self._finalize(findings, text)

    def analyze_document(
        self,
        text: str,
        max_chars: int = DEFAULT_MAX_CHARS,
        progress: ProgressCallback | None = None,
    ) -> AnalysisResult:
        """Uzun belgeyi kademeli geçişlerle inceler.

        Yerel ve ton geçişleri parça parça (offset rebasing ile); tutarlılık geçişi
        bütün belgede bir kez. Tüm bulgular tek listede toplanır.

        İsteğe bağlı `progress` callback'i her adımda bir `ProgressEvent` alır
        (web paneli/CLI canlı geri bildirim için); `None` ise davranış değişmez.

        MVP: parçalar sırayla işlenir (paralelleştirme sonraki bir iyileştirme).
        """
        chunks = chunk_text(text, max_chars=max_chars)
        total = len(chunks)
        emit(progress, ProgressEvent("chunk", f"Belge {total} parçaya bölündü", 0, total))

        findings: list[Finding] = []
        for index, chunk in enumerate(chunks, start=1):
            emit(progress, ProgressEvent(
                "local", f"Parça {index}/{total}: yazım ve dil bilgisi inceleniyor",
                index, total))
            local = self._local_pass(chunk.text)
            emit(progress, ProgressEvent(
                "tone", f"Parça {index}/{total}: ton/üslup inceleniyor", index, total))
            tone = self._tone_pass(chunk.text)
            for finding in local + tone:
                if finding.start is not None:
                    finding.start += chunk.start
                if finding.end is not None:
                    finding.end += chunk.start
                findings.append(finding)

        # Belge-geneli tutarlılık: bütün metinde tek geçiş (offsetler zaten global).
        emit(progress, ProgressEvent(
            "consistency", "Belge geneli tutarlılık inceleniyor", total, total))
        findings += self._consistency_pass(text)

        emit(progress, ProgressEvent(
            "finalize", "Bulgular birleştiriliyor ve sıralanıyor", total, total))
        result = self._finalize(findings, text)
        emit(progress, ProgressEvent("done", "Analiz tamamlandı", total, total))
        return result

    # --- Tek tek geçişler ----------------------------------------------------

    def _local_pass(self, text: str) -> list[Finding]:
        """Cümle bazlı geçiş: Hunspell adayları + noktalama/dil bilgisi/bağlamsal imla."""
        rules_context = self._rules.get_context(text)
        candidates = self._speller.check_text(text) if self._speller else []
        candidate_words = [c.excerpt for c in candidates]

        user_message = build_user_message(rules_context, text, candidate_words)
        raw = self._invoke_cached(LOCAL_SYSTEM_PROMPT, user_message)

        result = raw.to_result()
        drop_noop_findings(result)
        enrich_with_offsets(result, text)

        spelling_findings = self._resolve_spelling(candidates, raw.spelling)
        return merge_findings(spelling_findings, result.findings)

    def _tone_pass(self, text: str) -> list[Finding]:
        """Paragraf bazlı geçiş: yalnız ton/üslup."""
        rules_context = self._rules.get_context(text)
        user_message = build_tone_message(rules_context, text)
        return self._located_findings(TONE_SYSTEM_PROMPT, user_message, text)

    def _consistency_pass(self, text: str) -> list[Finding]:
        """Bütün belge geçişi: terim/birim/kısaltma tutarsızlığı."""
        user_message = build_consistency_message(text)
        return self._located_findings(CONSISTENCY_SYSTEM_PROMPT, user_message, text)

    def _located_findings(
        self, system_prompt: str, user_message: str, text: str
    ) -> list[Finding]:
        """LLM geçişini çalıştırır, noop'ları atar, offsetleri konumlar."""
        raw = self._invoke_cached(system_prompt, user_message)
        result = raw.to_result()
        drop_noop_findings(result)
        enrich_with_offsets(result, text)
        return result.findings

    # --- Birleştirme / son işleme -------------------------------------------

    def _finalize(self, findings: list[Finding], text: str) -> AnalysisResult:
        """Tüm geçişlerin bulgularını tekilleştirir, doğrular ve sıralar."""
        result = AnalysisResult(findings=_dedup(findings))
        result.model_id = self._model_id
        result.text_len = len(text)
        # Bozuk öneri koruması (örn. "birçok" → "birchoq"): otomatik uygulamada
        # veriyi bozacak önerileri eler.
        validate_suggestions(result)
        result.findings.sort(
            key=lambda f: (f.start is None, f.start if f.start is not None else 0)
        )
        return result

    @staticmethod
    def _resolve_spelling(
        candidates: list[Finding], decisions: list[LLMSpellingDecision]
    ) -> list[Finding]:
        """Hunspell adaylarını Gemini kararlarıyla birleştirir.

        - Gemini "hata değil" dediyse (özel ad/terim) aday elenir.
        - "hata" + düzeltme verdiyse öneri bağlama uygun olanla güncellenir.
        - Gemini bu adaya dair karar vermediyse: tespit kaybolmasın diye Hunspell
          bulgusu kendi (zayıf) önerisiyle korunur (fallback).
        """
        by_word: dict[str, LLMSpellingDecision] = {}
        for d in decisions:
            by_word.setdefault(d.word, d)
            by_word.setdefault(d.word.casefold(), d)

        resolved: list[Finding] = []
        for c in candidates:
            d = by_word.get(c.excerpt) or by_word.get(c.excerpt.casefold())
            if d is None:
                resolved.append(c)  # fallback: tespiti koru
                continue
            if not d.is_error:
                continue  # Gemini: geçerli kullanım, ele
            if d.correction.strip():
                c.suggestion = d.correction.strip()
            resolved.append(c)
        return resolved

    def _invoke_cached(self, system_prompt: str, user_message: str) -> LLMAnalysis:
        key = make_key(self._model_id or "", system_prompt, user_message)
        if self._cache is not None:
            hit = self._cache.get(key)
            if hit is not None:
                return LLMAnalysis.model_validate_json(hit)

        raw: LLMAnalysis = self._structured.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]
        )

        if self._cache is not None:
            self._cache.set(key, raw.model_dump_json())
        return raw


def _dedup(findings: list[Finding]) -> list[Finding]:
    """Geçişler arası birebir tekrarları (aynı tip + konum + alıntı) eler."""
    seen: set[tuple] = set()
    out: list[Finding] = []
    for f in findings:
        key = (f.type, f.start, f.end, f.excerpt)
        if key in seen:
            continue
        seen.add(key)
        out.append(f)
    return out


def build_default_analyzer(
    settings: Settings | None = None, use_cache: bool = True
) -> Analyzer:
    """Env tabanlı varsayılan analyzer (Gemini + statik kurallar + disk önbelleği)."""
    settings = settings or Settings.from_env()
    chat_model = build_chat_model(settings)
    cache = DiskCache(".cache/llm_cache.json") if use_cache else None
    # RULES_PATH verilmişse harici dökümanı kullan; yoksa paketteki rules.md.
    rules_path = Path(settings.rules_path) if settings.rules_path else None
    # Sözlük varsa deterministik imla katmanını (Hunspell) etkinleştir.
    speller = None
    if settings.dict_path and Path(f"{settings.dict_path}.dic").exists():
        speller = HunspellChecker(settings.dict_path)
    return Analyzer(
        chat_model=chat_model,
        rules_provider=StaticRulesProvider(rules_path=rules_path),
        model_id=settings.model_id,
        cache=cache,
        speller=speller,
    )
