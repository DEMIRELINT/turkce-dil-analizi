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

import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from .cache import DiskCache, make_key
from .chunk import DEFAULT_MAX_CHARS, chunk_text
from .config import Settings
from .extract import BlockSpan
from .locate import enrich_with_offsets
from .postprocess import (
    drop_context_satisfied_findings,
    drop_noop_findings,
    drop_unlocated_findings,
    merge_findings,
    validate_suggestions,
)
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
from .schema import AnalysisResult, Finding, FindingType, LLMAnalysis, LLMSpellingDecision
from .spell import HunspellChecker, match_case


class LLMCallError(RuntimeError):
    """LLM çağrısı zaman aşımına uğradığında veya retry'lar tükendiğinde fırlatılır.

    Orijinal istisnayı sarmalar; kullanıcıya CLI/web sınırında anlaşılır bir
    mesaj göstermek içindir (ham stack trace yerine).
    """


class Analyzer:
    """Metin analiz motoru (çok geçişli)."""

    def __init__(
        self,
        chat_model: BaseChatModel,
        rules_provider: RulesProvider,
        model_id: str | None = None,
        cache: DiskCache | None = None,
        speller: HunspellChecker | None = None,
        max_workers: int = 1,
    ) -> None:
        self._rules = rules_provider
        self._model_id = model_id
        self._cache = cache
        self._speller = speller
        # Eşzamanlı işlenecek parça sayısı. 1 → sıralı (eski) davranış.
        self._max_workers = max(1, max_workers)
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
        spans: list[BlockSpan] | None = None,
    ) -> AnalysisResult:
        """Uzun belgeyi kademeli geçişlerle inceler.

        Yerel ve ton geçişleri parça parça (offset rebasing ile); tutarlılık geçişi
        bütün belgede bir kez. Tüm bulgular tek listede toplanır.

        İsteğe bağlı `progress` callback'i her adımda bir `ProgressEvent` alır
        (web paneli/CLI canlı geri bildirim için); `None` ise davranış değişmez.

        İsteğe bağlı `spans` (bkz. `extract.extract_docx_blocks`) blok türlerini
        taşır; verilirse yapısal gürültü deterministik olarak süzülür:
        - tablo hücrelerine ve İçindekiler (TOC) satırlarına düşen imla/dil
          bilgisi/ton bulguları elenir (ikisi de düzyazı değildir; TOC üretilmiş
          metindir, başlığın kendisi gövdede zaten denetlenir); tutarlılık
          bulguları korunur,
        - yalnız tablo/İçindekiler verisi içeren parçalar yerel/ton geçişine hiç
          gönderilmez (API tasarrufu),
        - başlık bloklarındaki tekrar/noktalama bulguları elenir (başlıklar cümle
          noktalaması izlemez; tekrarları da çoğu kez dönüştürme artığıdır),
        - tablodaki ondalık-nokta kullanımı tek tek değil, belge-geneli TEK özet
          bulguyla raporlanır (bkz. `_decimal_summary`).
        `spans=None` → süzme yok (düz metin girdisi, eski davranış).

        Parçalar `max_workers` kadar EŞZAMANLI işlenir (LLM çağrıları ağ-bağımlı;
        paralellik toplam süreyi kısaltır). Çıktı parçaların işlenme sırasından
        BAĞIMSIZ: `_finalize` deterministik sıralayıp tekilleştirir, böylece
        `max_workers` ne olursa olsun sonuç birebir aynıdır. `max_workers == 1`
        tamamen sıralı (eski) davranıştır.
        """
        table_ranges = [(s.start, s.end) for s in (spans or []) if s.kind == "tablo_hucresi"]
        heading_ranges = [(s.start, s.end) for s in (spans or []) if s.kind == "baslik"]
        # Tablo + İçindekiler: ikisi de düzyazı denetimi dışı (tek listede, blok
        # sırası korunur — `_covered_by_ranges` artan sıra bekler). Ondalık
        # özeti (`_decimal_summary`) ise YALNIZ gerçek tablo aralıklarında
        # çalışır; TOC sayfa numaraları ondalık veri değildir.
        drop_ranges = [
            (s.start, s.end) for s in (spans or [])
            if s.kind in ("tablo_hucresi", "icindekiler")
        ]

        chunks = chunk_text(text, max_chars=max_chars)
        total = len(chunks)
        emit(progress, ProgressEvent("chunk", f"Belge {total} parçaya bölündü", 0, total))

        # İlerleme yayını thread-safe olmalı: paralelde parça-işçileri aynı anda
        # "başladı/bitti" olayı yayar; callback (web SSE yazarı) thread-safe
        # olmayabilir, bu yüzden emit'i kilitle serileştiriyoruz.
        progress_lock = threading.Lock()

        def emit_safe(event: ProgressEvent) -> None:
            with progress_lock:
                emit(progress, event)

        def chunk_worker(index: int, chunk) -> list[Finding]:
            # Parça başına İKİ olay: işçi parçayı ALDIĞINDA "chunk_start", BİTİRDİĞİNDE
            # "chunk_done". `index` parçanın kararlı kimliği (1 tabanlı); arayüz bununla
            # her parçayı ayrı satır/hücre olarak gösterip aynı anda kaçının işlendiğini
            # canlı izleyebilir.
            emit_safe(ProgressEvent(
                "chunk_start", f"Parça {index}/{total} inceleniyor", index, total))
            if _covered_by_ranges(text, chunk.start, chunk.end, drop_ranges):
                # Parça yalnız tablo/İçindekiler verisi: düzyazı denetimi
                # anlamsız, LLM'e gönderme (tablo değerlerini tutarlılık geçişi
                # zaten görüyor; TOC başlıkları gövdede zaten denetleniyor).
                emit_safe(ProgressEvent(
                    "chunk_done",
                    f"Parça {index}/{total} tablo/içindekiler verisi — dil denetimi atlandı",
                    index, total))
                return []
            out = self._chunk_pass(chunk)
            emit_safe(ProgressEvent(
                "chunk_done", f"Parça {index}/{total} tamamlandı", index, total))
            return out

        def consistency_worker() -> list[Finding]:
            emit_safe(ProgressEvent(
                "consistency_start", "Belge geneli tutarlılık inceleniyor", total, total))
            out = self._consistency_pass(text)
            emit_safe(ProgressEvent(
                "consistency_done", "Belge geneli tutarlılık tamamlandı", total, total))
            return out

        findings: list[Finding] = []

        if self._max_workers <= 1:
            # Sıralı referans yol: deterministik; eval/hata ayıklama/karşılaştırma.
            for index, chunk in enumerate(chunks, start=1):
                findings.extend(chunk_worker(index, chunk))
            findings += consistency_worker()
        else:
            findings_lock = threading.Lock()
            with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
                # Tutarlılık çağrısı (bütün belge) en uzun süren tek iştir; onu İLK
                # gönderiyoruz ki bir işçiyi baştan tutup parça işleriyle örtüşsün
                # (toplam süre ≈ max(tutarlılık, parça dalgaları)).
                futures = {pool.submit(consistency_worker)}
                futures |= {
                    pool.submit(chunk_worker, index, chunk)
                    for index, chunk in enumerate(chunks, start=1)
                }
                for fut in as_completed(futures):
                    res = fut.result()  # hata olduğu gibi yükselir → "hata çıkarsa dur"
                    with findings_lock:
                        findings.extend(res)

        emit(progress, ProgressEvent(
            "finalize", "Bulgular birleştiriliyor ve sıralanıyor", total, total))
        # Yapısal süzme + ondalık özeti DETERMİNİSTİK adımlardır ve sıralama/
        # tekilleştirmeden ÖNCE uygulanır → çıktı max_workers'tan bağımsız kalır.
        if drop_ranges or heading_ranges:
            findings = _drop_structural_noise(findings, drop_ranges, heading_ranges)
            findings += _decimal_summary(text, table_ranges)
        result = self._finalize(findings, text)
        emit(progress, ProgressEvent("done", "Analiz tamamlandı", total, total))
        return result

    def _chunk_pass(self, chunk) -> list[Finding]:
        """Tek parça için yerel + ton geçişi; offsetleri kaynağa taşır (rebasing).

        Saf: yalnız o parçanın bulgu listesini döndürür (paylaşılan duruma yazmaz),
        böylece paralel çağrılabilir. Offset rebasing burada yapılır.
        """
        out: list[Finding] = []
        for finding in self._local_pass(chunk.text) + self._tone_pass(chunk.text):
            if finding.start is not None:
                finding.start += chunk.start
            if finding.end is not None:
                finding.end += chunk.start
            out.append(finding)
        return out

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
        """Tüm geçişlerin bulgularını sıralar, tekilleştirir ve doğrular.

        ÖNCE konumlanamayan (kaynakta bulunamayan, muhtemelen halüsinasyon)
        VE bağlamca zaten karşılanmış (öneri kaynakta alıntının hemen
        ardında zaten var olan) bulgular elenir, SONRA deterministik
        (tam-sıra) sıralama, SONRA tekilleştirme yapılır: böylece hem nihai
        sıra hem de tekilleştirmede "ilk korunan" kayıt, parçaların paralel
        işlenme/toplanma sırasından BAĞIMSIZ olur — çıktı `max_workers`
        değerinden etkilenmez (birebir aynı).
        """
        located = drop_unlocated_findings(findings)
        located = drop_context_satisfied_findings(located, text)
        ordered = sorted(located, key=_sort_key)
        result = AnalysisResult(findings=_dedup(ordered))
        result.model_id = self._model_id
        result.text_len = len(text)
        # Bozuk öneri koruması (örn. "birçok" → "birchoq"): otomatik uygulamada
        # veriyi bozacak önerileri eler.
        validate_suggestions(result)
        return result

    @staticmethod
    def _resolve_spelling(
        candidates: list[Finding], decisions: list[LLMSpellingDecision]
    ) -> list[Finding]:
        """Hunspell adaylarını Gemini kararlarıyla birleştirir.

        - Gemini "hata değil" dediyse (özel ad/terim) aday elenir.
        - "hata" + düzeltme verdiyse öneri, alıntının harf düzenine (case)
          giydirilerek uygulanır ("SEÇENEKLERI" → "SEÇENEKLERİ", "seçenekleri"
          değil).
        - Gemini bu adaya dair karar vermediyse: tespit kaybolmasın diye bulgu
          "öneri yok" yer tutucusuyla korunur (Hunspell artık kendi önerisini
          ÜRETMEZ — bkz. spell.py görev ayrımı).
        """
        # İKİ ayrı geçiş: önce TÜM tam eşleşmeler kaydedilir, SONRA casefold
        # fallback'i yalnız boş kalan anahtarlar için eklenir. Tek geçişte
        # (tam eşleşme + casefold aynı anda) yapılırsa, örn. "Herşey" önce
        # işlenince onun casefold'u ("herşey") kendi asıl kararı ("herşey"
        # adayının kararı) sırası gelmeden ÖNCE işgal eder — o zaman "herşey"
        # candidate'ı yanlışlıkla "Herşey"in kararını (büyük harfli) alır.
        by_word: dict[str, LLMSpellingDecision] = {}
        for d in decisions:
            by_word.setdefault(d.word, d)
        for d in decisions:
            by_word.setdefault(d.word.casefold(), d)

        resolved: list[Finding] = []
        for c in candidates:
            d = by_word.get(c.excerpt) or by_word.get(c.excerpt.casefold())
            if d is None:
                resolved.append(c)  # fallback: tespiti koru (öneri yer tutucu kalır)
                continue
            if not d.is_error:
                continue  # Gemini: geçerli kullanım, ele
            correction = d.correction.strip()
            if correction:
                c.suggestion = match_case(c.excerpt, correction)
            resolved.append(c)
        return resolved

    def _invoke_cached(self, system_prompt: str, user_message: str) -> LLMAnalysis:
        key = make_key(self._model_id or "", system_prompt, user_message)
        if self._cache is not None:
            hit = self._cache.get(key)
            if hit is not None:
                return LLMAnalysis.model_validate_json(hit)

        try:
            raw: LLMAnalysis = self._structured.invoke(
                [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]
            )
        except Exception as exc:  # noqa: BLE001 — kullanıcıya okunur hata göster
            raise LLMCallError(
                f"Gemini API'ye ulaşılamadı (zaman aşımı veya bağlantı hatası): {exc}. "
                "Bağlantıyı kontrol edin; kurumsal ağdaysanız "
                "GOOGLE_GENAI_TRANSPORT=rest deneyin."
            ) from exc

        if self._cache is not None:
            self._cache.set(key, raw.model_dump_json())
        return raw


