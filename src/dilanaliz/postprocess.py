"""Bulgu son-işleme (deterministik temizlik).

LLM bazen "hata var" deyip `suggestion`'ı `excerpt` ile birebir aynı veriyor
(örn. "Ben de" → "Ben de"). Bu, değiştirilecek bir şey olmadığı anlamına gelir:
gerçek bir düzeltme değil, yanlış pozitiftir. Bu tür bulguları deterministik
olarak eleriz. Bu, özellikle de/da ve ki üzerindeki aşırı tetiklenmeyi azaltır.

Normalleştirme HAFİF tutulur (baş/son boşluk + iç boşluk daraltma); noktalama
KORUNUR, çünkü "yalnız mı" → "yalnız mı?" gerçek bir düzeltmedir.
"""

from __future__ import annotations

import unicodedata

from .schema import AnalysisResult, Finding

# Türkçe alfabede bulunmayan harfler. Öneride bunlar varken ALINTIDA yoksa, öneri
# büyük olasılıkla bozulmuştur (örn. "birçok" → "birchoq") → güvenilmez sayılır.
_NON_TURKISH = set("qwxQWX")

# Türkçe yazımda hiç kullanılmayan işaretler. Model bazen kesme işareti yerine
# backtick üretir (örn. "Modu'na" → "Modu`na") — geçersiz, uygulanamaz öneri.
# ALINTIDA yoksa (yani öneri onu SONRADAN eklemişse) bozuk sayılır; aynı mantık
# _NON_TURKISH ile — ayrı kümede çünkü harf değil işarettir.
_INVALID_PUNCT = set("`")

# Tırnak/kesme eşdeğerlikleri: Word "akıllı tırnak" üretir (’ “ ”), LLM çoğu kez
# düz ASCII döndürür (' "). İkisi görsel olarak aynı işlevi görür; normalize
# edilmeden karşılaştırılırsa "ALKALINE'den" → "ALKALINE’den" gibi hiçbir şey
# değiştirmeyen öneriler noop sayılmaz ve rapora sızar.
_QUOTE_TRANS = str.maketrans({
    "’": "'", "‘": "'", "‚": "'", "ʼ": "'",
    "“": '"', "”": '"', "„": '"',
})


def _norm(s: str) -> str:
    # NFC normalizasyonu: Türkçe "î/â/ê" gibi harfler tek kod noktası (NFC)
    # veya harf+bileşik-işaret (NFD) olarak gelebilir; ikisi görsel olarak
    # aynıdır ama normalize edilmeden karşılaştırılırsa eşit sayılmaz.
    # Tırnak çeşitleri de tek biçime indirilir (yukarıya bak).
    s = unicodedata.normalize("NFC", s).translate(_QUOTE_TRANS)
    return " ".join(s.split())


def is_noop_suggestion(excerpt: str, suggestion: str) -> bool:
    """Öneri, alıntıyla anlamlı bir fark taşımıyorsa True."""
    return _norm(excerpt) == _norm(suggestion)


def drop_noop_findings(result: AnalysisResult) -> AnalysisResult:
    """Önerisi alıntıyla aynı olan bulguları çıkarır (yerinde)."""
    result.findings = [
        f for f in result.findings if not is_noop_suggestion(f.excerpt, f.suggestion)
    ]
    return result


def _suggestion_is_corrupt(excerpt: str, suggestion: str) -> bool:
    """Öneri, alıntıda olmayan Türkçe-dışı harf (q/w/x) veya geçersiz işaret
    (backtick) içeriyorsa True."""
    extra = set(suggestion) - set(excerpt)
    return bool(extra & _NON_TURKISH) or bool(extra & _INVALID_PUNCT)


def validate_suggestions(result: AnalysisResult) -> AnalysisResult:
    """Bozuk öneri içeren bulguları eler (yerinde).

    Model bazen yakaladığı bir hataya geçersiz/ASCII'leştirilmiş öneri üretir
    (örn. "birçok" yerine "birchoq"). Böyle bir öneri otomatik uygulanırsa metni
    bozar; kaçırmaktan daha tehlikelidir. Bu yüzden güvenilmez kabul edilip atılır.
    """
    result.findings = [
        f
        for f in result.findings
        if not _suggestion_is_corrupt(f.excerpt, f.suggestion)
    ]
    return result


