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
    # Cümle sınırı OLMAYAN tek paragraf bütçeyi aşsa da bölünemez (bütün kalır).
    big = "x" * 50
    chunks = chunk_text(big, max_chars=10)
    assert len(chunks) == 1
    assert chunks[0].text == big


def test_oversized_paragraph_split_at_sentences():
    # Cümle sınırı olan, bütçeyi aşan tek paragraf birden çok parçaya bölünür;
    # hiçbir parça bütçeyi aşmaz ve metin birebir korunur (sözleşme).
    source = (
        "Birinci cümle burada yer alıyor. İkinci cümle de buradadır. "
        "Üçüncü cümle son cümledir."
    )
    chunks = chunk_text(source, max_chars=40)
    assert len(chunks) > 1
    assert all(len(c.text) <= 40 for c in chunks)
    # Birebir-dilim / offset sözleşmesi.
    assert all(source[c.start : c.end] == c.text for c in chunks)
    # Birleştirildiğinde kaynağa eşit (hiç karakter kaybı/çoğalması yok).
    assert "".join(c.text for c in chunks) == source


def test_sentence_split_respects_abbreviations_and_numbers():
    # "Prof.", "Dr." kısaltma; "15.30", "2." sayı/sıra → bölme bunlardan OLMAZ.
    # Yalnız "geldi." sonrası gerçek cümle sınırıdır.
    source = "Prof. Dr. Ahmet Bey saat 15.30'da 2. kez geldi. Sonra hemen çıktı."
    chunks = chunk_text(source, max_chars=40)
    # İlk parça tüm ilk cümleyi (kısaltma/sayı bölünmeden) içermeli.
    assert chunks[0].text.startswith("Prof. Dr. Ahmet Bey")
    assert chunks[0].text.rstrip().endswith("geldi.")
    assert all(source[c.start : c.end] == c.text for c in chunks)


def test_single_sentence_longer_than_budget_kept_whole():
    # Bölünemeyen tek bir cümle (sınır yok) bütçeyi aşsa da son çare olarak bütün
    # kalır — veri bozulmaz.
    source = "Bu cümlede hiç cümle sonu noktalaması bulunmuyor ve oldukça uzundur"
    chunks = chunk_text(source, max_chars=20)
    assert len(chunks) == 1
    assert chunks[0].text == source


def test_invalid_max_chars_raises():
    with pytest.raises(ValueError):
        chunk_text("metin", max_chars=0)


def test_chunk_end_property():
    ch = Chunk(text="abc", start=5)
    assert ch.end == 8