def _sort_key(f: Finding) -> tuple:
    """Bulgular için tam-sıra (deterministik) anahtar.

    Yalnız offset'e göre sıralamak, aynı konumdaki bulguların görece sırasını
    ekleme sırasına (paralelde sırasız) bırakır. Tüm ayırt edici alanları
    anahtara katarak sıralamayı işlenme sırasından bağımsız kılıyoruz.
    Konumsuz bulgular (start=None) sona alınır.
    """
    return (
        f.start is None,
        f.start if f.start is not None else 0,
        f.end if f.end is not None else 0,
        f.type.value,
        f.excerpt,
        f.suggestion,
        f.explanation,
    )


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


# --- Yapısal süzme (etiketli bloklar) ----------------------------------------
# Bu adımlar tamamen deterministiktir (LLM yok): extract'ın blok türü haritasına
# dayanarak tablo/başlık kaynaklı yapay bulguları eler ve tablo ondalıklarını
# tek özet bulguya indirir. Hepsi _finalize'ın sıralama/tekilleştirmesinden ÖNCE
# çalışır; determinizm sözleşmesi korunur.

# Tablo hücresinde ondalık NOKTA kullanımı (örn. "446.00625").
_DECIMAL_DOT = re.compile(r"\d+\.\d+")

# Başlıklarda elenecek yapısal kural kimlikleri: başlık cümle noktalaması
# izlemez; ardışık başlık tekrarı da yazarın değil dönüştürmenin ürünüdür.
_HEADING_NOISE_RULES = frozenset({"GRAMER-TEKRAR", "IMLA-NOKTALAMA"})


