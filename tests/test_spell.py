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
