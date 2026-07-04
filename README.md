# Türkçe Doküman Dil Analizi

Türkçe kurumsal metinleri **imla**, **dil bilgisi**, **ton** ve **belge-geneli
tutarlılık** eksenlerinde inceleyip her sorun için *gerekçe + düzeltme önerisi*
üreten **hibrit** bir sistem. Deterministik olarak çözülebilen işi araca
(Hunspell), yargı/bağlam gerektiren işi yapay zekâya (Gemini) bırakır.

**Sistem önerir, düzeltmez** — son söz her zaman kullanıcıdadır.

---

## 1. Ne İşe Yarar? (Problem & Değer)

Kurumsal Türkçe metinlerde (resmî yazışma, rapor, prosedür) dil kalitesini
denetlemek elle yavaş, tutarsız ve gözden kaçmalara açıktır. Bu sistem metni
dört eksende tarar, her bulgu için **nerede/neden hatalı** olduğunu ve **nasıl
düzeltileceğini** söyler; kararı kullanıcıya bırakır.

Tasarımın çekirdek felsefesi: **deterministik olan işi araca, yargı gerektiren
işi LLM'e.** Yazım hatası gibi kesin çözülebilen bir sorunu kural motoru
(Hunspell) sıfır halüsinasyonla ve kesin konumla bulur; "bu özel ad mı, bu ton
kurumsal mı, bu terim belgede tutarlı mı" gibi bağlam/yargı gerektiren soruları
Gemini yanıtlar.

**Neden değerli:** Bir kurumsal denetçide en büyük kusur, temiz metinde hata
*uydurmaktır* (yanlış-pozitif). Bu yüzden sistem ölçülerek geliştirilir ve
yanlış-pozitifi düşük tutmak, kapsamı artırmaktan önce gelir.

## 2. Öne Çıkan Özellikler

- **Sıfır-halüsinasyon deterministik imla** — Hunspell (`spylls`, saf-Python) +
  `tr_TR` sözlüğü; yazım hatasını kesin offset ile bulur.
- **LLM ile bağlamsal yargı** — Gemini; aday kelimeleri bağlama göre eler (özel
  ad/terim), düzeltme önerir, dil bilgisi ve tonu değerlendirir.
- **Kademeli geçişler** — yerel (cümle), ton (paragraf), tutarlılık (belge) ayrı
  geçişlerde çalışır; her eksen kendi bazında incelenir.
- **Belge-geneli tutarlılık** — aynı terim/birim/kısaltmanın farklı yazımlarını
  tek çağrıda, bütün metni görerek yakalar.
- **.docx tam çıkarma** — gövde + tablo + metin kutusu + üst/altbilgi + dipnot
  (`docx2python`).
- **Paralel ama deterministik** — parçalar eşzamanlı işlenir; çıktı işlenme
  sırasından bağımsız, birebir aynıdır.
- **Air-gap uyumu** — bağımlılıklar pinli, telemetri kapalı, gizli dış çağrı yok;
  sözlük ve web paneli dahil her şey yerel.
- **Canlı web paneli** — docx yükle / metin yapıştır + gerçek-zamanlı ilerleme
  (yalnız stdlib, sıfır ek bağımlılık).

## 3. Nasıl Çalışır? — Mimari & Algoritmik Akış ⭐

Analiz tek bir dev çağrı değil; **deterministik parçalama + kademeli LLM
geçişleri**dir. Uçtan uca boru hattı:

```
  Girdi (.docx / düz metin)
        │
        ▼
  extract.py ──► tam metin (tablo/dipnot/altbilgi dahil)
        │
        ▼
  chunk.py ────► [parça 1] [parça 2] … [parça N]   (deterministik; offset korunur)
        │
        ├─ her parça (paralel, CONCURRENCY kadar):
        │     ├─ yerel geçiş  : Hunspell adayları + noktalama/dil bilgisi/imla
        │     └─ ton geçişi   : üslup/nezaket/resmiyet
        │     └─ offset rebasing (parça-içi → kaynak)
        │
        └─ bütün belge (tek çağrı):
              tutarlılık geçişi : terim/birim/kısaltma çakışması
        │
        ▼
  postprocess ─► noop ele + birleştir + deterministik sırala + tekilleştir
        │
        ▼
  AnalysisResult (JSON)
```

