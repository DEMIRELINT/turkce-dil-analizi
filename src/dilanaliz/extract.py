"""Belge → temiz metin çıkarma (Faz 3 — girdi katmanı).

`.docx` dosyasından metni belge **sırasını koruyarak** ve **eksiksiz** okur:
gövde paragrafları, **tablo hücreleri**, **metin kutuları/şekiller**,
**üst/altbilgiler** ve **dipnot/sonnotlar** dahil. Bloklar ÇİFT satır sonu ile
birleşir; böylece downstream parçalama (`chunk.py`) paragrafları boş-satır
sınırından ayırabilir.

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
buradan geçirmektir.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# İki bloğu ayıran sınır; chunk.py ile tutarlı olmalı.
_PARAGRAPH_SEP = "\n\n"

# docx2python, gövde akışındaki bir görselin yerine "----media/image1.png----"
# gibi bir yer tutucu metin koyar. Bu, analiz metnine gürültü katmasın diye
# elenir (görseller ayrıca ExtractionReport.images ile raporlanır).
_IMAGE_MARKER = re.compile(r"^-{2,}media/\S+-{2,}$")


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


def _blocks_from_section(section: list) -> list[str]:
    """docx2python bölümünü (``[tablo][satır][hücre][paragraf]``) düz blok listesi
    yapar.

    Her paragraf dizesi ayrı bir blok olur; böylece tablo hücreleri ve gövde
    paragrafları atomik kalır (cümleler hücreler/paragraflar arasında birleşmez).
    Boş bloklar atılır.
    """
    blocks: list[str] = []
    for table in section:
        for row in table:
            for cell in row:
                for paragraph in cell:
                    text = paragraph.strip()
                    if text and not _IMAGE_MARKER.match(text):
                        blocks.append(text)
    return blocks


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


def extract_docx_with_report(path: str | Path) -> tuple[str, ExtractionReport]:
    """`.docx` dosyasını eksiksiz temiz metne çevirir ve bir kapsam raporu döner.

    Sıra: gövde (paragraf + tablo + metin kutusu, belgedeki sırasıyla), ardından
    üst/altbilgi ve dipnot/sonnotlar belgenin SONUNA ayrı bloklar olarak eklenir
    (gövde akışını/tonunu bozmasın ama tutarlılık geçişine dahil olsunlar).
    Tekrar eden üst/altbilgiler (her bölümde yinelenebilir) tekilleştirilir.
    """
    # Geç içe aktarma: docx2python yalnız docx işlerinde gereksin (chunk/metin
    # akışını gereksiz bağımlılıkla yüklemeyelim, air-gap'te de esneklik kalsın).
    from docx2python import docx2python

    with docx2python(str(path)) as doc:
        body_blocks = _blocks_from_section(doc.body)
        header_blocks = _blocks_from_section(doc.header)
        footer_blocks = _blocks_from_section(doc.footer)
        footnote_blocks = _blocks_from_section(doc.footnotes)
        endnote_blocks = _blocks_from_section(doc.endnotes)
        n_tables = _count_tables(doc.body)
        n_images = len(doc.images)

    # Ek bölümler (sayfa mobilyası + notlar): tekrar edenleri sıra koruyarak ele.
    extra_blocks = list(dict.fromkeys(
        header_blocks + footer_blocks + footnote_blocks + endnote_blocks
    ))
    blocks = body_blocks + extra_blocks
    text = _PARAGRAPH_SEP.join(blocks)

    report = ExtractionReport(
        paragraphs=len(blocks),
        tables=n_tables,
        images=n_images,
        has_header_footer=bool(header_blocks or footer_blocks),
        has_notes=bool(footnote_blocks or endnote_blocks),
    )
    return text, report


def extract_docx(path: str | Path) -> str:
    """`.docx` içindeki metni tek temiz metne çevirir (kapsam raporu olmadan).

    Geriye dönük uyumlu sade arayüz; çıktı `chunk_text` ve `Analyzer` için
    doğrudan kaynak metin olarak kullanılır.
    """
    text, _ = extract_docx_with_report(path)
    return text
