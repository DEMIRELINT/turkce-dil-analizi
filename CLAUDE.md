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
büyük güncellemelerde raporlama atlanmamalıdır. Yapılan güncellemeler sonrasında kullanıcıya yapılacak açıklama, teknik terimlerle boğulmamalı ve net anlaşılır olmalıdır.**

**CLAUDE.md güncel tutulmalıdır.** Yapılan bir güncelleme, bu dosyada yazılı bir
bilgiyi (mimari, dizin yapısı, komutlar, ortam değişkenleri, kural kimlikleri,
bilinen sınırlar vb.) etkiliyor ya da burada belgelenmesi gereken yeni bir kural/
komut/seam getiriyorsa, **değişiklikle birlikte CLAUDE.md de güncellenmelidir** —
kod ile rehberin ayrışması (drift) önlenir. Değişiklik CLAUDE.md'yi
ilgilendirmiyorsa (yalnız yerel bir hata düzeltmesi gibi) güncelleme gerekmez.

---

## Proje Özeti

**Türkçe Doküman Dil Analizi** — Türkçe kurumsal metinleri **imla**, **dil
bilgisi**, **ton** ve **belge-geneli tutarlılık** eksenlerinde inceleyip her
sorun için *gerekçe + düzeltme önerisi* üreten hibrit bir sistem. Sistem
**önerir, düzeltmez**; son söz kullanıcıdadır.

Çekirdek felsefe: **deterministik olarak çözülebilen işi araca, yargı/bağlam
gerektiren işi yapay zekâya** bırakmak.

- **Tespit (deterministik):** Hunspell (`spylls`, saf-Python) + tr_TR sözlük —
  yazım hatalarını sıfır halüsinasyonla, kesin offset ile bulur. **Yalnız
  tespit eder, öneri ÜRETMEZ** — öneri her zaman bağlamı gören LLM'den gelir;
  LLM karar vermezse bulgu "(öneri yok ...)" yer tutucusuyla kalır.
- **Düzeltme + yargı (LLM):** Gemini — bağlama göre düzeltme önerir, dil bilgisi
  ve tonu analiz eder, özel adları eler.

Analiz **tek çağrı değil, kademeli geçişlerle** yürür (bkz. `analyzer.py`):
**yerel** (cümle: imla/noktalama/dil bilgisi), **ton** (paragraf) ve **bütün
belgede tutarlılık** geçişi. Uzun belge önce deterministik olarak parçalanır
(`chunk.py`); parça-içi offsetler kaynağa geri taşınır (rebasing). Girdi düz
metin **veya** `.docx` olabilir (`extract.py`); bir **web paneli** (`web/`)
docx yükleme + canlı ilerleme sunar.