def drop_context_satisfied_findings(findings: list[Finding], source: str) -> list[Finding]:
    """Öneri, alıntının kaynaktaki HEMEN ARDINDAN gelen karakterleriyle zaten
    karşılanıyorsa eler (bulgu offsetli olmalı — bu yüzden `enrich_with_offsets`
    SONRASI çağrılmalıdır).

    Örnek: cümle zaten "...sunuyoruz." diye bitmişken, model alıntı sınırını
    noktadan ÖNCE keser ("sunuyoruz") ve "sunuyoruz." öneririr — nokta
    kaynakta zaten alıntının hemen ardında duruyor, öneri hiçbir şeyi
    değiştirmiyor. `is_noop_suggestion` bunu yakalayamaz çünkü yalnız
    excerpt/suggestion metnini karşılaştırır, kaynak bağlamına bakmaz.
    """
    out: list[Finding] = []
    for f in findings:
        if (
            f.start is not None
            and f.end is not None
            and f.suggestion.startswith(f.excerpt)
            and len(f.suggestion) > len(f.excerpt)
        ):
            extra = f.suggestion[len(f.excerpt):]
            if source[f.end : f.end + len(extra)] == extra:
                continue  # öneri kaynakta zaten var — sahte düzeltme
        out.append(f)
    return out


def drop_unlocated_findings(findings: list[Finding]) -> list[Finding]:
    """Kaynakta konumlanamayan (start/end=None) bulguları eler.

    `locate.py` bir alıntıyı kaynakta (birebir veya boşluk/tırnak-normalize)
    bulamazsa offseti None bırakır. Bu, LLM'in kaynakta OLMAYAN bir alıntı
    ürettiği (genelde DİL KURALLARI'ndaki "Yanlış:" örneğini kaynaktaki DOĞRU
    yazılmış hâliyle karıştırması) anlamına gelir — kullanıcıya belgede
    hiç geçmeyen bir "hata"yı düzeltme olarak sunmamak için sessizce atılır.
    """
    return [f for f in findings if f.start is not None and f.end is not None]


def _spans_overlap(a: Finding, b: Finding) -> bool:
    if None in (a.start, a.end, b.start, b.end):
        return False
    return a.start < b.end and b.start < a.end


# Çapraz-geçiş tip-kopyası önceliği: aynı hata iki geçişten iki tip etiketiyle
# gelirse (örn. "zamanı aşınır" hem dil_bilgisi hem ton) daha SOMUT eksen
# kazanır. tutarlilik bu sıraya DAHİL DEĞİLDİR — belge-geneli çakışma iddiası
# yerel bulgunun kopyası değil, ayrı bir bilgidir (korunur).
_TYPE_PRIORITY = {"imla": 0, "dil_bilgisi": 1, "ton": 2}

# Kelime sonu noktalama: atomik düzeltme karşılaştırmasında yok sayılır (bir
# geçiş "sundular." bir geçiş "sundular" diye alıntılayabilir — aynı kelime).
_TRAILING_PUNCT = ".,!?;:'\"”’"


def _atomic_correction(excerpt: str, suggestion: str) -> tuple[str, str] | None:
    """Alıntı ile öneri arasındaki TEK kelime farkını (önce, sonra) döndürür.

    Kelime sayıları eşit değilse veya fark sayısı 1'den farklıysa (0 veya
    birden çok kelime değişmişse) None döner — bu durumda iki bulgunun AYNI
    düzeltmeyi mi yaptığı güvenilir biçimde karşılaştırılamaz (örn. tam cümle
    yeniden yazımı gibi çok-kelimeli öneriler).
    """
    exc_words = [w.rstrip(_TRAILING_PUNCT) for w in _norm(excerpt).split(" ")]
    sug_words = [w.rstrip(_TRAILING_PUNCT) for w in _norm(suggestion).split(" ")]
    if len(exc_words) != len(sug_words):
        return None
    diffs = [(a, b) for a, b in zip(exc_words, sug_words) if a != b]
    if len(diffs) != 1:
        return None
    return diffs[0]


