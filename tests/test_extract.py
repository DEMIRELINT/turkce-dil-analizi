import pytest

from dilanaliz.extract import extract_docx

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
