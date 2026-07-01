# CLAUDE.md

Bu dosya, bu depoda çalışan Claude Code (ve diğer yapay zekâ ajanları) için
rehberdir. Projenin mimarisini, çalışma kurallarını ve dikkat edilmesi gereken
noktaları özetler.

---

## ⚠️ Öncelikli Kural — Büyük Güncellemeleri Raporla

**Claude Code, yaptığı her büyük güncellemeyi (major update) raporlamayı
unutmamalıdır.** Mimariyi etkileyen, yeni bağımlılık ekleyen, davranışı veya
çıktı şemasını değiştiren ya da ölçüm (precision/recall) sonuçlarını etkileyen
her değişiklikten sonra:

1. **Ne değişti?** — yapılan değişikliğin kısa ve net özeti.
2. **Neden?** — değişikliğin gerekçesi.
3. **Etkisi ne?** — etkilenen dosyalar/modüller, metrik değişimi, geriye dönük
   uyumluluk (varsa kırılan şeyler).

Bu rapor; commit mesajında, PR açıklamasında ve kullanıcıya verilen yanıtta
açıkça belirtilmelidir. **Küçük düzeltmeler (typo, format) için gerekmez; ama
büyük güncellemelerde raporlama atlanmamalıdır.**

---

## Proje Özeti

**Türkçe Doküman Dil Analizi** — Türkçe kurumsal metinleri **imla**, **dil
bilgisi**, **ton** ve **belge-geneli tutarlılık** eksenlerinde inceleyip her
sorun için *gerekçe + düzeltme önerisi* üreten hibrit bir sistem. Sistem
**önerir, düzeltmez**; son söz kullanıcıdadır.

Çekirdek felsefe: **deterministik olarak çözülebilen işi araca, yargı/bağlam
gerektiren işi yapay zekâya** bırakmak.

- **Tespit (deterministik):** Hunspell (`spylls`, saf-Python) + tr_TR sözlük —
  yazım hatalarını sıfır halüsinasyonla, kesin offset ile bulur.
- **Düzeltme + yargı (LLM):** Gemini — bağlama göre düzeltme önerir, dil bilgisi
  ve tonu analiz eder, özel adları eler.

Analiz **tek çağrı değil, kademeli geçişlerle** yürür (bkz. `analyzer.py`):
**yerel** (cümle: imla/noktalama/dil bilgisi), **ton** (paragraf) ve **bütün
belgede tutarlılık** geçişi. Uzun belge önce deterministik olarak parçalanır
(`chunk.py`); parça-içi offsetler kaynağa geri taşınır (rebasing). Girdi düz
metin **veya** `.docx` olabilir (`extract.py`); bir **web paneli** (`web/`)
docx yükleme + canlı ilerleme sunar.

Detaylı anlatım için [README.md](README.md) dosyasına bakın.

---

## Dizin Yapısı

```
cli.py                      # Elle deneme girişi (CLI; metin stdin/arg veya .docx)
pyproject.toml              # Bağımlılıklar (pinli, air-gap uyumlu)
.env.example                # Örnek ortam değişkenleri (kopyala → .env)
dicts/tr_TR.{aff,dic}       # Hunspell Türkçe sözlüğü (air-gap: repoda bulundurulur)
src/dilanaliz/
  analyzer.py               # Ana orkestrasyon (kademeli geçişler, paralel parça, build_default_analyzer)
  spell.py                  # Hunspell tabanlı deterministik imla tespiti
  extract.py                # .docx → eksiksiz metin (docx2python; tablo/dipnot dahil)
  chunk.py                  # Uzun metni deterministik paragraf parçalarına böler (taşan paragraf cümleye iner)
  progress.py               # Geçiş ilerleme olayları (CLI stderr / web SSE)
  prompt.py                 # LLM davranışı (geçiş başına system prompt; kurallar ayrı)
  providers/                # LLM sağlayıcı soyutlaması (Gemini → vLLM değişebilir)
  rules/                    # RulesProvider + rules.md (kurallar koddan ayrı, kimlikli)
  schema.py                 # Pydantic v2 bulgu/çıktı şemaları (imla/dil_bilgisi/ton/tutarlilik)
  locate.py                 # Alıntıyı kaynakta konumlama (offset — LLM offset üretmez)
  postprocess.py            # Birleştirme + tekilleştirme + noop/bozuk öneri eleme
  cache.py                  # Disk önbelleği (.cache/llm_cache.json; thread-safe)
  config.py                 # Ortam değişkenleri / yapılandırma
web/
  server.py                 # Yerel panel sunucusu (stdlib http.server + SSE; docx yükle)
  index.html                # Panel arayüzü (canlı parça ızgarası, iki sütun, gruplama)
tests/                      # pytest birim testleri (API gerektirmez; sahte model kalıbı)
eval/
  golden.jsonl              # Elle etiketli altın set (pozitif + temiz-metin negatif örnekler)
  run_eval.py               # Eksen-bazlı precision/recall ölçümü (API gerektirir)
  compare_parallel.py       # Sıralı vs paralel: hız + çıktı eşdeğerliği (API gerektirir)
  *_test.txt                # Manuel deneme metinleri (kesme, gruplama, geniş kapsamlı)
```