def drop_cross_pass_duplicates(findings: list[Finding]) -> list[Finding]:
    """Örtüşen konum + (aynı alıntı YA DA aynı atomik düzeltme) taşıyan FARKLI
    tipteki bulguları tip önceliğiyle (imla > dil_bilgisi > ton) teke indirir.

    Geçişler birbirini görmediğinden aynı ifade iki geçişten iki ayrı bulgu
    olarak gelebilir; rapor aynı hatayı iki satır gösterir. İki eşleşme yolu
    vardır: (1) alıntılar birebir aynı (örn. ikisi de "zamanı aşınır"), (2)
    alıntılar FARKLI ama İKİSİ DE AYNI kelimeyi aynı biçimde düzeltiyor (örn.
    dil_bilgisi bulgusu tüm cümleyi alıntılarken "sundular"→"sunuldu" öneriyor,
    ton bulgusu yalnız "sundular" kelimesini alıntılayıp AYNI düzeltmeyi
    öneriyor — `_atomic_correction` bu iki bulgunun aynı hatayı hedeflediğini
    kelime-farkı üzerinden tespit eder). Atomik düzeltme çıkarılamayan (çok
    kelimeli/serbest yeniden yazım) bulgular yalnız (1) yoluyla karşılaştırılır
    — böylece örtüşen ama GERÇEKTEN FARKLI iddialar (örn. aynı kelimeye farklı
    gerekçelerle işaret eden iki ayrı bulgu) yanlışlıkla birleştirilmez.

    Aynı-tip birebir kopyaları `_dedup` (analyzer) zaten eler; bu fonksiyon
    yalnız TİP FARKLI kopyaları hedefler. `tutarlilik` tipi elemeye de
    elenmeye de girmez. Deterministiktir: karşılaştırma konum+içeriğe, seçim
    sabit önceliğe dayanır; girdi sırasından bağımsızdır.
    """
    corrections = {
        id(f): _atomic_correction(f.excerpt, f.suggestion) for f in findings
    }
    out: list[Finding] = []
    for f in findings:
        if f.type.value not in _TYPE_PRIORITY:
            out.append(f)
            continue
        f_correction = corrections[id(f)]
        superseded = False
        for other in findings:
            if other is f or other.type == f.type:
                continue
            if other.type.value not in _TYPE_PRIORITY:
                continue
            if not _spans_overlap(f, other):
                continue
            same_excerpt = _norm(other.excerpt) == _norm(f.excerpt)
            same_correction = (
                f_correction is not None and f_correction == corrections[id(other)]
            )
            if not (same_excerpt or same_correction):
                continue
            if _TYPE_PRIORITY[other.type.value] < _TYPE_PRIORITY[f.type.value]:
                superseded = True  # daha öncelikli tip aynı hatayı taşıyor
                break
        if not superseded:
            out.append(f)
    return out


def merge_findings(
    deterministic: list[Finding], llm: list[Finding]
) -> list[Finding]:
    """Deterministik (Hunspell) ve LLM bulgularını birleştirir.

    Deterministik bulgular her zaman korunur (sözlük temelli, uydurma yok). Aynı
    bölgeye denk gelen (çakışan) LLM bulguları elenir — deterministik olan tercih
    edilir. Konumsuz LLM bulguları (offset yok) karşılaştırılamaz, korunur.
    Sonuç başlangıç offsetine göre sıralanır (konumsuzlar sona).
    """
    merged = list(deterministic)
    for f in llm:
        if any(_spans_overlap(f, d) for d in deterministic):
            continue
        merged.append(f)
    merged.sort(key=lambda x: (x.start is None, x.start if x.start is not None else 0))
    return merged
