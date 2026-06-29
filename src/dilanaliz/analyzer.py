"""Analiz orkestrasyonu.

Akış: text → RulesProvider.get_context → prompt (system + rules + text)
→ chat_model.with_structured_output(LLMAnalysis) → public sonuca dönüştür
→ locate ile offset → AnalysisResult.

Sağlayıcı ve kural kaynağı dışarıdan enjekte edilir; böylece test edilebilir ve
ileride (RAG / self-host) bu parçalar değişse de analyzer değişmez.
"""

from __future__ import annotations

from pathlib import Path

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from .cache import DiskCache, make_key
from .chunk import DEFAULT_MAX_CHARS, chunk_text
from .config import Settings
from .locate import enrich_with_offsets
from .postprocess import drop_noop_findings, merge_findings
from .prompt import SYSTEM_PROMPT, build_user_message
from .providers import build_chat_model
from .rules import RulesProvider, StaticRulesProvider
from .schema import AnalysisResult, Finding, LLMAnalysis, LLMSpellingDecision
from .spell import HunspellChecker


class Analyzer:
    """Metin analiz motoru."""

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
        # Yapılandırılmış çıktı: parse hatasını kaldırır.
        self._structured = chat_model.with_structured_output(LLMAnalysis)

    def analyze(self, text: str) -> AnalysisResult:
        rules_context = self._rules.get_context(text)

        # Deterministik tespit: Hunspell şüpheli kelimeleri (offsetli) bulur.
        candidates = self._speller.check_text(text) if self._speller else []
        candidate_words = [c.excerpt for c in candidates]

        user_message = build_user_message(rules_context, text, candidate_words)
        raw = self._invoke_cached(user_message)

        # LLM bulguları: dil bilgisi + ton + bağlamsal imla.
        result = raw.to_result()
        result.model_id = self._model_id
        result.text_len = len(text)
        drop_noop_findings(result)
        enrich_with_offsets(result, text)

        # İmla bulguları: Hunspell adayları + Gemini'nin bağlamsal düzeltme/doğrulaması.
        spelling_findings = self._resolve_spelling(candidates, raw.spelling)

        result.findings = merge_findings(spelling_findings, result.findings)
        return result

    def analyze_document(
        self, text: str, max_chars: int = DEFAULT_MAX_CHARS
    ) -> AnalysisResult:
        """Uzun metni parçalara bölüp her parçayı `analyze` ile inceler (Faz 3).

        Parça-içi bulgu offsetleri, parçanın kaynaktaki başlangıcı kadar kaydırılıp
        (rebasing) kaynak metne taşınır; böylece offsetler tüm belgeye göre doğru
        kalır. Bulgular tek listede toplanır ve başlangıç offsetine göre sıralanır
        (konumsuzlar sona).

        MVP: parçalar sırayla işlenir (paralelleştirme sonraki bir iyileştirme).
        Parçalar çakışmadığı için parçalar-arası tekrar oluşmaz; belge-geneli
        tutarlılık (terim/birim) bu turun KAPSAMINDA DEĞİLDİR.
        """
        chunks = chunk_text(text, max_chars=max_chars)
        all_findings: list[Finding] = []
        for chunk in chunks:
            part = self.analyze(chunk.text)
            for finding in part.findings:
                if finding.start is not None:
                    finding.start += chunk.start
                if finding.end is not None:
                    finding.end += chunk.start
                all_findings.append(finding)

        all_findings.sort(
            key=lambda f: (f.start is None, f.start if f.start is not None else 0)
        )
        result = AnalysisResult(findings=all_findings)
        result.model_id = self._model_id
        result.text_len = len(text)
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

    def _invoke_cached(self, user_message: str) -> LLMAnalysis:
        key = make_key(self._model_id or "", SYSTEM_PROMPT, user_message)
        if self._cache is not None:
            hit = self._cache.get(key)
            if hit is not None:
                return LLMAnalysis.model_validate_json(hit)

        raw: LLMAnalysis = self._structured.invoke(
            [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_message)]
        )

        if self._cache is not None:
            self._cache.set(key, raw.model_dump_json())
        return raw


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