---

## Sık Kullanılan Komutlar

```bash
# Kurulum
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env        # GEMINI_API_KEY girin

# Çalıştırma (CLI)
python cli.py "Bu cümlede ki hata var ve yanlız yazılmış."
cat metin.txt | python cli.py               # .txt → stdin ile ver (cli yalnız .docx'i dosya sanar)
python cli.py belge.docx > sonuc.json       # .docx → çıkar + parçala + analiz
CONCURRENCY=1 python cli.py belge.docx      # sıralı (paralelliği kapat)

# Web paneli (docx yükle / metin yapıştır + canlı ilerleme)
python web/server.py                        # http://127.0.0.1:8765

# Test (API gerektirmez)
pytest

# Ölçüm (altın set — API gerektirir)
EVAL_DELAY_SEC=0 python eval/run_eval.py

# Sıralı vs paralel karşılaştırma (hız + eşdeğerlik; API gerektirir)
python eval/compare_parallel.py belge.docx  # küçük belgeyle: belgeyi 3× analiz eder
```

---

## Ortam Değişkenleri (`.env`)

| Değişken | Varsayılan | Açıklama |
|---|---|---|
| `GEMINI_API_KEY` | *(zorunlu)* | Gemini API anahtarı. Repoda YOK, her makinede elle girilir. |
| `MODEL_ID` | `gemini-2.5-flash-lite` | Kullanılacak Gemini modeli. Daha güçlü sonuç için `-flash`/`-pro`. |
| `TEMPERATURE` | `0` | Tutarlılık için 0. (Not: 0 dahi tam deterministik değildir — bkz. Bilinen Sınırlar.) |
| `CONCURRENCY` | `6` | Eşzamanlı işlenecek parça sayısı. `1` → tamamen sıralı (eski) davranış. |
| `DICT_PATH` | `dicts/tr_TR` | Hunspell sözlük taban yolu (uzantısız). |
| `RULES_PATH` | *(boş)* | Harici kural dosyası; boşsa paketteki `rules/rules.md` kullanılır. |
| `LANGSMITH_TRACING` | `false` | Air-gap hijyeni: telemetri kapalı kalmalı. |
| `GOOGLE_GENAI_TRANSPORT` | *(boş)* | Opsiyonel Gemini REST taşıma anahtarı (gRPC yerine REST). |
| `EVAL_DELAY_SEC` | `13` | Yalnız `eval/run_eval.py`'de çağrılar arası gecikme; ücretli katmanda `0`. |

---

## Mimari "Seam"leri (Değiştirmeden Önce Oku)

Bu noktalar bilinçli olarak değiştirilebilir bırakıldı; dokunurken soyutlamayı
koru:

- **Davranış / Bilgi ayrımı** — `prompt.py` yalnız modelin *davranışını* tutar;
  *kurallar* `RulesProvider` üzerinden ayrı gelir. Kural değişikliği `rules.md`
  veya `.env`'deki `RULES_PATH` ile yapılır, **kod değişmeden**.
- **Sağlayıcı soyutlaması** — `providers/build_chat_model` bir LangChain
  `BaseChatModel` döndürür. Gemini'yi yerel vLLM ile değiştirmek analyzer'ı
  etkilememeli.
- **Katı JSON çıktı** — `with_structured_output` parse hatasını engeller; çıktı
  şeması `schema.py`'dedir, gevşetme.
- **Kademeli geçiş + parçalama** — orkestrasyon (`analyzer.py`) her kontrolü kendi
  bazında ayrı geçişte çalıştırır; parçalama (`chunk.py`) deterministik koddur.
  Parça-içi offsetler kaynağa geri taşınır (rebasing) — yeni geçiş/baz eklerken
  bu sözleşmeyi koru.
