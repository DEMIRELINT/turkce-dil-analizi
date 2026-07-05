"""StaticRulesProvider geçiş-farkında kesitleme testleri.

Paketli rules.md üzerinde: yerel geçiş yalnız A+B, ton geçişi yalnız C alır;
"Bilinen Sınırlar" (geliştirici notu) hiçbir kesite girmez; önsöz (rule_id
talimatları) her kesitte bulunur. Tanınan başlığı olmayan harici dosyada
kesitleme devre dışı kalır (tam metin döner — güvenli geri düşüş).
"""

from dilanaliz.rules import StaticRulesProvider


def test_local_purpose_has_imla_and_grammar_but_not_tone():
    ctx = StaticRulesProvider().get_context("metin", purpose="local")
    assert "**IMLA-DE-DA**" in ctx
    assert "**GRAMER-CATI**" in ctx
    assert "**TON-RESMI**" not in ctx
    assert "Bilinen Sınırlar" not in ctx
    # Önsöz (rule_id talimatı) her kesitte olmalı.
    assert "rule_id" in ctx


def test_tone_purpose_has_tone_but_not_imla():
    ctx = StaticRulesProvider().get_context("metin", purpose="tone")
    assert "**TON-RESMI**" in ctx
    assert "**IMLA-DE-DA**" not in ctx
    assert "**GRAMER-CATI**" not in ctx
    assert "Bilinen Sınırlar" not in ctx
    assert "rule_id" in ctx


def test_all_purpose_has_every_axis_but_not_dev_notes():
    ctx = StaticRulesProvider().get_context("metin")  # varsayılan: all
    assert "**IMLA-DE-DA**" in ctx
    assert "**GRAMER-CATI**" in ctx
    assert "**TON-RESMI**" in ctx
    assert "Bilinen Sınırlar" not in ctx


def test_headingless_external_file_returns_full_text(tmp_path):
    # Kurumun kendi RULES_PATH dosyası bizim başlık yapımızı izlemeyebilir;
    # o durumda kesitleme devre dışı — hiçbir kural sessizce kaybolmaz.
    custom = tmp_path / "kurum_kurallari.md"
    custom.write_text("Kurum kuralı: her cümle nokta ile biter.", encoding="utf-8")
    provider = StaticRulesProvider(rules_path=custom)
    for purpose in ("local", "tone", "all"):
        assert provider.get_context("metin", purpose=purpose) == (
            "Kurum kuralı: her cümle nokta ile biter."
        )


def test_unknown_purpose_falls_back_to_all():
    ctx = StaticRulesProvider().get_context("metin", purpose="bilinmeyen")
    assert "**IMLA-DE-DA**" in ctx
    assert "**TON-RESMI**" in ctx
    assert "Bilinen Sınırlar" not in ctx
