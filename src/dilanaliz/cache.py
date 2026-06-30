"""Basit disk önbelleği (LLM çağrıları için).

Amaç: aynı (model + sistem talimatı + kural + metin) bileşeni için API'yi tekrar
çağırmamak. Bu, kısıtlı ücretsiz kotada iteratif geliştirmeyi ve tekrarlanabilir
eval çalışmalarını mümkün kılar. temperature=0 olduğu için önbellek anlamca güvenli.

Anahtar tüm girdiyi (model_id + system + user_message) kapsadığından; prompt,
kural veya model değişince anahtar da değişir → önbellek kendiliğinden geçersizleşir.
Harici bağımlılık yok (air-gap dostu).
"""

from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path


def make_key(model_id: str, system: str, user_message: str) -> str:
    h = hashlib.sha256()
    h.update(model_id.encode("utf-8"))
    h.update(b"\x00")
    h.update(system.encode("utf-8"))
    h.update(b"\x00")
    h.update(user_message.encode("utf-8"))
    return h.hexdigest()


class DiskCache:
    """JSON dosyasında tutulan basit anahtar→değer önbelleği.

    Thread-safe: parçalar paralel işlendiğinde birden çok iş parçacığı aynı anda
    `set` çağırabilir. `set` oku-değiştir-yaz (dict mutasyonu + tüm dosyayı yazma)
    olduğundan kilitsiz çağrı kayıp yazmaya veya bozuk JSON'a yol açar. Bir
    `Lock` ile `get`/`set` serileştirilir; yazma yalnız cache-miss'te olduğundan
    kilit maliyeti ihmal edilebilir.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._lock = threading.Lock()
        self._data: dict[str, str] = {}
        if self._path.exists():
            try:
                self._data = json.loads(self._path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._data = {}

    def get(self, key: str) -> str | None:
        with self._lock:
            return self._data.get(key)

    def set(self, key: str, value: str) -> None:
        with self._lock:
            self._data[key] = value
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                json.dumps(self._data, ensure_ascii=False), encoding="utf-8"
            )