**3.1 Girdi.** Düz metin veya `.docx`. `.docx`'te `extract.py` gövdenin
yanında tablo, metin kutusu, üst/altbilgi ve dipnotları da çıkarır; okunan/
okunamayan içeriği bir rapor (`ExtractionReport`) ile bildirir. Görseller:
tek başına duran (kendi satırındaki) bir görsel tamamen atılır; cümle
içinde geçen bir görsel `[görsel]` yer tutucusuna dönüşür (cümle bütünlüğü
korunur, LLM bunu yok sayar).

**3.2 Parçalama.** [chunk.py](src/dilanaliz/chunk.py) uzun metni **deterministik**
(AI değil) böler. Birim paragraftır (boş satırla ayrılmış blok), böylece cümle
asla ortadan kesilmez; bütçeyi (`max_chars=3000`) aşan paragraf, kısaltma/sayı/
baş-harf korumalı cümle sınırından bölünür. Her parça kaynağın **birebir
dilimidir** ve başlangıç offsetini taşır — parça-içi bulgu offsetleri kaynağa
geri taşınabilir (*rebasing*).

**3.3 Kademeli geçişler.** [analyzer.py](src/dilanaliz/analyzer.py) her kontrolü
ayrı geçişte çalıştırır: **yerel** (cümle: imla + noktalama + dil bilgisi),
**ton** (paragraf), **tutarlılık** (belge). *Niçin ayrı?* Her eksen farklı bir
bağlam penceresi ister; birini diğerinin gürültüsünden ayırmak isabeti artırır.

**3.4 Deterministik imla + LLM ayrımı — Hunspell neden TEK BAŞINA yetmiyor?**
Hunspell yalnız *"bu kelime Türkçede var mı yok mu"* sorusuna bakar — bir
**sözlük** denetimidir. Ama pek çok yazım hatası **sözlükte tamamen geçerli
kelimelerle** yapılır; Hunspell bunları yapısal olarak GÖREMEZ:

| Örnek | Hunspell'e göre | Gerçek durum |
|---|---|---|
| "Ben**de** geldim." | "bende" geçerli bir kelime → hata YOK | Bağlaç "de" burada AYRI yazılmalı — bağlama bakmadan anlaşılmaz |
| "Kaynak Telsiz**'**de sorun var." | "Telsiz'de" de "Telsizde" de tek başına geçerli | Hangisinin doğru olduğu "özel ad mı değil mi" kuralına bağlı, sözlüğe değil |
| "CPS, cihaza ihtiyacınız olacak." | virgül sözlüğün konusu değil | Virgülün yeri/gerekliliği bir **kural** meselesi (bağlaç, liste, zarf tümleci) |

Bu üç örnek de **kelime düzeyinde** doğru ama **kullanım düzeyinde** hatalı
olabilir — sözlük burada çaresiz kalır. Bu yüzden sistem iki katmanlı çalışır:

1. **Hunspell** ([spell.py](src/dilanaliz/spell.py)) — sözlükte OLMAYAN
   kelimeleri offset'leriyle bulur (deterministik, sıfır halüsinasyon, ama
   yalnız tespit — öneri üretmez).
2. **LLM + `rules.md`** — (a) Hunspell'in bulduğu şüpheli kelimelere bağlama
   göre karar verir (`LLMSpellingDecision`): gerçek hata mı, yoksa özel ad/
   terim mi? Karar vermezse tespit kaybolmasın diye Hunspell bulgusu korunur
   (fallback). (b) Hunspell'in hiç *göremeyeceği*, sözlükte geçerli ama
   bağlamda yanlış kullanılan yazım kurallarını (de/da, ki, mi ayrımı,
   bitişik/ayrı yazım, kesme işareti, noktalama, birim yazımı) **kendi
   başına** tarar — bu kuralların kaynağı `rules.md`'dir (bkz. §9).

