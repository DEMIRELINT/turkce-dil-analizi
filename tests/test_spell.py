"""Hunspell deterministik imla testleri.

Sözlük (dicts/tr_TR.dic) yoksa testler atlanır — CI/air-gap'te sözlük vendor'lanır.
"""

from pathlib import Path

import pytest

DICT_BASE = "dicts/tr_TR"
_has_dict = Path(f"{DICT_BASE}.dic").exists()

pytestmark = pytest.mark.skipif(not _has_dict, reason="tr_TR sözlüğü yok")


@pytest.fixture(scope="module")
def checker():
    from dilanaliz.spell import HunspellChecker

    return HunspellChecker(DICT_BASE)


def test_detects_misspellings(checker):
    fs = checker.check_text("Bu raporu yanlız ben hazırladım.")
    excerpts = [f.excerpt for f in fs]
    assert "yanlız" in excerpts


def test_clean_text_no_false_positive(checker):
    fs = checker.check_text("Toplantı notları onayınıza sunulmuştur.")
    assert fs == []


def test_offsets_are_exact(checker):
    text = "Bu raporu yanlız ben hazırladım."
    fs = checker.check_text(text)
    f = next(f for f in fs if f.excerpt == "yanlız")
    assert text[f.start:f.end] == "yanlız"


def test_whitelist_skips_word():
    from dilanaliz.spell import HunspellChecker

    hc = HunspellChecker(DICT_BASE, whitelist={"Acme"})
    fs = hc.check_text("Acme şirketi raporu gönderdi.")
    assert all(f.excerpt != "Acme" for f in fs)


def test_short_fragments_are_skipped(checker):
    # PDF dönüştürmesinden kopan 1-3 harfli ek parçaları ("nde", "nda")
    # denetlenmez — bunlara sözlük önerisi uydurulması ("ned") kökten biter.
    fs = checker.check_text("Kılavuz nde ayrıntı nda verilmiştir.")
    excerpts = [f.excerpt for f in fs]
    assert "nde" not in excerpts
    assert "nda" not in excerpts


def test_uppercase_valid_turkish_word_not_flagged(checker):
    # Python/spylls ASCII küçültmesi Türkçe I/İ'yi bozar; Türkçe-kurallı
    # küçültme denenmeden BÜYÜK harfli geçerli kelime hata sanılmamalı.
    fs = checker.check_text("TOPLANTI NOTLARI ONAYINIZA SUNULMUŞTUR.")
    assert fs == []


def test_detection_has_no_dictionary_suggestion(checker):
    # Hunspell yalnız tespit eder; öneri LLM'den gelir (görev ayrımı).
    from dilanaliz.spell import NO_SUGGESTION

    fs = checker.check_text("Bu raporu yanlız ben hazırladım.")
    f = next(f for f in fs if f.excerpt == "yanlız")
    assert f.suggestion == NO_SUGGESTION


def test_tr_case_helpers():
    from dilanaliz.spell import match_case, tr_capitalize, tr_lower, tr_upper

    assert tr_lower("FREKANSINA") == "frekansına"
    assert tr_lower("DİĞER") == "diğer"
    assert tr_upper("seçenekleri") == "SEÇENEKLERİ"
    assert tr_capitalize("istanbul") == "İstanbul"
    assert match_case("SEÇENEKLERI", "seçenekleri") == "SEÇENEKLERİ"
    assert match_case("Çağri", "çağrı") == "Çağrı"
    assert match_case("küçük", "kücük") == "kücük"  # referans küçükse dokunma