`.docx` çıkarımı **etiketli bloklar** üretir: her blok türüyle işaretlenir
(`paragraf` / `baslik` / `tablo_hucresi`; `extract_docx_blocks` →
`BlockSpan`). Analiz bu haritayla yapısal gürültüyü deterministik süzer:
tablo hücrelerine imla/dil bilgisi/ton bulgusu üretilmez (yalnız tablodan
oluşan parçalar LLM'e hiç gönderilmez), başlıklarda tekrar/noktalama bulgusu
elenir, tablodaki ondalık-nokta kullanımı tek tek değil **belge-geneli TEK
özet bulguyla** raporlanır. Düz metin girdisinde (spans yok) süzme yoktur.

Detaylı anlatım için [README.md](README.md) dosyasına bakın.

---

## Dizin Yapısı

```
cli.py                      # Elle deneme girişi (CLI; metin stdin/arg veya .docx)
pyproject.toml              # Bağımlılıklar (pinli, air-gap uyumlu)
.env.example                # Örnek ortam değişkenleri (kopyala → .env)
dicts/tr_TR.{aff,dic}       # Hunspell Türkçe sözlüğü (air-gap: repoda bulundurulur)
src/dilanaliz/
  analyzer.py               # Ana orkestrasyon (kademeli geçişler, paralel parça, span-farkında süzme, build_default_analyzer)
  spell.py                  # Hunspell deterministik imla TESPİTİ (öneri üretmez; Türkçe İ/I-farkında lookup; 4 harf altı denetlenmez)
  extract.py                # .docx → etiketli bloklar (paragraf/baslik/tablo_hucresi; satır-içi marker temizliği, ardışık tekrar tekilleştirme)
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
  index.html                # Panel arayüzü (canlı parça ızgarası, iki sütun, gruplama; rapor indir/kopyala — ajan-dostu Markdown)
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

# Ucuz kısmi ölçüm (yalnız ilgili id/ön-ekler — küçük kural değişikliklerinde)
EVAL_FILTER=imla-yabanci,temiz EVAL_DELAY_SEC=0 python eval/run_eval.py

# Sıralı vs paralel karşılaştırma (hız + eşdeğerlik; API gerektirir)
python eval/compare_parallel.py belge.docx  # küçük belgeyle: belgeyi 3× analiz eder

# Hızlı reçeteler
pytest tests/test_chunk.py -q               # tek modülü çalıştır
pytest -x -q                                # ilk hatada dur (hızlı geri bildirim)
pytest -k chunk                             # ada göre süz
python cli.py "Bu cümlede ki hata var."     # hızlı duman testi (gerçek API)
```

**Sorun giderme (hata alınca buraya bak — her seferinde önden çalıştırma):**

- **Beklenmedik "eksik/bayat sonuç":** önce `rm -rf .cache/` ve tekrar dene
  (bkz. Bilinen Sınırlar → bayat önbellek).
- **Sözlük/`HunspellChecker` hatası veya imla bulgusu hiç çıkmıyor:**
  `dicts/tr_TR.dic` var mı? Yoksa Hunspell katmanı sessizce kapanır.
- **`GEMINI_API_KEY` / kimlik hatası:** `.env` dolu mu, `.venv` aktif mi?
- **Bağlantı donuyor/timeout (kurumsal ağ):** `GOOGLE_GENAI_TRANSPORT=rest` dene.

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
| `EVAL_FILTER` | *(boş)* | Yalnız `eval/run_eval.py`'de: virgülle ayrılmış id/id-ön-eki listesi (örn. `imla-yabanci,temiz`) — yalnız eşleşen örnekleri çalıştırır. Ücretli API'de küçük kural değişikliklerinde tam 53 örneği göndermemek için; tam koşu yalnız büyük kilometre taşlarında (Faz sonu, PR öncesi) önerilir. |

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
- **Etiketli blok sözleşmesi** — `extract_docx_blocks` blok türü haritası
  (`BlockSpan`) döndürür; offsetler birleşik metinle birebir hizalıdır
  (`text[s.start:s.end]` bloğun kendisi). `analyzer.analyze_document(spans=...)`
  bu haritayla yapısal süzme yapar; süzme `_finalize` sıralamasından ÖNCE ve
  tamamen deterministiktir. Yeni blok türü/süzme kuralı eklerken bu hizalamayı
  ve determinizmi koru. Tutarlılık bulguları tablo aralıklarında da KORUNUR
  (birim çakışması tabloda geçerli) — bunu süzmeye dahil etme.
- **Hunspell yalnız tespitçidir** — `spell.py` öneri üretmez (`suggest()`
  çağrısı bilinçli kaldırıldı); öneri `_resolve_spelling`'de LLM'den gelir ve
  alıntının harf düzenine giydirilir (`match_case`). Hunspell'e yeniden öneri
  ürettirme — bağlamdan habersiz sözlük önerisi kopuk parçalara uydurma üretir.
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

### İş Bitti mi? (Definition of Done — koşullu)

İşi tamamlamadan aşağıdakileri **duruma göre** çalıştır. Hepsini her seferinde
körlemesine çalıştırma; özellikle API'li adımlar zaman ve para harcar.

- **Her zaman:** `pytest` (API gerektirmez, ucuz — kod değiştiyse çalıştır).
- **Prompt/kural değiştiyse:** `eval/run_eval.py` (öncesi/sonrası precision-recall
  karşılaştır) + `golden.jsonl`'e örnek ekle. *Yalnız* bu durumda — aksi hâlde
  gereksiz API maliyeti.
- **Deterministiklik/paralellik sözleşmesine dokundunsa:** `compare_parallel.py`.
- **Davranış/çıktı/mimari değiştiyse:** Büyük Güncelleme Raporu + gerekiyorsa
  CLAUDE.md güncellemesi (bkz. Öncelikli Kural).

---

## Üretilmiş / Elle Dokunulmayan Dosyalar

Bunlar araç tarafından üretilir veya hassastır; **elle düzenleme**, canlı sonuç
kaynağı sanma, gözden geçirmeden silme:

- **`.cache/`** — LLM yanıt önbelleği; canlı sonuç değildir (bayat olabilir).
  Elle düzenleme; şüpheli sonuçta topluca sil (`rm -rf .cache/`).
- **`eval/last_predictions.json`** — `run_eval.py`'nin ürettiği son tahmin
  dökümü; elle yazma, ölçüm çıktısıdır.
- **`dicts/tr_TR.{aff,dic}`** — dış sözlük (LibreOffice); elle düzeltme, vendor'la.
- **`.env`** — sırlar; commit'lenmez, içeriği yanıtlara/loglara yazılmaz.
- **`history/`** — web panelinin analiz geçmişi kayıtları (üretilmiş).

---

## Git / Dal / PR Kuralları

- **`main` tek doğruluk kaynağıdır — main'e yalnız TEST EDİLMİŞ kod iner.**
  Test makine seviyesindedir (`web/server.py`, `cli.py`, gerçek API); her
  değişiklik merge'den önce fiziksel bir makinede çalıştırılıp denenmelidir.
  makine ≠ dal.

- **Ev (macOS, yerel):** `~/Desktop/a-proje` altında `.venv` + dolu `.env`.
  Burada **doğrudan `main`'de** çalışılır: `git pull` → değişiklik → yerelde test
  → `git push`. Dal/PR seremonisi yok (tek kullanıcı, çakışma riski düşük).

- **Kurum — iki katman:**
  - *Claude Code Web (bulut):* değişikliği yazar ve `claude/...` **dalına** push
    eder; fiziksel makineye/`main`'e yazamaz. Kod bu aşamada TEST EDİLMEMİŞTİR.
  - *Kurum bilgisayarı (fiziksel):* webserver testi burada yapılır → Web'in dalı
    buraya çekilir ve çalıştırılır. Bu, günde **birçok kez**, her küçük
    değişiklikte olur.
  - **Sürtünmeyi azalt:** Web **tek bir feature dalında** kalsın (yeni oturumda
    yeni dal AÇMA, aynı dala devam et). Böylece fiziksel makine dal değiştirmez,
    yalnız `git pull --ff-only` yapar.

- **Kurum test döngüsü (fiziksel makinede):**
  ```bash
  git fetch origin
  git checkout -t origin/<claude/dal>   # ilk kez; zaten o daldaysan atla
  git pull --ff-only                    # Web'in son değişikliğini al
  python web/server.py                  # (veya python cli.py "...") test et
  ```
  Aktif dalı bul: `git branch -r --sort=-committerdate | grep claude/ | head -1`.

- **Test geçince:** dalı `main`'e indir (PR merge ya da fiziksel makinede
  `git checkout main && git merge --ff-only <dal> && git push`). main artık
  test edilmiştir. **Test kalırsa:** Web'de AYNI dalda düzelt, makinede tekrar
  `git pull` → tekrar test (main kirlenmez).