**3.5 Offset üretimi.** LLM offset **üretmez** (uydurma konum riski).
[locate.py](src/dilanaliz/locate.py) her bulgunun `excerpt`'ini kaynak metinde
konumlayıp `start`/`end` hesaplar.

**3.6 Birleştirme.** [postprocess.py](src/dilanaliz/postprocess.py) noop/bozuk
önerileri eler; `_finalize` bulguları **önce** tam-sıra anahtarıyla sıralar,
**sonra** tekilleştirir.

**3.7 Paralel ama deterministik.** Parçalar `CONCURRENCY` kadar eşzamanlı
işlenir (`ThreadPoolExecutor`); en uzun süren tutarlılık çağrısı ilk gönderilip
parça işleriyle örtüştürülür. Deterministik sıralama sayesinde `CONCURRENCY` ne
olursa olsun çıktı birebir aynıdır. Önbellek (`cache.py`) ve ilerleme yayını
thread-safe'tir (kilitli). **Tutarlılık geçişi parçalanamaz** — parçalanırsa
"AI" ↔ "Artificial Intelligence" gibi çapraz-parça çakışmaları görülmez.

## 4. Teknoloji Yığını (Ne + Niçin) ⭐

| Katman | Teknoloji | Niçin |
|---|---|---|
| LLM | **Gemini** (`gemini-2.5-flash-lite`) | Bağlam/yargı gerektiren düzeltme, dil bilgisi ve ton için. `flash-lite` geliştirme/eval'de en bol ücretsiz kotayı verir; nihai kalite için `-flash`/`-pro`'ya yükseltilebilir. |
| İmla motoru | **spylls** (saf-Python Hunspell) | Yazım hatasını deterministik + sıfır halüsinasyonla bulur. Saf-Python olması JVM/dış ikili gerektirmez → **air-gap** uyumlu. |
| Sözlük | `dicts/tr_TR.{aff,dic}` (LibreOffice) | Türkçe morfolojik sözlük; repoda/yerel ağda bulundurulur. |
| Belge çıkarma | **docx2python** | `.docx`'ten tablo/metin kutusu/üst-altbilgi/dipnot dahil eksiksiz metin; saf Python, ağ gerektirmez. |
| Orkestrasyon | **langchain-core** + `with_structured_output` | Sağlayıcıdan bağımsız `BaseChatModel` soyutlaması; katı JSON çıktı → parse hatası olmaz. |
| Şema/doğrulama | **Pydantic v2** | Çıktı sözleşmesini tipli ve doğrulanmış tutar (`schema.py`). |
| Web paneli | **stdlib** `http.server` + SSE | Canlı ilerleme için **sıfır yeni bağımlılık**; harici CDN/font/script yok. |

Python **≥ 3.11**. Tüm bağımlılıklar **pinli aralıkta** — kapalı ağa (air-gap)
mirror/vendor edilebilsin diye. Meta `langchain` paketi değil, modüler
`langchain-core` kullanılır.

## 5. Kurulum

```bash
# 1) Sanal ortam
python -m venv .venv && source .venv/bin/activate

# 2) Bağımlılıklar (geliştirme ekleriyle)
pip install -e ".[dev]"

# 3) Ortam değişkenleri
cp .env.example .env        # .env içine GEMINI_API_KEY girin

# 4) Türkçe Hunspell sözlüğü (repoda yoksa)
mkdir -p dicts
curl -fsSL -o dicts/tr_TR.aff https://raw.githubusercontent.com/LibreOffice/dictionaries/master/tr_TR/tr_TR.aff
curl -fsSL -o dicts/tr_TR.dic https://raw.githubusercontent.com/LibreOffice/dictionaries/master/tr_TR/tr_TR.dic
```

