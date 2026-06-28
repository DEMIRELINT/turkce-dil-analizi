# Türkçe Doküman Dil Analizi — Faz 1 (prompt-first çekirdek)

Türkçe kurumsal metinleri **imla**, **dil bilgisi** ve **ton** eksenlerinde
inceleyip her sorun için gerekçe + öneri üreten sistemin çekirdeği. Sistem
**önerir**, düzeltmez; son söz kullanıcıdadır.

Bu faz prompt tabanlıdır; mimari, dokümanlar geldiğinde **RAG**'e ve üretimde
**self-host** (kapalı ağ) ortamına *kod değişmeden* büyüyecek şekilde tasarlandı.

## Mimari (seam'ler)

- **Davranış / Bilgi ayrımı** — `prompt.py` yalnız modelin davranışını tutar;
  kurallar (`bilgi`) `RulesProvider` üzerinden ayrı gelir. Faz 1'de
  `StaticRulesProvider` tüm `rules/rules.md`'yi verir; Faz 2'de aynı imzayla
  retrieval gelir, analyzer değişmez.
- **Sağlayıcı soyutlaması** — `providers/build_chat_model` bir LangChain
  `BaseChatModel` döndürür. Bugün Gemini; Faz 8'de yerel vLLM aynı arayüzle.
- **Katı JSON çıktı** — `with_structured_output(LLMAnalysis)` parse hatasını
  kaldırır; offset/üstveri LLM'e gösterilmez, sonradan eklenir.
- **Offset konumlama** — `locate.py` alıntıyı kaynakta bulur (birebir → boşluk
  normalize → bulunamazsa konumsuz).
- **Hibrit motor (Faz 4 + 4.5)** — `spell.py` Hunspell (spylls, saf-Python) ile
  yazım hatalarını **deterministik tespit** eder (kesin offset). Gemini ise tek
  çağrıda: (a) bu şüpheli kelimeleri **bağlama göre düzeltir** veya "hata değil
  (özel ad)" diye **eler**, (b) dil bilgisi + ton + bağlamsal imla (de/da, ki, mi)
  bulur. Yani **tespit = Hunspell, düzeltme/doğrulama = Gemini**. Bulgular
  `postprocess.merge_findings` ile birleştirilip çakışanlar tekilleştirilir.

## Hunspell sözlüğü (deterministik imla)

`dicts/tr_TR.aff` ve `dicts/tr_TR.dic` gereklidir (LibreOffice tr_TR). Yoksa
deterministik katman otomatik devre dışı kalır (yalnız LLM çalışır). İndirme:

```bash
mkdir -p dicts
curl -fsSL -o dicts/tr_TR.aff https://raw.githubusercontent.com/LibreOffice/dictionaries/master/tr_TR/tr_TR.aff
curl -fsSL -o dicts/tr_TR.dic https://raw.githubusercontent.com/LibreOffice/dictionaries/master/tr_TR/tr_TR.dic
```

Air-gap'te bu iki dosya iç ağa vendor'lanır. Yol `.env`'de `DICT_PATH` ile
değiştirilebilir. Bilinen sınır: sözlükte olmayan özel ad/yabancı kelime
yanlış-pozitif olabilir → `HunspellChecker(whitelist=...)` ile beyaz liste.

## Kurulum

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # GEMINI_API_KEY değerini girin
```

## Kullanım

```bash
python cli.py "Bu cümlede ki hata var ve yanlız yazılmış."
echo "uzun metin..." | python cli.py
```

Çıktı, her bulgu için `type, excerpt, explanation, suggestion, rule_id,
start/end` içeren JSON'dur.

## Kural dökümanını değiştirme (kod değişmeden)

Kurallar [src/dilanaliz/rules/rules.md](src/dilanaliz/rules/rules.md) dosyasında
tutulur; analiz motorundan bağımsızdır. İki yol:

1. **Dosya içeriğini değiştir** — `rules.md`'yi düzenle/değiştir. Kod değişmez.
2. **Harici dökümana işaret et** — `.env`'de `RULES_PATH=/yol/resmi_kurallar.md`
   ver. Kod değişmez.

Döküman çok büyürse (bağlam bütçesini aşarsa) `StaticRulesProvider` yerine
`RetrievalRulesProvider` (RAG) takılır — analyzer yine değişmez (Faz 2).

> Not: Kural metni değişince LLM önbellek anahtarı da değişir; bir sonraki çalışma
> taze API çağrısı yapar.

## Ölçüm (altın set)

```bash
python eval/run_eval.py   # eksen-bazlı precision/recall + temiz-metin yanlış pozitif
pytest                    # locate + schema testleri (API gerektirmez)
```

`eval/golden.jsonl` elle etiketli tohum settir (imla/gramer/ton + temiz metinler).
Parametre/prompt değişiklikleri bu set üzerinde ölçülerek değerlendirilir.
Her çalıştırma `eval/last_predictions.json`'a tüm tahminleri yazar (kalibrasyon için).

### Ücretsiz kota ve önbellek

Gemini ücretsiz katmanı **günlük** istek sınırına sahiptir (model bazlı; `2.5-flash`
çok düşük, `2.5-flash-lite` en bol). Bu yüzden:
- Varsayılan model `gemini-2.5-flash-lite` (`.env`'de `MODEL_ID`).
- LLM çağrıları `.cache/llm_cache.json`'a **önbelleklenir**: aynı metin+kural+model
  bir daha API'ye gitmez. Prompt/kural/model değişince anahtar değişir, önbellek
  kendiliğinden tazelenir. Önbelleği sıfırlamak için `.cache/` silinir.
- Dakikalık limit için eval çağrı aralarında bekler (`EVAL_DELAY_SEC`, varsayılan 13;
  ücretli katmanda `EVAL_DELAY_SEC=0`).

### Metrik hedefleri (başlangıç)

| Eksen | Recall hedefi | Precision hedefi |
|---|---|---|
| imla | ≥ 0.85 | ≥ 0.90 |
| dil_bilgisi | ≥ 0.65 | ≥ 0.80 |
| ton | ≥ 0.60 | ≥ 0.80 |

Yanlış pozitif (özellikle temiz metinlerde) en kritik göstergedir; hedefler
altın set büyüdükçe revize edilir.

## Sonraki fazlar

- **Faz 2 — RAG:** `RetrievalRulesProvider` (langchain-chroma + splitter).
- **Faz 3 — Uzun metin:** hiyerarşik parçalama + paralel analiz + tekilleştirme.
- **Faz 4 — Hibrit (Zemberek):** deterministik imla katmanı, bulgu birleştirme.
  Not: "de/da, mi, ki" saf regex değil — morfoloji gerektirir.
- **Faz 8 — Self-host / air-gap:** `providers/vllm.py`, yerel embedding, telemetri
  kapalı, pinli bağımlılıkların iç ağa mirror'lanması.