- **Ajan `main`'e onaysız push/merge yapmaz** — push/merge kullanıcı onayıyladır.
- **Commit mesajları Türkçe** ve büyük değişikliklerde "Ne / Neden / Etki"
  formatını içerir.
- **Commit'lenmeyecekler:** `.cache/` ve `.env` (`.gitignore`'da); büyük ikili
  dosyalar (ör. `.pdf`, kaynak belgeler) repoya girmez.
- Kullanıcı yeni bir chat başlangıcında çalıştığı ortamı (iş veya ev) belirtmezse kullanıcıya öncelikle nerede çalıştığını sor.

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
  Temiz dijital `.docx` tercih edilir. PDF'ten çevrilmiş `.docx`'lerde çıkarma
  katmanı satır-içi görsel işaretçilerini ve ardışık tekrar başlıkları süzer;
  ama metin kutusu kırpıntıları (yarım cümleler) metinde kalabilir ve "cümle
  eksik" bulguları üretebilir — bu belge kalitesinin ürünüdür.
- **4 harften kısa kelimeler imla denetimine girmez.** Kopuk ek parçaları
  ("nde", "nda") sahte bulgu üretmesin diye bilinçli eşik; 1-3 harfli gerçek
  kelime hatası bu katmanda yakalanmaz (bkz. `rules.md` → Bilinen Sınırlar).
- **Tablo verisi dil denetimi dışıdır.** Etiketli bloklarda `tablo_hucresi`
  türü imla/dil bilgisi/ton geçişlerinden muaftır; tablodaki ondalık-nokta
  kullanımı tek TEK değil belge-geneli tek özet bulguyla raporlanır (N ≥ 3).
  Tablo hücresindeki bir yazım hatası bu yüzden raporlanmayabilir (bilinçli
  takas — tablo verisi düzyazı değildir).

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