> **Not:** Sözlük dosyaları yoksa deterministik imla katmanı (Hunspell) sessizce
> devre dışı kalır ve yalnız LLM çalışır. Air-gap ortamda bu iki dosya yerel
> ağdan vendor'lanır.

## 6. Kullanım

### 6.1 CLI

```bash
# Doğrudan metin
python cli.py "Bu cümlede ki hata var ve yanlız yazılmış."

# stdin (.txt için önerilen — cli yalnız .docx'i dosya sanar)
cat metin.txt | python cli.py

# .docx → çıkar + parçala + analiz
python cli.py belge.docx > sonuc.json

# Sıralı (paralelliği kapat)
CONCURRENCY=1 python cli.py belge.docx
```

Çıktı **JSON olarak stdout**'a yazılır; ilerleme mesajları **stderr**'e akar
(boru hattı bozulmaz). Metin verilmezse çıkış kodu `2`.

### 6.2 Web paneli

```bash
python web/server.py            # http://127.0.0.1:8765 (PORT ile değiştirilebilir)
```

docx yükleyip veya metin yapıştırıp canlı ilerlemeyle analiz eder (bkz. §10).

### 6.3 Örnek çıktı (kısaltılmış)

```json
{
  "findings": [
    {
      "type": "imla",
      "excerpt": "cümlede ki",
      "explanation": "Bağlaç olan 'ki' ayrı yazılır; ama burada ek olan '-ki' bitişik olmalı.",
      "suggestion": "cümledeki",
      "rule_id": "IMLA-KI",
      "confidence": 0.95,
      "start": 4,
      "end": 14
    }
  ],
  "model_id": "gemini-2.5-flash-lite",
  "text_len": 47
}
```

## 7. Çıktı Şeması (JSON Sözleşmesi)

Şema [schema.py](src/dilanaliz/schema.py)'de Pydantic v2 ile tanımlıdır.

**`AnalysisResult`** (kök):

| Alan | Tip | Açıklama |
|---|---|---|
| `findings` | `Finding[]` | Bulgu listesi |
| `model_id` | `str \| null` | Kullanılan model (üstveri) |
| `text_len` | `int \| null` | Kaynak metin uzunluğu (üstveri) |

**`Finding`** (tek bulgu):

| Alan | Tip | Açıklama |
|---|---|---|
| `type` | `imla \| dil_bilgisi \| ton \| tutarlilik` | Bulgunun ekseni |
| `excerpt` | `str` | Metinden **birebir** alınan en kısa alıntı |
| `explanation` | `str` | Sorunun kısa gerekçesi |
| `suggestion` | `str` | Önerilen düzeltme (uygulama kullanıcıya bırakılır) |
| `rule_id` | `str \| null` | Tetikleyen kuralın kimliği (varsa) |
| `confidence` | `float \| null` | 0–1 arası güven |
| `start`, `end` | `int \| null` | Kaynak metindeki offset — **LLM üretmez**, `locate.py` hesaplar |

> LLM yalnız `LLMFinding`/`LLMSpellingDecision` alanlarını üretir; offset ve
> üstveri sonradan analyzer/locate tarafından eklenir. Böylece modele offset
> göstermeyiz ve uydurma konum riskini kaldırırız.

## 8. Ortam Değişkenleri (`.env`)

