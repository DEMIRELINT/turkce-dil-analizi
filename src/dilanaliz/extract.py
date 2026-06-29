"""Belge → temiz metin çıkarma (Faz 3 — girdi katmanı).

`.docx` dosyasından paragraf metinlerini sırayla okur, boş paragrafları atar ve
paragrafları ÇİFT satır sonu ile birleştirir. Bu sayede downstream parçalama
(`chunk.py`) paragrafları boş-satır sınırından ayırabilir.

Kapsam: YALNIZ metin içeriği. Biçim/şablon (font, başlık stili, header/footer,
sayfa/section break) bu katmanın kapsamında DEĞİLDİR — onlar sonraki bir faza
aittir. Tablo hücreleri de MVP'de dışarıdadır (gerekirse sonra eklenir).

PDF çıkarma bilinçli olarak buraya KONMADI: PDF'te çok sütunlu düzen, araya giren
görsel ve satır kırılmaları metni bozar; güvenilir yol, kaynağı Word olarak alıp
buradan geçirmektir.
"""

from __future__ import annotations

from pathlib import Path

# İki paragrafı ayıran sınır; chunk.py ile tutarlı olmalı.
_PARAGRAPH_SEP = "\n\n"


def extract_docx(path: str | Path) -> str:
    """`.docx` dosyasındaki paragraf metnini tek bir temiz metne çevirir.

    Boş paragraflar atılır; kalanlar çift satır sonuyla birleştirilir. Çıktı,
    `chunk_text` ve `Analyzer` için doğrudan kaynak metin olarak kullanılır.
    """
    # Geç içe aktarma: python-docx yalnız docx işlerinde gereksin (chunk/metin
    # akışını gereksiz bağımlılıkla yüklemeyelim, air-gap'te de esneklik kalsın).
    from docx import Document

    document = Document(str(path))
    paragraphs = (p.text.strip() for p in document.paragraphs)
    return _PARAGRAPH_SEP.join(p for p in paragraphs if p)
