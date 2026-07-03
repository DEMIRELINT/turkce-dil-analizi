import pytest

from dilanaliz.extract import (
    IMAGE_PLACEHOLDER,
    extract_docx,
    extract_docx_with_report,
)

docx = pytest.importorskip("docx")


def _make_docx(tmp_path, paragraphs):
    document = docx.Document()
    for text in paragraphs:
        document.add_paragraph(text)
    path = tmp_path / "ornek.docx"
    document.save(str(path))
    return path


def test_extract_joins_paragraphs_with_blank_line(tmp_path):
    path = _make_docx(tmp_path, ["Birinci paragraf.", "İkinci paragraf."])
    text = extract_docx(path)
    assert text == "Birinci paragraf.\n\nİkinci paragraf."


def test_extract_drops_empty_paragraphs(tmp_path):
    path = _make_docx(tmp_path, ["Dolu.", "   ", "", "Yine dolu."])
    text = extract_docx(path)
    assert text == "Dolu.\n\nYine dolu."


def test_extract_output_is_chunkable(tmp_path):
    # Çıkarılan metin, boş-satır sınırından parçalanabilmeli (chunk.py ile uyum).
    from dilanaliz.chunk import chunk_text

    path = _make_docx(tmp_path, ["Bir.", "İki.", "Üç."])
    text = extract_docx(path)
    chunks = chunk_text(text, max_chars=4)
    assert [c.text for c in chunks] == ["Bir.", "İki.", "Üç."]


# --- Atlanan içeriklerin artık yakalandığını doğrula ----------------------

def test_extract_includes_table_cells(tmp_path):
    # python-docx'in atladığı tablo hücreleri docx2python ile okunmalı.
    document = docx.Document()
    document.add_paragraph("Gövde paragrafı.")
    table = document.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Hücre A1"
    table.cell(0, 1).text = "Hücre B1"
    table.cell(1, 0).text = "Hücre A2"
    table.cell(1, 1).text = ""  # boş hücre atılmalı
    path = tmp_path / "tablo.docx"
    document.save(str(path))

    text, report = extract_docx_with_report(path)
    assert "Gövde paragrafı." in text
    for cell in ("Hücre A1", "Hücre B1", "Hücre A2"):
        assert cell in text
    assert report.tables == 1
    # Her dolu hücre + gövde paragrafı ayrı blok; boş hücre yok.
    assert text.count("\n\n") == 3


def test_extract_includes_header_and_footer(tmp_path):
    document = docx.Document()
    document.add_paragraph("Gövde.")
    section = document.sections[0]
    section.header.paragraphs[0].text = "ÜST BİLGİ metni"
    section.footer.paragraphs[0].text = "ALT BİLGİ metni"
    path = tmp_path / "hf.docx"
    document.save(str(path))

    text, report = extract_docx_with_report(path)
    assert "ÜST BİLGİ metni" in text
    assert "ALT BİLGİ metni" in text
    assert report.has_header_footer is True


def _png_bytes(width=2, height=2):
    """Geçerli, küçük bir RGB PNG üretir (python-docx boyut okuyabilsin)."""
    import struct
    import zlib

    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)  # 8-bit RGB
    raw = b"".join(b"\x00" + b"\xff\x00\x00" * width for _ in range(height))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def test_report_counts_images_and_warns(tmp_path):
    # Görsel göm → sayılmalı ve uyarı üretmeli (içindeki yazı okunamaz).
    import io

    png = _png_bytes()
    document = docx.Document()
    document.add_paragraph("Görselli belge.")
    document.add_picture(io.BytesIO(png))
    path = tmp_path / "gorsel.docx"
    document.save(str(path))

    text, report = extract_docx_with_report(path)
    assert report.images >= 1
    assert any("görsel" in w.lower() for w in report.warnings)
    # Görsel yer tutucu işaretçisi analiz metnine sızmamalı.
    assert "media/" not in text
    assert "Görselli belge." in text