def _covered_by_ranges(
    text: str, start: int, end: int, ranges: list[tuple[int, int]]
) -> bool:
    """`text[start:end]`'in boşluk-dışı TAMAMI verilen aralıklar içinde mi?

    Parçalar blokları "\\n\\n" ayıraçlarıyla birlikte kapsar; ayıraçlar boşluk
    olduğundan yalnız tablo bloklarından oluşan bir parça True döner.
    """
    if not ranges:
        return False
    pos = start
    for r_start, r_end in ranges:  # aralıklar blok sırasında (artan) gelir
        if r_end <= pos:
            continue
        if r_start >= end:
            break
        if text[pos:min(r_start, end)].strip():
            return False  # aralık öncesinde tablo-dışı içerik var
        pos = max(pos, r_end)
        if pos >= end:
            return True
    return not text[pos:end].strip()


def _overlaps_any(f: Finding, ranges: list[tuple[int, int]]) -> bool:
    if f.start is None or f.end is None:
        return False
    return any(f.start < r_end and r_start < f.end for r_start, r_end in ranges)


def _drop_structural_noise(
    findings: list[Finding],
    drop_ranges: list[tuple[int, int]],
    heading_ranges: list[tuple[int, int]],
) -> list[Finding]:
    """Tablo/İçindekiler/başlık bloklarına düşen yapay bulguları eler.

    - Tablo hücresi + İçindekiler satırı (`drop_ranges`): imla/dil bilgisi/ton
      bulguları elenir (ikisi de düzyazı değildir; ondalıklar `_decimal_summary`
      ile toplu raporlanır). Tutarlılık bulguları KORUNUR — birim yazımı
      çakışması (Khz↔kHz) tabloda da geçerli.
    - Başlık: yalnız `_HEADING_NOISE_RULES` bulguları elenir; başlıktaki gerçek
      yazım hatası (örn. "SINIRLIİ") yakalanmaya devam eder.
    """
    out: list[Finding] = []
    for f in findings:
        if f.type != FindingType.TUTARLILIK and _overlaps_any(f, drop_ranges):
            continue
        if f.rule_id in _HEADING_NOISE_RULES and _overlaps_any(f, heading_ranges):
            continue
        out.append(f)
    return out


