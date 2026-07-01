import pytest

from dilanaliz.extract import extract_docx, extract_docx_with_report

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