# --- Satır-içi işaretçi temizliği + ardışık tekrar tekilleştirme -------------

def test_inline_image_markers_become_placeholder(tmp_path):
    # Cümle İÇİNDE (satır-içi) geçen görsel işaretçisi boşlukla silinmez,
    # `[görsel]` yer tutucusuna dönüşür — cümle bütünlüğü korunur, LLM görselin
    # orada olduğunu görür (bkz. prompt.py). "media/" ham işaretçisi kalmamalı.
    path = _make_docx(tmp_path, [
        "Metin ----media/image3.png---- ortasında işaretçi.",
    ])
    text = extract_docx(path)
    assert "media/" not in text
    assert IMAGE_PLACEHOLDER in text
    assert text == f"Metin {IMAGE_PLACEHOLDER} ortasında işaretçi."


def test_leading_inline_image_marker_becomes_placeholder(tmp_path):
    # İşaretçi metne YAPIŞIK ve zincirli gelebilir; yine `[görsel]` olur,
    # ardındaki gerçek metin (bitişik olsa da) korunur.
    path = _make_docx(tmp_path, [
        "----media/image1.png--------media/image2.png----Alıcı/Verici Telsizler",
    ])
    text = extract_docx(path)
    assert "media/" not in text
    assert IMAGE_PLACEHOLDER in text
    assert "Alıcı/Verici Telsizler" in text


def test_standalone_image_marker_fully_removed_no_placeholder(tmp_path):
    # TEK-BAŞINA (kendi satırında) bir görsel HÂLÂ tamamen silinir — yer
    # tutucu BIRAKMADAN. Ayrım korunur: outline görsel LLM'e hiç gitmez.
    path = _make_docx(tmp_path, [
        "Gerçek paragraf.",
        "----media/image9.png----",
        "İkinci gerçek paragraf.",
    ])
    text = extract_docx(path)
    assert IMAGE_PLACEHOLDER not in text
    assert text == "Gerçek paragraf.\n\nİkinci gerçek paragraf."


def test_consecutive_duplicate_blocks_are_deduped(tmp_path):
    # Sayfa başlığı artıkları gövdeye art arda iki kez düşer; teke inmeli.
    path = _make_docx(tmp_path, ["BAŞLARKEN", "BAŞLARKEN", "Gerçek metin.", "BAŞLARKEN"])
    text = extract_docx(path)
    assert text.count("BAŞLARKEN") == 2  # ardışık ikili teke indi; uzaktaki korundu


# --- Etiketli blok API'si (extract_docx_blocks) ------------------------------

def test_blocks_api_spans_match_text(tmp_path):
    from dilanaliz.extract import extract_docx_blocks

    path = _make_docx(tmp_path, ["Birinci paragraf.", "İkinci paragraf."])
    text, spans, report = extract_docx_blocks(path)
    assert len(spans) == 2
    for s in spans:
        # Offset sözleşmesi: text[s.start:s.end] bloğun kendisidir.
        assert text[s.start:s.end].strip() == text[s.start:s.end]
    assert text[spans[0].start:spans[0].end] == "Birinci paragraf."
    assert report.paragraphs == 2


def test_blocks_api_classifies_table_cells(tmp_path):
    from dilanaliz.extract import extract_docx_blocks

    document = docx.Document()
    document.add_paragraph("Gövde paragrafı burada uzunca yazılmış.")
    table = document.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Hücre metni bir"
    table.cell(0, 1).text = "Hücre metni iki"
    path = tmp_path / "tablo.docx"
    document.save(str(path))

    text, spans, _ = extract_docx_blocks(path)
    kinds = {text[s.start:s.end]: s.kind for s in spans}
    assert kinds["Gövde paragrafı burada uzunca yazılmış."] == "paragraf"
    assert kinds["Hücre metni bir"] == "tablo_hucresi"
    assert kinds["Hücre metni iki"] == "tablo_hucresi"


