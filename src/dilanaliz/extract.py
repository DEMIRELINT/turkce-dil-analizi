"""Belge → temiz metin çıkarma (girdi katmanı, ETİKETLİ bloklar).

`.docx` dosyasından metni belge **sırasını koruyarak** ve **eksiksiz** okur:
gövde paragrafları, **tablo hücreleri**, **metin kutuları/şekiller**,
**üst/altbilgiler** ve **dipnot/sonnotlar** dahil. Bloklar ÇİFT satır sonu ile
birleşir; böylece downstream parçalama (`chunk.py`) paragrafları boş-satır
sınırından ayırabilir.

Her blok bir TÜR etiketi taşır (`paragraf` / `baslik` / `tablo_hucresi`).
Downstream analiz (analyzer) bu etiketlerle tablo verisini imla denetiminden,
başlıkları da yapısal (tekrar/noktalama) denetimden muaf tutar — düz-metin
çorbasında "bu neydi?" tahmini yerine kaynağında kesin bilgi.

Neden `docx2python`? En yaygın `python-docx`, belgenin yalnız normal gövde
paragraflarını okur; tablo, metin kutusu, üst/altbilgi ve dipnotları SESSİZCE
atlar. 50+ sayfalık kurumsal belgelerde metnin çoğu bu öğelerde olduğundan,
atlanan içeriği minimuma indirmek için `docx2python` kullanılır. Tamamen
yereldir (ağ erişimi yok → air-gap uyumlu).

Çözülemeyen tek artık: **görsel içindeki yazı** (resim olarak gömülü metin). Bu
yalnız OCR ile çıkarılır ve kapsam dışıdır; ancak `ExtractionReport` ile kaç
görsel bulunduğu raporlanır, böylece bu atlama SESSİZ kalmaz, kullanıcıya
görünür olur.

PDF çıkarma bilinçli olarak buraya KONMADI: PDF'te çok sütunlu düzen, araya giren
görsel ve satır kırılmaları metni bozar; güvenilir yol, kaynağı Word olarak alıp
buradan geçirmektir. (PDF'ten Word'e çevrilmiş belgelerde dahi metin kutusu
kırpıntıları ve tekrar eden sayfa başlıkları kalabilir; aşağıdaki temizlik
adımları bu artıkları azaltır ama sıfırlayamaz.)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

# İki bloğu ayıran sınır; chunk.py ile tutarlı olmalı.
_PARAGRAPH_SEP = "\n\n"

# docx2python, gövde akışındaki bir görselin yerine "----media/image1.png----"
# gibi bir yer tutucu metin koyar. Bu, analiz metnine gürültü katmasın diye
# elenir (görseller ayrıca ExtractionReport.images ile raporlanır).
# İKİ biçim görülür: (1) tek başına bir satır; (2) metne YAPIŞIK ve/veya art
# arda zincirlenmiş ("----media/a.png--------media/b.png----Metin"). Tam-satır
# regex'i (2)'yi kaçırdığından, satır-İÇİ eşleşen ayrı bir desen de kullanılır.
_IMAGE_MARKER = re.compile(r"^-{2,}media/\S+-{2,}$")
# Satır-içi biçim ZİNCİR olarak da gelir ("----media/a.png--------media/b.png----");
# tek tek eşleşen desende sondaki tire dizisi bir sonraki işaretçinin baş
# tirelerini yutar ve ikinci işaretçi sızar. Bu yüzden desen zinciri BÜTÜN
# olarak yakalar: (tireler + media/dosyaadı) bir+ kez, sonda kapanış tireleri.
_IMAGE_MARKER_INLINE = re.compile(r"(?:-{2,}media/[\w.]+(?:-[\w.]+)*)+-{2,}")

# Blok türü: analiz katmanının denetim kapsamını belirler.
BlockKind = Literal["paragraf", "baslik", "tablo_hucresi"]


@dataclass(frozen=True)
class BlockSpan:
    """Birleşik metindeki bir bloğun aralığı ve türü.

    `start`/`end`, `extract_docx_blocks`'un döndürdüğü birleşik metin
    üzerindeki offsetlerdir (`text[start:end]` bloğun kendisidir); analiz
    bulgu offsetleriyle DOĞRUDAN karşılaştırılabilir.
    """

    start: int
    end: int
    kind: BlockKind


@dataclass(frozen=True)
class ExtractionReport:
    """Çıkarmanın özeti — neyin okunduğunu ve neyin OKUNAMADIĞINI görünür kılar.

    Asıl amaç: görsel içi yazı gibi çözülemeyen atlamaları kullanıcıya bildirmek
    (sessiz veri kaybını önlemek).
    """

    paragraphs: int          # toplam metin bloğu (gövde + tablo + ek bölümler)
    tables: int              # okunan tablo sayısı
    images: int              # gömülü görsel sayısı (içindeki olası yazı OKUNMADI)
    has_header_footer: bool  # üst/altbilgiden metin geldi mi
    has_notes: bool          # dipnot/sonnottan metin geldi mi

    @property
    def warnings(self) -> list[str]:
        """Kullanıcıya gösterilecek uyarılar (çözülemeyen atlamalar)."""
        out: list[str] = []
        if self.images:
            out.append(
                f"{self.images} görsel bulundu; görsel içindeki olası yazı "
                f"okunamadı (OCR gerekir)."
            )
        return out

    def describe(self) -> str:
        """Tek satırlık özet (CLI/log için)."""
        parts = [f"{self.paragraphs} metin bloğu", f"{self.tables} tablo",
                 f"{self.images} görsel"]
        if self.has_header_footer:
            parts.append("üst/altbilgi dahil")
        if self.has_notes:
            parts.append("dipnot dahil")
        return "Belge okundu: " + ", ".join(parts) + "."


def _clean_paragraph(text: str) -> str:
    """Tek paragraf metnini temizler: görsel işaretçileri (tam-satır VE satır-içi)
    silinir, işaretçi silinince oluşan çift boşluklar daraltılır."""
    text = text.strip()
    if not text or _IMAGE_MARKER.match(text):
        return ""
    text = _IMAGE_MARKER_INLINE.sub(" ", text)
    # İşaretçi silinince kalan art arda boşlukları tekle (satır sonlarına dokunma).
    text = re.sub(r"[ \t]{2,}", " ", text).strip()
    return text


def _classify(text: str, par: object | None) -> BlockKind:
    """Bloğun türünü belirler.

    Öncelik: (1) docx yapısı — paragraf gerçek bir tablo hücresinde mi
    (`lineage` içinde 'tbl'); (2) sayı-ağırlıklı kısa blok (PDF'ten çevrilmiş
    belgelerde tablolar çoğu kez gerçek tablo değil, hücre başına bir "paragraf"
    olarak gelir — "446.00625", "67.0 Hz" gibi); (3) paragraf stili "Heading*";
    (4) sezgisel yedek — kısa, tamamı büyük harf bloklar başlık sayılır
    (PDF'ten çevrilmiş belgelerde başlıklar çoğu kez stilsizdir).
    """
    lineage = getattr(par, "lineage", None)
    if lineage and "tbl" in lineage:
        return "tablo_hucresi"
    # Sayı-ağırlıklı kısa blok: rakam içeriyor ve rakam/işaret dışında en çok
    # 3 harf kalıyorsa (birim simgesi: "Hz", "kHz", "W") tablo verisi say.
    # Eşik bilinçli dar: "5. adım" gibi gerçek metin (4+ harf) paragraf kalır.
    if len(text) <= 40 and any(ch.isdigit() for ch in text):
        residue = re.sub(r"[\d\s.,:;%/()\-+±°=*]+", "", text)
        if len(residue) <= 3:
            return "tablo_hucresi"
    style = (getattr(par, "style", "") or "")
    if style.lower().startswith("heading"):
        return "baslik"
    letters = [ch for ch in text if ch.isalpha()]
    if letters and len(text) <= 100 and text == text.upper():
        return "baslik"
    return "paragraf"


def _blocks_from_section(section: list, section_pars: list | None = None) -> list[tuple[str, BlockKind]]:
    """docx2python bölümünü (``[tablo][satır][hücre][paragraf]``) etiketli blok
    listesi yapar: her öğe ``(metin, tür)``.

    Her paragraf dizesi ayrı bir blok olur; böylece tablo hücreleri ve gövde
    paragrafları atomik kalır (cümleler hücreler/paragraflar arasında birleşmez).
    Boş bloklar atılır. `section_pars` (docx2python `*_pars` görünümü) aynı
    iç içe yapıyı taşır ve stil/soy (lineage) bilgisini sağlar; erişilemezse
    sınıflandırma yalnız sezgisel yedekle yapılır.
    """
    blocks: list[tuple[str, BlockKind]] = []
    for t_i, table in enumerate(section):
        for r_i, row in enumerate(table):
            for c_i, cell in enumerate(row):
                for p_i, paragraph in enumerate(cell):
                    text = _clean_paragraph(paragraph)
                    if not text:
                        continue
                    par = None
                    if section_pars is not None:
                        try:
                            par = section_pars[t_i][r_i][c_i][p_i]
                        except (IndexError, TypeError):
                            par = None  # yapılar ayrışırsa sezgisel yedeğe düş
                    blocks.append((text, _classify(text, par)))
    return blocks


def _dedup_consecutive(blocks: list[tuple[str, BlockKind]]) -> list[tuple[str, BlockKind]]:
    """ARDIŞIK ve (boşluk-normalize) birebir aynı blokları teke indirir.

    PDF'ten çevrilmiş belgelerde sayfa başlıkları gövdeye çoğu kez art arda iki
    kez düşer ("BAŞLARKEN\\n\\nBAŞLARKEN"); bu yapay tekrar LLM'de sahte
    GRAMER-TEKRAR bulgusu üretir. Yalnız ARDIŞIK tekrar elenir — belgenin uzak
    yerlerindeki meşru tekrarlar (bölüm başlıkları vb.) korunur.
    """
    out: list[tuple[str, BlockKind]] = []
    prev_key: str | None = None
    for text, kind in blocks:
        key = " ".join(text.split())
        if key == prev_key:
            continue
        out.append((text, kind))
        prev_key = key
    return out


def _count_tables(body: list) -> int:
    """Gövdede gerçek tabloları sayar.

    docx2python'da normal bir paragraf da tek-satır/tek-hücreli bir "tablo"
    olarak sarmalanır; gerçek tablo en az bir boyutta >1'dir.
    """
    count = 0
    for table in body:
        rows = len(table)
        cols = max((len(row) for row in table), default=0)
        if rows > 1 or cols > 1:
            count += 1
    return count


def extract_docx_blocks(
    path: str | Path,
) -> tuple[str, list[BlockSpan], ExtractionReport]:
    """`.docx` dosyasını temiz metne + etiketli blok haritasına çevirir.

    Dönenler: ``(text, spans, report)`` — `text` blokların ``\\n\\n`` ile
    birleşimi; `spans` her bloğun `text` içindeki aralığı ve türü (offset
    sözleşmesi: `text[s.start:s.end]` bloğun kendisidir); `report` kapsam özeti.

    Sıra: gövde (paragraf + tablo + metin kutusu, belgedeki sırasıyla), ardından
    üst/altbilgi ve dipnot/sonnotlar belgenin SONUNA ayrı bloklar olarak eklenir
    (gövde akışını/tonunu bozmasın ama tutarlılık geçişine dahil olsunlar).
    Tekrar eden üst/altbilgiler tekilleştirilir; gövdede ARDIŞIK tekrar bloklar
    (sayfa başlığı artıkları) teke indirilir.
    """
    # Geç içe aktarma: docx2python yalnız docx işlerinde gereksin (chunk/metin
    # akışını gereksiz bağımlılıkla yüklemeyelim, air-gap'te de esneklik kalsın).
    from docx2python import docx2python

    with docx2python(str(path)) as doc:
        body_blocks = _blocks_from_section(doc.body, _pars_or_none(doc, "body_pars"))
        header_blocks = _blocks_from_section(doc.header, _pars_or_none(doc, "header_pars"))
        footer_blocks = _blocks_from_section(doc.footer, _pars_or_none(doc, "footer_pars"))
        footnote_blocks = _blocks_from_section(doc.footnotes, _pars_or_none(doc, "footnotes_pars"))
        endnote_blocks = _blocks_from_section(doc.endnotes, _pars_or_none(doc, "endnotes_pars"))
        n_tables = _count_tables(doc.body)
        n_images = len(doc.images)

    # Ek bölümler (sayfa mobilyası + notlar): tekrar edenleri sıra koruyarak ele.
    # (dict anahtarı (metin, tür) çifti — aynı metin farklı türle gelirse ayrı.)
    extra_blocks = list(dict.fromkeys(
        header_blocks + footer_blocks + footnote_blocks + endnote_blocks
    ))
    blocks = _dedup_consecutive(body_blocks + extra_blocks)

    # Birleşik metin + blok aralık haritası (offset sözleşmesi burada kurulur).
    spans: list[BlockSpan] = []
    parts: list[str] = []
    offset = 0
    for text_block, kind in blocks:
        start = offset
        parts.append(text_block)
        offset += len(text_block)
        spans.append(BlockSpan(start=start, end=offset, kind=kind))
        offset += len(_PARAGRAPH_SEP)
    text = _PARAGRAPH_SEP.join(parts)

    report = ExtractionReport(
        paragraphs=len(blocks),
        tables=n_tables,
        images=n_images,
        has_header_footer=bool(header_blocks or footer_blocks),
        has_notes=bool(footnote_blocks or endnote_blocks),
    )
    return text, spans, report


def _pars_or_none(doc: object, attr: str) -> list | None:
    """docx2python `*_pars` görünümünü güvenle alır (sürüm farkına dayanıklı)."""
    try:
        return getattr(doc, attr)
    except Exception:
        return None


def extract_docx_with_report(path: str | Path) -> tuple[str, ExtractionReport]:
    """`.docx` dosyasını eksiksiz temiz metne çevirir ve bir kapsam raporu döner.

    Geriye dönük uyumlu arayüz (blok haritası olmadan); yeni kod
    `extract_docx_blocks`'u tercih etmeli (analiz, blok türlerinden yararlanır).
    """
    text, _, report = extract_docx_blocks(path)
    return text, report


def extract_docx(path: str | Path) -> str:
    """`.docx` içindeki metni tek temiz metne çevirir (kapsam raporu olmadan).

    Geriye dönük uyumlu sade arayüz; çıktı `chunk_text` ve `Analyzer` için
    doğrudan kaynak metin olarak kullanılır.
    """
    text, _, _ = extract_docx_blocks(path)
    return text