def _decimal_summary(text: str, table_ranges: list[tuple[int, int]]) -> list[Finding]:
    """Tablo bloklarındaki ondalık-nokta kullanımını TEK özet bulguya indirir.

    Kural (IMLA-BIRIM) ondalık ayracın virgül olmasını ister; ama bir frekans
    çizelgesindeki her hücre için ayrı bulgu üretmek raporu boğar (60 sayfalık
    denemede 40 bulgu). N ≥ 3 ise tek `tutarlilik` bulgusu üretilir; N < 3 ise
    hiç üretilmez (tek tük değer düzyazı geçişinin işi).
    """
    hits: list[tuple[int, int, str]] = []
    for r_start, r_end in table_ranges:
        for m in _DECIMAL_DOT.finditer(text, r_start, r_end):
            hits.append((m.start(), m.end(), m.group(0)))
    if len(hits) < 3:
        return []
    first_start, first_end, first_text = hits[0]
    return [
        Finding(
            type=FindingType.TUTARLILIK,
            excerpt=first_text,
            explanation=(
                f"Belge genelinde tablo değerlerinde ondalık ayraç olarak nokta "
                f"kullanılmış ({len(hits)} yerde); TDK'ya göre ondalık ayraç "
                f"virgüldür. Tek tek işaretlemek yerine toplu bildirilmiştir."
            ),
            suggestion=first_text.replace(".", ","),
            rule_id="IMLA-BIRIM",
            start=first_start,
            end=first_end,
        )
    ]


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
        max_workers=settings.max_workers,
    )
