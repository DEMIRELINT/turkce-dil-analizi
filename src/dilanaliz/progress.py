"""İlerleme yayını (analiz adımlarını canlı bildirme).

Boru hattı uzun bir belgede çok sayıda senkron LLM çağrısı yapar; bu modül her
adımda "şu an şunu yapıyorum" bilgisini dışarıya (örn. web paneli) iletmek için
hafif, bağımsız bir olay tipi ve callback imzası tanımlar.

Tasarım: `analyze_document` opsiyonel bir `ProgressCallback` alır. `None` ise
hiçbir şey değişmez (CLI ve testler aynen çalışır). Hiçbir ağ/IO yapmaz; ne
yapılacağına çağıran taraf (CLI → stderr, web → SSE) karar verir.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class ProgressEvent:
    """Tek bir analiz adımının insan-okur durumu.

    stage   : makine-okur aşama anahtarı
              ("chunk" = bölme tamamlandı | "chunk_start"/"chunk_done" = bir parça
               başladı/bitti | "consistency_start"/"consistency_done" |
               "finalize" | "done").
    message : Türkçe, kullanıcıya gösterilecek mesaj ("Parça 2/5 inceleniyor").
    current : parça kimliği (1 tabanlı, kararlı); 0 = anlamlı değil. Paralelde
              parçalar sırasız biter, ama her parçanın `current`'ı sabittir.
    total   : toplam parça sayısı; 0 = anlamlı değil.
    """

    stage: str
    message: str
    current: int = 0
    total: int = 0


# Çağıran tarafın sağladığı tüketici; her adımda bir olayla çağrılır.
ProgressCallback = Callable[[ProgressEvent], None]


def emit(progress: ProgressCallback | None, event: ProgressEvent) -> None:
    """None-güvenli yayın: callback yoksa sessizce geçer."""
    if progress is not None:
        progress(event)
