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

from .spell import HunspellChecker

# İki bloğu ayıran sınır; chunk.py ile tutarlı olmalı.
_PARAGRAPH_SEP = "\n\n"

# docx2python, gövde akışındaki bir görselin yerine "----media/image1.png----"
# gibi bir yer tutucu metin koyar. Bu, analiz metnine gürültü katmasın diye
# elenir (görseller ayrıca ExtractionReport.images ile raporlanır).
_IMAGE_MARKER = re.compile(r"^-{2,}media/\S+-{2,}$")

# Bitişik iki "harf dizisi" (rakam hariç) — kelime-içi ayraç onarımı için.
_WORD_TOKEN = re.compile(r"[^\W\d_]+", re.UNICODE)


def _repair_broken_words(text: str, speller: HunspellChecker) -> tuple[str, int]:
    """docx2python'un run-birleştirme kusuruna karşı dar, Hunspell-doğrulamalı onarım.

    Word bir kelimeyi biçimlendirme farkı yüzünden iki run'a bölebilir; docx2python
    yalnız AYNI biçimlendirmeye sahip run'ları birleştirir, farklıysa aralarında
    beklenmeyen bir ayraç (tek boşluk/nokta) kalır (bkz. kütüphanenin belgelenmiş
    sınırı). Burada yalnız EN AZ BİR parça tek başına sözlükte yoksa VE
    birleştirilmiş hali TAM OLARAK sözlükte varsa ayraç kaldırılır; aksi halde
    (ikisi de geçerliyse ya da birleşim de geçersizse) metne DOKUNULMAZ — belirsiz
    durumlarda içerik uydurmaktansa olduğu gibi bırakıp mevcut Hunspell-aday/LLM
    akışına devretmek tercih edilir.
    """
    tokens = list(_WORD_TOKEN.finditer(text))
    if len(tokens) < 2:
        return text, 0

    gaps_to_remove: list[tuple[int, int]] = []
    for left, right in zip(tokens, tokens[1:]):
        gap = text[left.end():right.start()]
        if gap not in (" ", "."):
            continue
        left_word, right_word = left.group(0), right.group(0)
        if speller.is_known(left_word) and speller.is_known(right_word):
            continue  # ikisi de geçerli kelime — dokunma (bkz. rules.md LLM rehberliği)
        if not speller.is_known(left_word + right_word):
            continue  # birleşim de geçersiz — dokunma
        gaps_to_remove.append((left.end(), right.start()))

    if not gaps_to_remove:
        return text, 0

    pieces: list[str] = []
    cursor = 0
    for start, end in gaps_to_remove:
        pieces.append(text[cursor:start])
        cursor = end
    pieces.append(text[cursor:])
    return "".join(pieces), len(gaps_to_remove)


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
    # docx2python'un run-birleştirme kusuru yüzünden kelime içine sızan boşluk/
    # nokta sayısı — yalnız sözlüğün KESİN doğruladığı durumlarda onarılır.
    repaired_words: int = 0

    @property
    def warnings(self) -> list[str]:
        """Kullanıcıya gösterilecek uyarılar (çözülemeyen atlamalar)."""
        out: list[str] = []
        if self.images:
            out.append(
                f"{self.images} görsel bulundu; görsel içindeki olası yazı "
                f"okunamadı (OCR gerekir)."
            )
        if self.repaired_words:
            out.append(
                f"{self.repaired_words} kelime, çıkarma sırasında bölünmüş "
                f"görünüyor ve otomatik onarıldı."
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


def _blocks_from_section(
    section: list, speller: HunspellChecker | None = None
) -> tuple[list[str], int]:
    """docx2python bölümünü (``[tablo][satır][hücre][paragraf]``) düz blok listesi
    yapar.

    Her paragraf dizesi ayrı bir blok olur; böylece tablo hücreleri ve gövde
    paragrafları atomik kalır (cümleler hücreler/paragraflar arasında birleşmez).
    Boş bloklar atılır. `speller` verilmişse her paragraf, birleştirilmeden ÖNCE
    (yani onarım asla paragraf sınırını AŞMADAN) `_repair_broken_words` ile
    onarılır; `speller=None` ise (sözlük yok) davranış değişmez.
    """
    blocks: list[str] = []
    repaired = 0
    for table in section:
        for row in table:
            for cell in row:
                for paragraph in cell:
                    text = paragraph.strip()
                    if text and not _IMAGE_MARKER.match(text):
                        if speller is not None:
                            text, n = _repair_broken_words(text, speller)
                            repaired += n
                        blocks.append(text)
    return blocks, repaired


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


def extract_docx_with_report(
    path: str | Path, speller: HunspellChecker | None = None
) -> tuple[str, ExtractionReport]:
    """`.docx` dosyasını eksiksiz temiz metne çevirir ve bir kapsam raporu döner.

    Sıra: gövde (paragraf + tablo + metin kutusu, belgedeki sırasıyla), ardından
    üst/altbilgi ve dipnot/sonnotlar belgenin SONUNA ayrı bloklar olarak eklenir
    (gövde akışını/tonunu bozmasın ama tutarlılık geçişine dahil olsunlar).
    Tekrar eden üst/altbilgiler (her bölümde yinelenebilir) tekilleştirilir.

    `speller` verilmişse (bkz. `Analyzer.speller`), docx2python'un bilinen
    run-birleştirme kusuruna (kelime ortasına sızan boşluk/nokta) karşı dar bir
    onarım uygulanır — yalnız sözlüğün KESİN doğruladığı durumlarda (bkz.
    `_repair_broken_words`). `speller=None` ise davranış tamamen bugünkü gibi
    kalır (geriye dönük uyumlu).
    """
    # Geç içe aktarma: docx2python yalnız docx işlerinde gereksin (chunk/metin
    # akışını gereksiz bağımlılıkla yüklemeyelim, air-gap'te de esneklik kalsın).
    from docx2python import docx2python

    with docx2python(str(path)) as doc:
        body_blocks, r1 = _blocks_from_section(doc.body, speller)
        header_blocks, r2 = _blocks_from_section(doc.header, speller)
        footer_blocks, r3 = _blocks_from_section(doc.footer, speller)
        footnote_blocks, r4 = _blocks_from_section(doc.footnotes, speller)
        endnote_blocks, r5 = _blocks_from_section(doc.endnotes, speller)
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
        repaired_words=r1 + r2 + r3 + r4 + r5,
    )
    return text, report


def extract_docx(path: str | Path, speller: HunspellChecker | None = None) -> str:
    """`.docx` içindeki metni tek temiz metne çevirir (kapsam raporu olmadan).

    Geriye dönük uyumlu sade arayüz; çıktı `chunk_text` ve `Analyzer` için
    doğrudan kaynak metin olarak kullanılır.
    """
    text, _ = extract_docx_with_report(path, speller=speller)
    return text