def test_blocks_api_classifies_headings(tmp_path):
    from dilanaliz.extract import extract_docx_blocks

    document = docx.Document()
    document.add_heading("Stil ile başlık", level=1)          # stilden yakalanır
    document.add_paragraph("PİLLER VE ŞARJ CİHAZLARI")        # sezgisel: tamamı büyük
    document.add_paragraph("Normal bir cümle geliyor burada.")
    path = tmp_path / "baslik.docx"
    document.save(str(path))

    text, spans, _ = extract_docx_blocks(path)
    kinds = {text[s.start:s.end]: s.kind for s in spans}
    assert kinds["Stil ile başlık"] == "baslik"
    assert kinds["PİLLER VE ŞARJ CİHAZLARI"] == "baslik"
    assert kinds["Normal bir cümle geliyor burada."] == "paragraf"


def test_blocks_api_classifies_numeric_pseudo_table(tmp_path):
    # PDF→Word dönüşümünde tablolar çoğu kez gerçek tablo değildir; salt
    # sayı(+birim) paragrafı tablo verisi sayılmalı, gerçek metin sayılmamalı.
    from dilanaliz.extract import extract_docx_blocks

    path = _make_docx(tmp_path, ["446.00625", "67.0 Hz", "5. adım burada anlatılır."])
    text, spans, _ = extract_docx_blocks(path)
    kinds = {text[s.start:s.end]: s.kind for s in spans}
    assert kinds["446.00625"] == "tablo_hucresi"
    assert kinds["67.0 Hz"] == "tablo_hucresi"
    assert kinds["5. adım burada anlatılır."] == "paragraf"


# --- Dipnot/sonnot: gerçek .docx yerine docx2python'ın kendi iç veri şekliyle -
# `python-docx` (fixture üreten kütüphane) dipnot/sonnot eklemek için hiçbir
# genel API sunmuyor (sürüm 1.2.0) — ham OOXML (footnotes part + ilişki +
# w:footnoteReference run) gerektirir, bu da kırılgan ve bu testin amacına
# göre aşırı mühendislik olur. Bunun yerine `_blocks_from_section`'ı
# docx2python'ın KENDİ iç veri şekliyle ([tablo][satır][hücre][paragraf])
# doğrudan çağırıyoruz — `extract_docx_blocks` dipnot/sonnotu header/footer
# ile BİREBİR aynı birleştirme yolundan (`extra_blocks`) geçirdiği için
# (extract.py:262-267), bu + mevcut `test_extract_includes_header_and_footer`
# birlikte dipnot/sonnot yolunu uçtan uca güvence altına alır.
#
# Not: Metin kutusu (textbox) için AYRI bir test YOK — araştırma sonucu:
# docx2python kaynağında textbox'a özgü hiçbir işleme kodu yok; metin kutusu
# içeriği docx2python tarafından genel gövde (body) tablo yapısına
# katlanıyor. extract.py'de textbox'a özel bir kod yolu olmadığından, ayrı
# bir test gerçek bir boşluğu kapatmaz — mevcut gövde paragrafı testleri
# zaten bu genel yolu kapsıyor.

def test_blocks_from_section_handles_footnote_shaped_input():
    from dilanaliz.extract import _blocks_from_section

    # docx2python şekli: [tablo][satır][hücre][paragraf]. Dipnot/sonnot da
    # aynı iç içe yapıyla gelir (extract.py:257-258).
    footnote_section = [[[["Dipnot metni burada."]]]]
    blocks = _blocks_from_section(footnote_section)
    assert blocks == [("Dipnot metni burada.", "paragraf")]


def test_blocks_from_section_handles_multiple_footnote_paragraphs():
    from dilanaliz.extract import _blocks_from_section

    # İki ayrı dipnot (iki "hücre") + boş bir dipnot paragrafı (atılmalı).
    footnote_section = [[
        [["İlk dipnot."]],
        [["İkinci dipnot.", ""]],
    ]]
    blocks = _blocks_from_section(footnote_section)
    assert blocks == [("İlk dipnot.", "paragraf"), ("İkinci dipnot.", "paragraf")]