| Değişken | Varsayılan | Açıklama |
|---|---|---|
| `GEMINI_API_KEY` | *(zorunlu)* | Gemini API anahtarı. Repoda yok; her makinede elle girilir. |
| `MODEL_ID` | `gemini-2.5-flash-lite` | Gemini modeli. Daha güçlü sonuç için `-flash`/`-pro`. |
| `TEMPERATURE` | `0` | Tutarlılık için 0 (yine de tam deterministik değildir — §14). |
| `CONCURRENCY` | `6` | Eşzamanlı işlenecek parça sayısı. `1` → tamamen sıralı. |
| `DICT_PATH` | `dicts/tr_TR` | Hunspell sözlük taban yolu (uzantısız). |
| `RULES_PATH` | *(boş)* | Harici kural dosyası; boşsa paketteki `rules/rules.md`. |
| `LANGSMITH_TRACING` | `false` | Air-gap hijyeni: telemetri kapalı kalmalı. |
| `GOOGLE_GENAI_TRANSPORT` | *(boş)* | Gemini taşıma katmanı: `rest \| grpc \| grpc_asyncio`. Kurumsal ağda gRPC (HTTP/2) engelliyse `rest`. |
| `EVAL_DELAY_SEC` | `13` | Yalnız `run_eval.py`; çağrılar arası gecikme (ücretsiz kota). Ücretli katmanda `0`. |
| `EVAL_FILTER` | *(boş)* | Yalnız `run_eval.py`; virgülle ayrılmış id/id-ön-eki listesi (örn. `imla-yabanci,temiz`) — küçük kural değişikliklerinde tam altın seti göndermeden ucuz kısmi ölçüm. |
| `PORT` | `8765` | *(web)* Panel portu. |
| `HISTORY_DIR` | `./history` | *(web)* Analiz geçmişi kayıt klasörü. |

## 9. Kural Dökümanı & Özelleştirme

**Dört eksen, iki motor.** Sistem 4 eksende bulgu üretir; her eksende görevli
motor ve kaynağı farklıdır:

