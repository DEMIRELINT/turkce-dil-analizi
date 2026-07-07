"""Yapılandırılmış çıktı şeması.

LLM çıktısı `with_structured_output(AnalysisResult)` ile bu modellere bağlanır;
böylece parse hatası ortadan kalkar. Offset alanları (start/end) LLM tarafından
DOLDURULMAZ — sonradan `locate.py` ile kaynak metinden hesaplanır.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class FindingType(str, Enum):
    """Bulgunun ait olduğu analiz ekseni."""

    IMLA = "imla"
    DIL_BILGISI = "dil_bilgisi"
    TON = "ton"
    # Belge-geneli tutarlılık: aynı terim/birim/kısaltmanın farklı yazılması.
    # Yalnız bütün-belge geçişinde üretilir (tek chunk göremez).
    TUTARLILIK = "tutarlilik"


class Finding(BaseModel):
    """Tek bir tespit: hata tipi, alıntı, gerekçe ve öneri."""

    type: FindingType = Field(description="Bulgunun ekseni: imla, dil_bilgisi veya ton")
    excerpt: str = Field(
        description="Metinden BİREBİR alınan, soruna konu olan en kısa alıntı"
    )
    explanation: str = Field(description="Sorunun kısa ve net gerekçesi")
    suggestion: str = Field(description="Önerilen düzeltme (uygulanması kullanıcıya bırakılır)")
    rule_id: str | None = Field(
        default=None, description="Tetikleyen kuralın kimliği (varsa)"
    )
    confidence: float | None = Field(
        default=None, ge=0.0, le=1.0, description="0-1 arası güven (opsiyonel)"
    )

    # locate.py tarafından doldurulur; LLM bunları üretmez.
    start: int | None = Field(default=None, description="Kaynak metindeki başlangıç offseti")
    end: int | None = Field(default=None, description="Kaynak metindeki bitiş offseti")


class Observation(BaseModel):
    """Doğrulanmamış gözlem: modelin kurala bağlayamadığı ama şüphelendiği yer.

    Bir bulgu (`Finding`) DEĞİLDİR — kesinlik iddiası taşımaz, düzeltme önerisi
    yoktur. `findings` boru hattından (offset/eleme/tekilleştirme) tamamen ayrı
    bir kanaldır; kullanıcıya "editör değerlendirmesi gerekir" etiketiyle ayrı
    gösterilir ve precision/recall ölçümüne GİRMEZ (bkz. analyzer._finalize).
    """

    excerpt: str = Field(description="Şüphe uyandıran, metinden BİREBİR alıntı")
    note: str = Field(description="Neden şüphelenildiğinin kısa gerekçesi (öneri değil)")


class AnalysisResult(BaseModel):
    """Bir metnin analiz sonucu: bulgu listesi + gözlemler + üstveri."""

    findings: list[Finding] = Field(default_factory=list)
    # Doğrulanmamış gözlemler — findings'ten AYRI kanal (bkz. Observation).
    observations: list[Observation] = Field(default_factory=list)

    # Üstveri analyzer tarafından doldurulur (LLM şemasında zorunlu değil).
    model_id: str | None = Field(default=None)
    text_len: int | None = Field(default=None)


# --- LLM-yüzlü şemalar -------------------------------------------------------
# LLM yalnız aşağıdaki alanları üretir. Offset (start/end) ve üstveri
# (model_id, text_len) sonradan analyzer/locate tarafından eklenir; bunları
# modele göstermeyiz ki dikkati dağılmasın ve uydurma offset üretmesin.


class LLMFinding(BaseModel):
    """LLM'in döndürdüğü ham bulgu (offset/üstveri içermez)."""

    type: FindingType = Field(description="Bulgunun ekseni: imla, dil_bilgisi veya ton")
    excerpt: str = Field(
        description="Metinden BİREBİR alınan, soruna konu olan en kısa alıntı"
    )
    explanation: str = Field(description="Sorunun kısa ve net gerekçesi")
    suggestion: str = Field(description="Önerilen düzeltme")
    rule_id: str | None = Field(default=None, description="Tetikleyen kuralın kimliği (varsa)")
    confidence: float | None = Field(default=None, description="0-1 arası güven (opsiyonel)")


class LLMSpellingDecision(BaseModel):
    """Yazım denetçisinin (Hunspell) işaretlediği şüpheli kelime için LLM kararı.

    LLM her aday kelimeyi bağlama göre değerlendirir: gerçek hata mı, yoksa özel
    ad/teknik terim gibi geçerli bir kullanım mı? Hataysa cümleye uygun doğru
    biçimi verir.
    """

    word: str = Field(description="Değerlendirilen aday kelime (birebir)")
    is_error: bool = Field(description="Gerçek yazım hatası mı? Özel ad/terim ise False")
    correction: str = Field(
        default="", description="Hata ise cümleye uygun doğru biçim; değilse boş"
    )


class TermEntry(BaseModel):
    """Tutarlılık için parçadan çıkarılan tek terim (map adımı çıktısı).

    Yalnız SABİT ad/terim/kısaltma/birim/arayüz-etiketi niteliğindeki ifadeler
    çıkarılır; serbest/betimleyici ifadeler DEĞİL (bkz. terim≠serbest ayrımı).
    Offset yoktur — reduce adımının ürettiği bulgular sonradan `locate.py` ile
    konumlanır (LLM offset üretmez sözleşmesi korunur).
    """

    surface: str = Field(
        description="Terimin metinde GEÇTİĞİ BİREBİR yüzey biçimi (harfi harfine)"
    )
    concept: str = Field(
        description=(
            "Terimin bağlamdan anlaşılan KISA kavram karşılığı (ne olduğu). "
            "Farklı yüzey biçimleri aynı kavrama işaret ediyorsa reduce adımı "
            "bunu kullanarak çakışmayı yakalar. Örn. 'BK' → 'posta idaresi'."
        )
    )


class LLMTermExtraction(BaseModel):
    """Terim çıkarımı (map) geçişinin `with_structured_output` kök şeması.

    Tutarlılık map-reduce'unun map adımında her parça için ayrı çağrılır; küçük
    ve sınırlı bir çıktıdır (parçadaki terimler). Reduce adımı bu indeksi görür,
    ham metnin tamamını değil — böylece tek dev çağrının zaman aşımı tavanı kalkar.
    """

    terms: list[TermEntry] = Field(
        default_factory=list,
        description="Bu parçada geçen sabit terim/kısaltma/birim/etiketler",
    )


class LLMAnalysis(BaseModel):
    """LLM'in `with_structured_output` ile bağlandığı kök şema."""

    findings: list[LLMFinding] = Field(default_factory=list)
    spelling: list[LLMSpellingDecision] = Field(
        default_factory=list,
        description="Yazım denetçisinin işaretlediği adaylar için kararlar",
    )
    observations: list[Observation] = Field(
        default_factory=list,
        description=(
            "Kurala bağlanamayan ama şüphelenilen yerler (doğrulanmamış gözlem). "
            "Bir bulgu DEĞİLDİR; yalnız yerel geçiş doldurur, ton/tutarlılık boş bırakır."
        ),
    )

    def to_result(self) -> AnalysisResult:
        """Ham LLM çıktısını zenginleştirilebilir public modele dönüştürür."""
        return AnalysisResult(
            findings=[
                Finding(
                    type=f.type,
                    excerpt=f.excerpt,
                    explanation=f.explanation,
                    suggestion=f.suggestion,
                    rule_id=f.rule_id,
                    confidence=f.confidence,
                )
                for f in self.findings
            ],
            observations=list(self.observations),
        )
