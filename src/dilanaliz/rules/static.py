"""Statik kural sağlayıcısı (Faz 1) — geçiş-farkında kesitleme.

`rules.md` bölümlere ayrılıp yalnız istenen geçişin (purpose) işine yarayan
kısımlar döndürülür: yerel geçiş A (imla) + B (dil bilgisi), ton geçişi C
(ton/üslup) alır. "Bilinen Sınırlar" bölümü geliştirici dokümantasyonudur ve
HİÇBİR geçişe gönderilmez. Önsöz (ilk `## ` başlığından önceki kısım —
rule_id talimatları) her kesite dahildir.

Güvenli geri düşüş: dosyada tanınan bölüm başlığı hiç yoksa (kurumun kendi
RULES_PATH dosyası farklı yapıdaysa) purpose ne olursa olsun dosyanın TAMAMI
döner — hiçbir kural sessizce kaybolmaz.

Korpus bağlam bütçesini aşınca RetrievalRulesProvider'a geçilir (aynı imza).
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

_RULES_PATH = Path(__file__).with_name("rules.md")

# Bölüm başlığı: satır başında "## " — başlık metni bölüm kimliğini belirler.
_SECTION_RE = re.compile(r"(?m)^## ")

# Başlık ön-eki → bölüm kimliği. Burada OLMAYAN başlıklar (ör. "Bilinen
# Sınırlar") hiçbir purpose'a dahil edilmez (geliştirici dokümantasyonu).
_HEADING_KINDS = {
    "A.": "imla",
    "B.": "dil_bilgisi",
    "C.": "ton",
}

# purpose → dahil edilecek bölüm kimlikleri.
_PURPOSE_KINDS = {
    "local": ("imla", "dil_bilgisi"),
    "tone": ("ton",),
    "all": ("imla", "dil_bilgisi", "ton"),
}


def _split_sections(source: str) -> tuple[str, list[tuple[str | None, str]]]:
    """Kaynağı (önsöz, [(bölüm_kimliği | None, bölüm_metni), ...]) olarak ayırır.

    Bölüm metni `## ` başlığıyla başlar (başlık dahil). Kimliği eşlenemeyen
    bölümler None kimlikle döner (hiçbir purpose'a girmez).
    """
    matches = list(_SECTION_RE.finditer(source))
    if not matches:
        return source, []
    preamble = source[: matches[0].start()]
    sections: list[tuple[str | None, str]] = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(source)
        body = source[m.start():end]
        heading = body[3:].split("\n", 1)[0].strip()
        kind = next(
            (k for prefix, k in _HEADING_KINDS.items() if heading.startswith(prefix)),
            None,
        )
        sections.append((kind, body))
    return preamble, sections


def _slice_for(source: str, purpose: str) -> str:
    """Kaynaktan, verilen purpose'un bölümlerini (önsözle birlikte) seçer.

    Tanınan bölüm hiç yoksa TAM metin döner (harici RULES_PATH güvenliği).
    Bilinmeyen purpose "all" gibi davranır (kural kaybettirmek yerine fazla
    göndermek güvenli taraftır).
    """
    preamble, sections = _split_sections(source)
    if not any(kind for kind, _ in sections):
        return source
    wanted = _PURPOSE_KINDS.get(purpose, _PURPOSE_KINDS["all"])
    picked = [body for kind, body in sections if kind in wanted]
    if not picked:
        return source
    return (preamble + "".join(picked)).rstrip() + "\n"


@lru_cache(maxsize=8)
def _packaged_slice(purpose: str) -> str:
    return _slice_for(_RULES_PATH.read_text(encoding="utf-8"), purpose)


class StaticRulesProvider:
    """Kural metnini geçişe (purpose) göre kesitleyerek döndürür."""

    def __init__(self, rules_path: Path | None = None) -> None:
        self._rules_path = rules_path

    def get_context(self, text: str, purpose: str = "all") -> str:  # noqa: ARG002 — Faz 1'de metin kullanılmaz
        if self._rules_path is not None:
            # Harici dosya her çağrıda okunur (canlı düzenleme desteği);
            # 27 KB okuma + ayrıştırma LLM gecikmesi yanında ihmal edilebilir.
            return _slice_for(self._rules_path.read_text(encoding="utf-8"), purpose)
        return _packaged_slice(purpose)