- **Paralel ama deterministik** — parçalar `CONCURRENCY` kadar eşzamanlı işlenir
  (ThreadPoolExecutor); ama çıktı işlenme sırasından BAĞIMSIZ olmalı. `_finalize`
  bulguları tam-sıra anahtarıyla (`_sort_key`) önce sıralar, sonra tekilleştirir —
  böylece `CONCURRENCY` ne olursa olsun sonuç birebir aynıdır. Yeni geçiş/bulgu
  eklerken bu deterministiklik sözleşmesini koru; önbellek (`cache.py`) ve ilerleme
  yayını thread-safe'tir (kilitli).
- **Belge-geneli tutarlılık parçalanamaz** — tutarlılık geçişi (terim/kısaltma
  çakışması) BÜTÜN metni tek çağrıda görür. Parçalarsan "AI"↔"Artificial
  Intelligence" gibi çapraz-parça çakışmaları göremez (kör nokta geri gelir).
- **Air-gap uyumu** — bağımlılıklar pinli; telemetri kapalı; gizli dış çağrı
  ekleme. `docx2python`, Hunspell ve web paneli (stdlib) dahil her şey yereldir.

---

## Test ve Doğrulama Süreci

- **Birim testler (`pytest`, API gerektirmez):** Her modülün kendi testi var
  (`tests/test_*.py`). LLM çağrıları **sahte model kalıbıyla** (`_FakeModel`,
  geçiş-farkında `_PassFakeStructured`) taklit edilir — ağ/anahtar gerekmez.
  Yeni kod eklerken bu kalıbı izle.
- **Ölçüm (`eval/run_eval.py`, API gerektirir):** `golden.jsonl` üzerinde
  eksen-bazlı precision/recall + temiz-metin yanlış-pozitif sayısı. Prompt veya
  kural değişikliği **buradan geçmeli** (öncesi/sonrası karşılaştır).
- **Paralellik doğrulama (`eval/compare_parallel.py`):** sıralı vs paralel hız +
  çıktı birebir eşdeğerliği (paylaşımlı önbellekle).
- **Manuel:** `web/server.py` veya `cli.py` ile gerçek API üzerinde deneme.
- **Yeni özellik eklerken beklenen iş:** (1) ilgili birim test; (2) prompt/kural
  değiştiysen `golden.jsonl`'e örnek + `run_eval.py` ölçümü; (3) davranış/çıktı
  değiştiyse Büyük Güncelleme Raporu.

---

## Git / Dal / PR Kuralları

- **İki makineli akış (bu projenin gerçek düzeni):**
  - *İş bilgisayarı:* Claude Code Web — repo'yu seçip **`main`'den** yeni bir
    `claude/...` dalı açar, çalışır ve **PR** açar.
  - *Ev (macOS):* `~/Desktop/a-proje` altında yerel `.venv` + dolu `.env`.
  - **`main` tek doğruluk kaynağıdır.** Her Web oturumu PR açar; o PR **`main`'e
    MERGE edilmezse** diğer makine değişikliği göremez (en sık yaşanan karışıklık).
    Makineler arası senkron: her iki tarafta `git checkout main && git pull`.
- **`main`'e izinsiz doğrudan push yapma** — değişiklik dal + PR üzerinden gider.
- **Ajan kendi açtığı PR'ı otomatik merge etmez** — merge kullanıcı onayıyla olur.
- **Commit mesajları Türkçe** ve büyük değişikliklerde "Ne / Neden / Etki"
  formatını içerir.
- **Commit'lenmeyecekler:** `.cache/` ve `.env` (`.gitignore`'da); büyük ikili
  dosyalar (ör. `.pdf`, kaynak belgeler) repoya girmez.

---

## Çalışma Kuralları / Kodlama Standartları

- **Türkçe yaz.** Kod yorumları, commit mesajları ve dokümantasyon Türkçe
  olmalı (mevcut tarz korunsun).
- **Ölçerek karar ver.** Prompt/kural değişiklikleri altın set (`eval/`)
  üzerinde precision/recall ile değerlendirilir; sezgiyle değil.
- **Yanlış-pozitif kritiktir.** Kurumsal denetçide temiz metinde hata uydurmak
  en büyük kusurdur; bunu artıran değişikliklerden kaçın.
- **Bağımlılık eklerken** pinli aralık kullan ve air-gap uyumunu gözet.
- **Formatter/linter yapılandırılmamıştır** — mevcut stil elle korunur (4 boşluk
  girinti, tip ipuçları, `from __future__ import annotations`, öz yorum).
- **Büyük güncellemelerde** yukarıdaki "Büyük Güncellemeleri Raporla" kuralını
  uygula.

---

## Yapılmaması Gerekenler (Anti-pattern'ler)

