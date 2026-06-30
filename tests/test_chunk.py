import pytest

from dilanaliz.chunk import Chunk, chunk_text


def test_empty_source_yields_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   \n\n  ") == []


def test_single_paragraph_one_chunk():
    source = "Tek bir paragraf cümlesi."
    chunks = chunk_text(source)
    assert len(chunks) == 1
    assert chunks[0].text == source
    assert chunks[0].start == 0


def test_chunk_text_is_exact_source_slice():
    # Offset rebasing'in doğru çalışması için parça metni kaynağın birebir dilimi
    # olmalı: source[start:end] == text.
    source = "Birinci paragraf.\n\nİkinci paragraf burada.\n\nÜçüncü."
    for ch in chunk_text(source, max_chars=20):
        assert source[ch.start : ch.end] == ch.text


def test_paragraphs_grouped_under_budget():
    source = "aaa\n\nbbb\n\nccc"
    # Bütçe büyük → hepsi tek parçada (ayraçlar dahil birebir dilim).
    chunks = chunk_text(source, max_chars=1000)
    assert len(chunks) == 1
    assert chunks[0].text == source


def test_split_when_budget_exceeded():
    source = "aaaa\n\nbbbb\n\ncccc"
    # Her paragraf 4 karakter; bütçe 5 → her paragraf ayrı parçaya düşer.
    chunks = chunk_text(source, max_chars=5)
    assert [c.text for c in chunks] == ["aaaa", "bbbb", "cccc"]
    assert [c.start for c in chunks] == [0, 6, 12]


def test_oversized_single_paragraph_kept_whole():
    # Tek paragraf bütçeyi aşsa bile bölünmez (cümle ortadan kesilmez).
    big = "x" * 50
    chunks = chunk_text(big, max_chars=10)
    assert len(chunks) == 1
    assert chunks[0].text == big


def test_invalid_max_chars_raises():
    with pytest.raises(ValueError):
        chunk_text("metin", max_chars=0)


def test_chunk_end_property():
    ch = Chunk(text="abc", start=5)
    assert ch.end == 8
