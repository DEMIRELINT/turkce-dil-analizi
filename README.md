# Türkçe Doküman Dil Analizi

Türkçe kurumsal metinleri **imla**, **dil bilgisi**, **ton** ve **belge-geneli
tutarlılık** eksenlerinde inceleyip her sorun için gerekçe ve düzeltme önerisi
üreten hibrit bir sistem. Deterministik olarak çözülebilen işi araca
(Hunspell), bağlam/yargı gerektiren işi yapay zekâya (Gemini) bırakır.

**Sistem önerir, düzeltmez** — son karar her zaman kullanıcıdadır.

## Özellikler

- Hunspell tabanlı sıfır-halüsinasyon imla tespiti + LLM ile bağlamsal düzeltme
- Dil bilgisi, ton/üslup ve belge-geneli tutarlılık denetimi
- `.docx` girdisi: gövde, tablo, metin kutusu, üst/altbilgi, dipnot dahil tam okuma
- Uzun belgelerde paralel işleme; çıktı her koşuda birebir aynı (deterministik)
- Komut satırı aracı ve yerel web paneli (canlı ilerleme, sıfır dış bağımlılık)
- Air-gap uyumlu: pinli bağımlılıklar, telemetri kapalı, gizli dış çağrı yok

## Kurulum

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env        # .env içine GEMINI_API_KEY girin

# Türkçe Hunspell sözlüğü (repoda yoksa)
mkdir -p dicts
curl -fsSL -o dicts/tr_TR.aff https://raw.githubusercontent.com/LibreOffice/dictionaries/master/tr_TR/tr_TR.aff
curl -fsSL -o dicts/tr_TR.dic https://raw.githubusercontent.com/LibreOffice/dictionaries/master/tr_TR/tr_TR.dic
```

Sözlük dosyaları yoksa deterministik imla katmanı sessizce devre dışı kalır,
yalnız LLM çalışır. Bağımlılıkların pinli sürüm listesi `requirements.txt`'te
de yer alır; projeyi çalıştırmak için yine de `pip install -e ".[dev]"` gerekir.

## Kullanım

```bash
# Komut satırı
python cli.py "Bu cümlede ki hata var ve yanlız yazılmış."
cat metin.txt | python cli.py
python cli.py belge.docx > sonuc.json

# Web paneli
python web/server.py            # http://127.0.0.1:8765
```

Çıktı, her bulgu için tip/alıntı/gerekçe/öneri/konum taşıyan yapılandırılmış
bir JSON'dur (bkz. `src/dilanaliz/schema.py`).

## Ortam Değişkenleri

En önemlileri: `GEMINI_API_KEY` (zorunlu), `MODEL_ID` (varsayılan
`gemini-3.5-flash`), `CONCURRENCY` (varsayılan `6`). Tam liste ve açıklamalar
için `.env.example`.

## Ölçüm

96 örneklik elle etiketlenmiş bir altın set üzerinde ölçülür; seçilen model
imla + dil bilgisi + tutarlılık ekseninde precision 0.96 / recall 1.00 sonucu
verir (bkz. `eval/`).

```bash
pytest                                    # birim testler (API gerekmez)
EVAL_DELAY_SEC=0 python eval/run_eval.py  # altın set ölçümü (API gerekir)
```

## Proje Yapısı

```
cli.py              # Komut satırı arayüzü
web/                 # Yerel web paneli (stdlib http.server + SSE)
src/dilanaliz/       # Analiz motoru (analyzer, spell, extract, chunk, ...)
eval/                # Altın set + ölçüm betikleri
tests/               # pytest (sahte model kalıbı, API gerekmez)
docs/                # Mimari gerekçeler ve bilinen sınırlar
```

Mimari kararların ve bilinçli sınırların ayrıntılı gerekçesi `docs/`
altındadır.
