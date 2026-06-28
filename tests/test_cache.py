from dilanaliz.cache import DiskCache, make_key


def test_key_is_stable_and_input_sensitive():
    k1 = make_key("m", "sys", "user")
    k2 = make_key("m", "sys", "user")
    k3 = make_key("m", "sys", "user2")
    k4 = make_key("m2", "sys", "user")
    assert k1 == k2
    assert k1 != k3  # metin değişince anahtar değişir
    assert k1 != k4  # model değişince anahtar değişir


def test_disk_cache_roundtrip_and_persistence(tmp_path):
    path = tmp_path / "c.json"
    cache = DiskCache(path)
    assert cache.get("k") is None
    cache.set("k", '{"a": 1}')
    assert cache.get("k") == '{"a": 1}'

    # yeniden açılınca veri kalıcı olmalı
    reopened = DiskCache(path)
    assert reopened.get("k") == '{"a": 1}'


def test_corrupt_cache_file_is_tolerated(tmp_path):
    path = tmp_path / "c.json"
    path.write_text("{ bozuk json", encoding="utf-8")
    cache = DiskCache(path)  # patlamamalı
    assert cache.get("k") is None