| Eksen | Motor | Kaynağı ne? |
|---|---|---|
| **İmla — kelime düzeyi** | Hunspell (sözlük) | TDK sözlüğü (`tr_TR.dic`) |
| **İmla — bağlamsal** (de/da, ki, mi, bitişik/ayrı, kesme, noktalama, birim) | LLM (`rules.md` A bölümü) | **TDK Yazım Kılavuzu** |
| **Dil bilgisi** (özne-yüklem, tamlama, çatı, anlatım bozukluğu) | LLM (`rules.md` B bölümü) | Genel Türkçe dil bilgisi (TDK'nin Yazım Kılavuzu'nun **kapsamı dışında** — kılavuz "nasıl yazılır" der, "cümle doğru mu kurulmuş" demez) |
| **Ton/üslup** | LLM (`rules.md` C bölümü) | Kurumsal yazışma normları (TDK'nin konusu değil) |
| **Tutarlılık** | LLM (belge-geneli, ayrı geçiş) | Redaksiyon pratiği (TDK'nin konusu değil) |

Yalnız **"İmla — bağlamsal"** satırı TDK'nin Yazım Kılavuzu'na doğrudan
bağlanabilir (kaynak: [tdk.gov.tr/icerik/yazim-kurallari](https://tdk.gov.tr/kategori/icerik/yazim-kurallari/)) —
çünkü Hunspell'in kelime-sözlüğü ile çözemediği, ama yine de "TDK ne diyor"
sorusuna kesin cevabı olan tek eksen budur (bkz. §3.4). Diğer üç eksen farklı
bilgi alanlarına dayanır; TDK'ya zorla bağlanırsa kaynağı olmayan kural
uydurulmuş olur.

**Davranış / Bilgi ayrımı:** [prompt.py](src/dilanaliz/prompt.py) yalnız modelin
*davranışını* tutar; *kurallar* `RulesProvider` üzerinden ayrı gelir
([rules/rules.md](src/dilanaliz/rules/rules.md)). Kural değiştirmek için **kod
değişmez** — `rules.md`'yi düzenle veya `.env`'de `RULES_PATH` ile kendi
kurumsal kural dökümanını göster.

Her bulgu mümkünse bir `rule_id` taşır:

- **İmla:** `IMLA-DE-DA`, `IMLA-KI`, `IMLA-MI`, `IMLA-BITISIK`, `IMLA-AYRI`,
  `IMLA-BAGLAMSAL-KARISTIRMA`, `IMLA-YALNIZ`, `IMLA-YANLIS`, `IMLA-HERKES`,
  `IMLA-HERSEY`, `IMLA-YABANCI`, `IMLA-SAAT`, `IMLA-KESME`, `IMLA-KISALTMA`,
  `IMLA-SIRA-SAYI`, `IMLA-DUZELTME-ISARETI`, `IMLA-TURKCE-KARAKTER`,
  `IMLA-NOKTALAMA`, `IMLA-BIRIM` (+ deterministik `HUNSPELL`).
- **Dil bilgisi:** `GRAMER-OZNE-YUKLEM`, `GRAMER-TAMLAMA`, `GRAMER-ANLATIM`,
  `GRAMER-CATI`, `GRAMER-EK-FIIL`, `GRAMER-SAYI-UYUM`, `GRAMER-TEKRAR`,
  `GRAMER-BOLUNMUS-KELIME`.
- **Ton:** `TON-RESMI`, `TON-NEZAKET`, `TON-HITAP-TUTARLILIK`, `TON-ACIKLIK`,
  `TON-KLISE`.
- **Tutarlılık:** belge-geneli terim/birim/kısaltma çakışması (`tutarlilik`).

> `RulesProvider` soyutlaması ileride **RAG** (metne göre ilgili kuralı getirme)
> yolunun geçeceği yerdir; bugün `StaticRulesProvider` tüm dökümanı verir.

## 10. Web Paneli Özellikleri

[web/server.py](web/server.py) (stdlib `http.server` + SSE) +
[web/index.html](web/index.html).

- **Girdi:** `.docx` sürükle-bırak **veya** metin yapıştır.
- **Canlı ilerleme:** SSE ile adım adım; **parça ızgarası** paralel işlemeyi
  görselleştirir (her hücre bir parça, aynı anda işlenenler görünür).
- **İki sütun sonuç:** solda bulgularla vurgulanmış kaynak metin, sağda
  eksen-bazlı bulgu kartları.
- **Bulgu gruplama:** aynı bulgu belgede kaç kez geçerse geçsin tek kartta
  toplanır; her *occurrence*'a tıklayarak metinde gezinilir (uzun belgede raporu
  okunur tutar).
- **Log / geçmiş paneli:** önceki analizler diske kaydedilir; tıklayınca **token
  harcamadan** diskten yeniden görüntülenir, silinebilir.
- **Güvenlik:** yalnız `127.0.0.1`'e bağlanır; `GEMINI_API_KEY` sunucuda kalır,
  tarayıcıya gönderilmez; harici CDN/font/script yok (%100 yerel).

**Uçlar:** `GET /`, `GET /logo.png`, `POST /upload`, `GET /stream?job=<id>`,
`GET /history`, `GET /history/get?id=<id>`, `POST /history/delete?id=<id>`.

## 11. Ölçüm & Sonuçlar (Eval) ⭐

Prompt/kural değişiklikleri **sezgiyle değil, ölçülerek** değerlendirilir.
[eval/golden.jsonl](eval/golden.jsonl) elle etiketli altın settir (30 örnek;
pozitif bulgular + temiz-metin negatif örnekler; bazıları uzun-belge yolunu
ölçmek için `mode: document`).

[eval/run_eval.py](eval/run_eval.py) eksen-bazlı **precision/recall** + temiz
metinde yanlış-pozitif sayısı üretir. Eşleştirme yumuşaktır: tahmin, aynı eksende
ve alıntısı beklenenle örtüşen (biri diğerini içeren, büyük/küçük harf duyarsız)
bir beklenene denk gelirse Doğru Pozitif sayılır.

**Son ölçüm — 1 Temmuz 2026** (`last_predictions.json`, 30 örnek):

| Eksen | Precision | Recall | TP | FP | FN |
|---|---|---|---|---|---|
| imla | 1.00 | 0.85 | 11 | 0 | 2 |
| dil_bilgisi | 1.00 | 1.00 | 6 | 0 | 0 |
| ton | 0.56 | 1.00 | 5 | 4 | 0 |
| tutarlilik | 1.00 | 1.00 | 1 | 0 | 0 |
| **GENEL** | **0.85** | **0.92** | 23 | 4 | 2 |

**Temiz metinlerde yanlış-pozitif: 0.**

Okuma: imla/dil bilgisi/tutarlılık precision'ı tam; **ton** ekseni recall'u tam
ama precision düşük (modelin savunulabilir ama etiketlenmemiş ton bulguları FP
yazıyor) — kalibrasyon açık nokta. İmla recall'undaki 2 FN, sözlük-geçerli
bağlamsal hataların bilinçli boşluğudur (§14).

```bash
EVAL_DELAY_SEC=0 python eval/run_eval.py        # yeniden ölç (API gerekli)
python eval/compare_parallel.py belge.docx      # sıralı-vs-paralel hız + eşdeğerlik
```

`compare_parallel.py` iki şeyi doğrular: (1) paralelin hız kazancı, (2) sıralı ve
paralel çıktının **birebir aynı** olması (belgeyi 3× analiz eder → küçük belgeyle
çalıştırın).

## 12. Test

```bash
pytest        # tüm birim testler — API/anahtar GEREKTİRMEZ
```

LLM çağrıları **sahte model kalıbıyla** (`_FakeModel`, geçiş-farkında
`_PassFakeStructured`) taklit edilir. Kapsam: analyzer, spell, chunk, extract,
locate, schema, postprocess, cache, progress, paralel eşdeğerlik, web.

## 13. Proje Yapısı

```
cli.py                      # CLI girişi (metin/stdin/.docx)
web/server.py               # Yerel panel (stdlib http.server + SSE)
web/index.html              # Panel arayüzü
src/dilanaliz/
  analyzer.py               # Orkestrasyon: kademeli geçiş, paralel parça, _finalize
  spell.py                  # Hunspell deterministik imla tespiti
  extract.py                # .docx → eksiksiz metin (docx2python)
  chunk.py                  # Deterministik paragraf/cümle parçalama
  locate.py                 # excerpt → kaynak offset (LLM offset üretmez)
  postprocess.py            # Birleştir + tekilleştir + noop/bozuk eleme
  prompt.py                 # Geçiş başına system prompt (davranış)
  providers/                # LLM sağlayıcı soyutlaması (Gemini → vLLM değişebilir)
  rules/                    # RulesProvider + rules.md (kurallar koddan ayrı)
  schema.py                 # Pydantic v2 şemaları
  cache.py                  # Disk önbelleği (thread-safe)
  progress.py               # İlerleme olayları (CLI stderr / web SSE)
  config.py                 # Ortam değişkenleri
eval/                       # golden.jsonl + run_eval.py + compare_parallel.py
tests/                      # pytest (sahte model kalıbı; API gerekmez)
dicts/tr_TR.{aff,dic}       # Hunspell Türkçe sözlüğü
```

## 14. Tasarım Kararları & Bilinçli Sınırlar

**Mimari seam'ler** (değiştirirken soyutlamayı koru):

- **Sağlayıcı soyutlaması** — `providers/build_chat_model` bir `BaseChatModel`
  döndürür; Gemini'yi yerel vLLM ile değiştirmek analyzer'ı etkilemez.
- **Davranış / Bilgi ayrımı** — davranış `prompt.py`'de, kurallar `rules.md`'de.
- **Katı JSON çıktı** — `with_structured_output` parse hatasını kaldırır; şema
  gevşetilmez.
- **Konumlanamayan bulgu sessizce elenir** — `locate.py` bir alıntıyı kaynakta
  bulamazsa offseti `None` bırakır; `postprocess.drop_unlocated_findings`
  bunu `_finalize`'da eler. Bu genelde LLM'in `rules.md`'deki bir "Yanlış:"
  örneğini analiz edilen metnin DOĞRU yazılmış hâliyle karıştırıp var
  olmayan bir alıntı üretmesini (halüsinasyon) engeller.
- **Parçalanamaz tutarlılık** — tüm belgeyi tek çağrıda görür (çapraz-parça
  çakışmaları için).
- **Paralel-ama-deterministik** — `_finalize` sıralayıp tekilleştirir; çıktı
  `CONCURRENCY`'den bağımsızdır.

**Bilinen sınırlar** (bug değil, ölçülmüş boşluk):

- **Model determinizmi yoktur.** Gemini `temperature=0`'da bile aynı metne
  çağrı-çağrı biraz farklı yanıt verebilir; bu paralellikten değil modelin
  doğasından.
- **Bayat önbellek.** Bir kez üretilen (belki eksik) yanıt `.cache/`'e kalıcı
  yazılır; kod/kural değişse de eski yanıt döner. İlk kontrol: `rm -rf .cache/`.
- **Sözlük-geçerli bağlamsal hata.** Hunspell morfolojik olarak kurulabilen ama
  bağlamda yanlış kelimeleri GENEL olarak yakalayamaz. Prompt'u genel olarak
  genişletmek yanlış-pozitif riskini artırır; genel taramaya dokunulmadı.
  Dar bir istisna var: `IMLA-BAGLAMSAL-KARISTIRMA` yalnız iki ölçülmüş çift
  için (güncelleme/günceleme, yarın/yarin) bu sınırı kapalı liste olarak deler.
- **Çapraz-geçiş çelişkisi.** Aynı ifade farklı geçişlerden (imla + dil bilgisi)
  iki ayrı öneri alabilir; geçişler birbirini görmez.
- **Uzun belge tutarlılık ölçeği.** Tutarlılık tek dev çağrıyla çalışır; 50+
  sayfada çakışmaları kaçırabilir (garanti yok).
- **OCR/çıkarma gürültüsü.** OCR ürünü girdide İ/I karışması, kelime-içi boşluk
  gibi bozulmalar sahte bulgu üretir. Temiz dijital `.docx` tercih edilir.

## 15. Yol Haritası

- **Tamamlandı:** prompt-first çekirdek (Faz 1), deterministik imla + Hunspell,
  `.docx` çıkarma (Faz 3), kademeli geçiş + parçalama, paralel-deterministik
  yürütme, web paneli + geçmiş.
- **Bekleyen — RAG:** `RulesProvider` üzerinden metne göre ilgili kuralı getirme
  (statik döküman yerine); §9'daki soyutlama bu yol için hazır.
- **Bekleyen — tutarlılık ölçeği:** deterministik terim-indeksi + LLM yargısı
  (uzun belgede dikkat seyrelmesini gidermek için).
- **Faz 8 — self-host / air-gap:** Gemini yerine yerel uç (vLLM). `providers/`
  soyutlaması sayesinde analyzer değişmeden sağlayıcı değişir.

## 16. Katkı / Geliştirme Kuralları

Ayrıntı için [CLAUDE.md](CLAUDE.md). Özet:

- **Türkçe yaz** (kod yorumu, commit, doküman).
- **Ölçerek karar ver** — prompt/kural değişikliği `eval/` üzerinde öncesi/
  sonrası karşılaştırılır.
- **Yanlış-pozitif kritiktir** — temiz metinde hata uydurmayı artıran
  değişikliklerden kaçın.
- **Air-gap uyumu** — bağımlılık pinli, telemetri kapalı, gizli dış çağrı yok.
- **Büyük güncellemeleri raporla** — Ne / Neden / Etki.
- **Git akışı:** `main` tek doğruluk kaynağı; değişiklik dal + PR üzerinden; ajan
  kendi PR'ını otomatik merge etmez.