- **`schema.py`'yi gevşetme** — katı yapılandırılmış çıktı sözleşmesini bozma.
- **LLM'e offset ürettirme** — offset (`start`/`end`) yalnız `locate.py` ile
  kaynak metinden hesaplanır; LLM'e bırakmak uydurma konumlar üretir.
- **Kuralı ölçmeden değiştirme** — `eval/` üzerinde öncesi/sonrası bakmadan
  prompt/kural değiştirme.
- **Tutarlılık geçişini parçalama** — kör noktayı geri getirir (yukarıya bak).
- **Çıktı sırasını bozan değişiklik** — `_finalize` determinizmini bozarsan
  paralel/sıralı sonuçlar ayrışır.
- **Gizli dış çağrı / telemetri** ekleme — air-gap uyumunu kırar.
- **`.cache/`'i canlı sonuç kaynağı sanma** — bayat/eksik bir yanıt önbelleğe
  düşerse silinene dek döner (bkz. Bilinen Sınırlar).

---

## Bilinen Sınırlar

Bunlar bilinçli olarak çözülmemiş, ölçülmüş boşluklardır — model bunları tekrar
"bug" sanıp gereksiz uğraşmasın. (Kural boşlukları ayrıca `rules/rules.md` →
"Bilinen Sınırlar" bölümünde.)

- **Model determinizmi yoktur.** Gemini `temperature=0`'da bile aynı isteme
  çağrı-çağrı farklı yanıt verebilir; aynı metin iki koşuda biraz farklı
  bulgu üretebilir. Bu paralellikten DEĞİL, modelin doğasındandır.
- **Bayat önbellek.** Bir kez üretilen (belki eksik) yanıt `.cache/`'e kalıcı
  yazılır; kod/kural değişse de aynı metin için eski yanıt döner. Beklenmedik
  "eksik sonuç"ta ilk kontrol: `rm -rf .cache/` ve tekrar dene.
- **Sözlük-geçerli bağlamsal yazım hatası.** Hunspell morfolojik olarak
  kurulabilen ama bağlamda yanlış kelimeleri yakalayamaz (ör. "güncelleme"
  yerine "günceleme"). Prompt'u genişletmek yanlış-pozitif riskini artırır;
  bilinçli olarak dokunulmadı (`golden.jsonl`'de ölçülü FN örneği var).
- **Çapraz-geçiş çelişkisi.** Aynı ifade farklı geçişlerden (ör. imla + dil
  bilgisi) iki farklı öneri alabilir; geçişler birbirini görmez.
- **Uzun belge tutarlılık ölçeği.** Tutarlılık tek dev LLM çağrısıyla çalışır;
  50+ sayfada dikkat seyrelmesi nedeniyle çakışmaları kaçırabilir — kaçırmama
  garantisi yoktur. (Gelecek: deterministik terim-indeksi + LLM yargısı.)
- **OCR/çıkarma gürültüsü.** Girdi OCR ürünüyse İ/I karışması, kelime-içi
  boşluk/nokta gibi bozulmalar sahte bulgu üretir ("çöp girer, çöp çıkar").
  Temiz dijital `.docx` tercih edilir.

---

## Kural Kimlikleri (Hızlı Sözlük)

Her bulgu mümkünse bir `rule_id` taşır; kuralların tam tanımı
`src/dilanaliz/rules/rules.md`'dedir.

- **İmla:** `IMLA-DE-DA`, `IMLA-KI`, `IMLA-MI`, `IMLA-BITISIK`, `IMLA-AYRI`,
  `IMLA-YALNIZ`, `IMLA-YANLIS`, `IMLA-HERKES`, `IMLA-HERSEY`, `IMLA-YABANCI`,
  `IMLA-SAAT`, `IMLA-KESME`, `IMLA-DUZELTME-ISARETI`, `IMLA-TURKCE-KARAKTER`,
  `IMLA-NOKTALAMA`, `IMLA-BIRIM` (+ deterministik `HUNSPELL`).
- **Dil bilgisi:** `GRAMER-OZNE-YUKLEM`, `GRAMER-TAMLAMA`, `GRAMER-ANLATIM`,
  `GRAMER-CATI`, `GRAMER-EK-FIIL`, `GRAMER-TEKRAR`, `GRAMER-BOLUNMUS-KELIME`.
- **Ton:** `TON-RESMI`, `TON-NEZAKET`, `TON-HITAP-TUTARLILIK`, `TON-ACIKLIK`,
  `TON-KLISE`.
- **Tutarlılık:** belge-geneli terim/birim/kısaltma çakışması (`tutarlilik`).
