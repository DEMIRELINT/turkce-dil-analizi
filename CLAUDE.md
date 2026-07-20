# CLAUDE.md

Bu dosya, bu depoda çalışan Claude Code (ve diğer yapay zekâ ajanları) için
rehberdir. Buradaki maddeler **demir kurallardır** (ne yapılmalı/yapılmamalı);
her kuralın gerekçesi, iç işleyişi ve tarihçesi `docs/` altındaki bağlantılı
dosyalardadır — **ilgili koda dokunmadan önce bağlantıyı oku.**

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
açıkça belirtilmelidir. Küçük düzeltmeler (typo, format) için gerekmez.
**Kullanıcıya yapılacak açıklama teknik terimlerle boğulmamalı, net ve
anlaşılır olmalıdır.**

**CLAUDE.md ve `docs/` güncel tutulmalıdır.** Bir güncelleme buradaki ya da
`docs/mimari-seamler.md` / `docs/bilinen-sinirlar.md` /
`docs/sorun-giderme.md`'deki bir bilgiyi etkiliyorsa, **değişiklikle birlikte
ilgili dosya da güncellenmelidir** — kod ile rehberin ayrışması (drift)
önlenir. Yalnız yerel bir hata düzeltmesi gibi rehberi ilgilendirmeyen
değişikliklerde güncelleme gerekmez.

---

## Proje Özeti

**Türkçe Doküman Dil Analizi** — Türkçe kurumsal metinleri **imla**, **dil
bilgisi**, **ton** ve **belge-geneli tutarlılık** eksenlerinde inceleyip her
sorun için *gerekçe + düzeltme önerisi* üreten hibrit bir sistem. Sistem
**önerir, düzeltmez**; son söz kullanıcıdadır.

Çekirdek felsefe: **deterministik olarak çözülebilen işi araca, yargı/bağlam
gerektiren işi yapay zekâya** bırakmak.

- **Tespit (deterministik):** Hunspell (`spylls`) + tr_TR sözlük — yazım
  hatasını kesin offset ile bulur; öneri ÜRETMEZ (öneri LLM'den gelir).
- **Düzeltme + yargı (LLM):** Gemini — bağlama göre öneri, dil bilgisi/ton
  analizi, özel ad eleme.

Analiz kademeli geçişlerle yürür (`analyzer.py`): **yerel** (imla/noktalama/
dil bilgisi), **ton** (paragraf), **belge-geneli tutarlılık**. Uzun belge
deterministik parçalanır (`chunk.py`), offsetler kaynağa geri taşınır. Girdi
düz metin veya `.docx` (`extract.py` → etiketli bloklar; tablo/TOC yapısal
süzmeye girer); web paneli (`web/`) docx yükleme + canlı ilerleme sunar.

Detaylı anlatım için [README.md](README.md) dosyasına bakın.

---

## Dizin Yapısı

```
cli.py                      # Elle deneme girişi (CLI; metin stdin/arg veya .docx)
pyproject.toml              # Bağımlılıklar (pinli, air-gap uyumlu)
.env.example                # Örnek ortam değişkenleri (kopyala → .env)
dicts/tr_TR.{aff,dic}       # Hunspell Türkçe sözlüğü (air-gap: repoda bulundurulur)
docs/
  mimari-seamler.md         # Seam'lerin tam anlatımı (gerekçe + iç işleyiş)
  bilinen-sinirlar.md       # Bilinen sınırların tam anlatımı
  sorun-giderme.md          # Hata alınca bakılacak liste
src/dilanaliz/
  analyzer.py               # Ana orkestrasyon (kademeli geçişler, paralel parça, span-farkında süzme, tutarlılık map-reduce, build_default_analyzer)
  spell.py                  # Hunspell deterministik imla TESPİTİ (öneri üretmez; İ/I-farkında; 4 harf altı denetlenmez)
  extract.py                # .docx → etiketli bloklar (paragraf/baslik/tablo_hucresi/icindekiler; görsel yer tutucu, tekrar tekilleştirme)
  chunk.py                  # Uzun metni deterministik paragraf parçalarına böler (taşan paragraf cümleye iner)
  progress.py               # Geçiş ilerleme olayları (CLI stderr / web SSE)
  prompt.py                 # LLM davranışı (geçiş başına system prompt; kurallar ayrı; map-reduce promptları)
  providers/                # LLM sağlayıcı soyutlaması (Gemini → vLLM değişebilir)
  rules/                    # RulesProvider + rules.md (kurallar koddan ayrı, kimlikli)
  schema.py                 # Pydantic v2 bulgu/çıktı şemaları + Observation + TermEntry/LLMTermExtraction
  locate.py                 # Alıntıyı kaynakta konumlama (offset — LLM offset üretmez)
  postprocess.py            # Birleştirme + tekilleştirme + noop/bozuk öneri eleme
  cache.py                  # Disk önbelleği (.cache/llm_cache.json; thread-safe)
  config.py                 # Ortam değişkenleri / yapılandırma
web/
  server.py                 # Yerel panel sunucusu (stdlib http.server + SSE; docx yükle)
  index.html                # Panel arayüzü (canlı parça ızgarası, gruplama; rapor indir/kopyala)
tests/                      # pytest birim testleri (API gerektirmez; sahte model kalıbı)
eval/
  golden.jsonl              # Elle etiketli altın set (pozitif + temiz-metin negatif örnekler)
  run_eval.py               # Eksen-bazlı precision/recall ölçümü (API gerektirir)
  compare_parallel.py       # Sıralı vs paralel: hız + çıktı eşdeğerliği (API gerektirir)
  *_test.txt                # Manuel deneme metinleri
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

**Sorun giderme:** hata alınca önce [docs/sorun-giderme.md](docs/sorun-giderme.md).
İlk refleks — beklenmedik "eksik/bayat sonuç"ta: `rm -rf .cache/` ve tekrar dene.

---

## Ortam Değişkenleri (`.env`)

| Değişken | Varsayılan | Açıklama |
|---|---|---|
| `GEMINI_API_KEY` | *(zorunlu)* | Gemini API anahtarı. Repoda YOK, her makinede elle girilir. |
| `MODEL_ID` | `gemini-3.5-flash` | Gemini modeli. "lite" sınıfı KULLANILMAZ (kalıcı karar — bkz. `eval/runs/` model kıyası). gemini-2.5-flash 16 Ekim 2026'da kapanacak. |
| `TEMPERATURE` | `0` | Tutarlılık için 0. (0 dahi tam deterministik değildir — bkz. Bilinen Sınırlar.) |
| `CONCURRENCY` | `6` | Eşzamanlı parça sayısı. `1` → tamamen sıralı davranış. |
| `DICT_PATH` | `dicts/tr_TR` | Hunspell sözlük taban yolu (uzantısız). |
| `RULES_PATH` | *(boş)* | Harici kural dosyası; boşsa paketteki `rules/rules.md`. |
| `LANGSMITH_TRACING` | `false` | Air-gap hijyeni: telemetri kapalı kalmalı. |
| `GOOGLE_GENAI_TRANSPORT` | *(boş)* | Opsiyonel: gRPC yerine REST taşıma. |
| `LLM_TIMEOUT_SEC` | `60` | Tek LLM çağrısı üst zaman aşımı (sn). `0`/boş → sınırsız. |
| `CONSISTENCY_MAP_REDUCE_CHARS` | `16000` | Tutarlılık map-reduce eşiği (karakter). Belge aşarsa map-reduce; altında tek-çağrı yolu (altın-set bu yolda ölçülü). `0`/negatif → fiilen her belge map-reduce. |
| `EVAL_DELAY_SEC` | `13` | Yalnız `run_eval.py`: çağrılar arası gecikme; ücretli katmanda `0`. |
| `EVAL_FILTER` | *(boş)* | Yalnız `run_eval.py`: virgüllü id/ön-ek listesi — yalnız eşleşen örnekler koşar (ucuz kısmi ölçüm). Tam koşu yalnız büyük kilometre taşlarında. |

---

## Mimari "Seam"leri (Demir Kurallar)

Tam anlatım + gerekçeler: [docs/mimari-seamler.md](docs/mimari-seamler.md).
**Bir seam'e dokunmadan önce oradaki ilgili bölümü oku.** Özet kurallar:

- **Davranış / Bilgi ayrımı** — `prompt.py` yalnız davranış; kurallar
  `RulesProvider`'dan (`rules.md` / `RULES_PATH`), kod değişmeden. Sağlayıcı
  geçiş-farkındadır (purpose kesitleme); yeni geçiş eklerken
  `rules/static.py → _PURPOSE_KINDS` güncelle.
- **Sağlayıcı soyutlaması** — `providers/build_chat_model` LangChain
  `BaseChatModel` döndürür; Gemini→vLLM değişimi analyzer'ı etkilememeli.
- **Katı JSON çıktı** — şema `schema.py`'dedir, gevşetme.
- **Gözlem kanalı (`observations`) findings'ten AYRIDIR** — findings boru
  hattına HİÇ girmez, ölçüme girmez, arayüzde "doğrulanmamış" etiketiyle ayrı
  bölümde gösterilir. Yalnız yerel geçişin şemasında bir alandır.
- **Konumlanamayan bulgu elenir** — eleme kararı `_finalize`'dadır
  (`drop_unlocated_findings`); `locate.py` yalnız konumlar, politika koymaz.
  Yeni geçiş eklerken bu sözleşmeyi koru.
- **Bağlamca zaten karşılanmış öneri elenir** —
  `drop_context_satisfied_findings`, konumlama SONRASI çalışır (offset ister).
- **Kademeli geçiş + parçalama** — her kontrol kendi bazında ayrı geçiş;
  parça-içi offsetler kaynağa geri taşınır (rebasing) — sözleşmeyi koru.
- **Paralel ama deterministik** — çıktı işlenme sırasından BAĞIMSIZ olmalı;
  `_finalize` önce sıralar (`_sort_key`) sonra tekilleştirir. `CONCURRENCY`
  ne olursa olsun sonuç birebir aynı kalmalı.
- **Tutarlılık: küçük belgede tek çağrı, büyük belgede map-reduce** — naif
  "böl ve her parçaya ayrı tutarlılık sor" YASAK (kör nokta); reduce'un tek
  yargı adımı bütün adayları bir arada görür. Reduce `excerpt`'i kümedeki bir
  `surface` ile birebir olmalı ki konumlanabilsin.
- **Etiketli blok sözleşmesi** — `BlockSpan` offsetleri birleşik metinle
  birebir hizalı; yapısal süzme `_finalize`'dan ÖNCE ve deterministik.
  Tutarlılık bulguları tablo aralıklarında KORUNUR — süzmeye dahil etme.
- **Hunspell yalnız tespitçidir** — `suggest()` bilinçli kaldırıldı; öneri
  LLM'den gelir (`_resolve_spelling` + `match_case`). Geri ekleme.
- **Air-gap uyumu** — bağımlılıklar pinli, telemetri kapalı, gizli dış çağrı
  ekleme; her şey yereldir.
- **LLM hatası SINIFLANDIRILIR** — kalıcı (model yok) → yeniden deneme YOK,
  net "MODEL_ID güncelle" mesajı; geçici (timeout/ağ) → 3 deneme. Kalıcı
  hatada TÜM analiz durur (bilinçli) — sessiz-atlamaya çevirme.

---

## Test ve Doğrulama Süreci

- **Birim testler (`pytest`, API gerektirmez):** LLM çağrıları sahte model
  kalıbıyla (`_FakeModel`, geçiş-farkında `_PassFakeStructured`) taklit
  edilir. Yeni kod eklerken bu kalıbı izle.
- **Ölçüm (`eval/run_eval.py`, API gerektirir):** `golden.jsonl` üzerinde
  eksen-bazlı precision/recall + temiz-metin yanlış-pozitif sayısı. Prompt
  veya kural değişikliği **buradan geçmeli** (öncesi/sonrası karşılaştır).
- **Paralellik doğrulama (`eval/compare_parallel.py`):** sıralı vs paralel
  hız + çıktı birebir eşdeğerliği.
- **Manuel:** `web/server.py` veya `cli.py` ile gerçek API üzerinde deneme.

### İş Bitti mi? (Definition of Done — koşullu)

Hepsini körlemesine çalıştırma; API'li adımlar zaman ve para harcar.

- **Her zaman:** `pytest` (kod değiştiyse — ucuz).
- **Prompt/kural değiştiyse:** `run_eval.py` (öncesi/sonrası) +
  `golden.jsonl`'e örnek. *Yalnız* bu durumda.
- **Deterministiklik/paralellik sözleşmesine dokundunsa:** `compare_parallel.py`.
- **Davranış/çıktı/mimari değiştiyse:** Büyük Güncelleme Raporu + gerekiyorsa
  CLAUDE.md/`docs/` güncellemesi (bkz. Öncelikli Kural).

---

## Üretilmiş / Elle Dokunulmayan Dosyalar

**Elle düzenleme**, canlı sonuç kaynağı sanma, gözden geçirmeden silme:

- **`.cache/`** — LLM yanıt önbelleği; bayat olabilir. Şüpheli sonuçta
  topluca sil (`rm -rf .cache/`).
- **`eval/last_predictions.json`** — `run_eval.py` çıktısı; elle yazma.
- **`eval/runs/`** — koşu arşivleri; üretilmiş çıktıdır, commit'lenmez.
- **`dicts/tr_TR.{aff,dic}`** — dış sözlük (LibreOffice); elle düzeltme, vendor'la.
- **`.env`** — sırlar; commit'lenmez, içeriği yanıtlara/loglara yazılmaz.
- **`history/`** — web panelinin analiz geçmişi kayıtları (üretilmiş).

---

## Git / Dal / PR Kuralları

- **`main` tek doğruluk kaynağıdır — main'e yalnız TEST EDİLMİŞ kod iner.**
  Test makine seviyesindedir (`web/server.py`, `cli.py`, gerçek API); her
  değişiklik merge'den önce fiziksel bir makinede denenmelidir. makine ≠ dal.
- **Ev (macOS, yerel):** `~/Desktop/a-proje`, `.venv` + dolu `.env`.
  **Doğrudan `main`'de** çalışılır: `git pull` → değişiklik → yerel test →
  `git push`. Dal/PR seremonisi yok.
- **Kurum — iki katman:**
  - *Claude Code Web (bulut):* `claude/...` **dalına** push eder;
    fiziksel makineye/`main`'e yazamaz. Kod bu aşamada TEST EDİLMEMİŞTİR.
  - *Kurum bilgisayarı (fiziksel):* Web'in dalı çekilir, webserver testi
    burada yapılır — günde birçok kez.
  - **Sürtünmeyi azalt:** Web tek bir feature dalında kalsın (yeni oturumda
    yeni dal AÇMA); fiziksel makine yalnız `git pull --ff-only` yapar.
- **Kurum test döngüsü (fiziksel makinede):**
  ```bash
  git fetch origin
  git checkout -t origin/<claude/dal>   # ilk kez; zaten o daldaysan atla
  git pull --ff-only                    # Web'in son değişikliğini al
  python web/server.py                  # (veya python cli.py "...") test et
  ```
  Aktif dalı bul: `git branch -r --sort=-committerdate | grep claude/ | head -1`.
- **Test geçince:** dalı `main`'e indir (PR merge ya da `git checkout main &&
  git merge --ff-only <dal> && git push`). **Test kalırsa:** Web'de AYNI dalda
  düzelt, makinede tekrar `git pull` → tekrar test (main kirlenmez).
- **Ajan `main`'e onaysız push/merge yapmaz** — push/merge kullanıcı onayıyladır.
- **Commit mesajları Türkçe**; büyük değişikliklerde "Ne / Neden / Etki" formatı.
- **Commit'lenmeyecekler:** `.cache/`, `.env` (`.gitignore`'da); büyük ikili
  dosyalar (ör. `.pdf`, kaynak belgeler) repoya girmez.
- Kullanıcı yeni bir chat başlangıcında çalıştığı ortamı (iş veya ev)
  belirtmezse, öncelikle nerede çalıştığını sor.

---

## Çalışma Kuralları / Kodlama Standartları

- **Türkçe yaz.** Kod yorumları, commit mesajları ve dokümantasyon Türkçe.
- **Ölçerek karar ver.** Prompt/kural değişiklikleri altın set (`eval/`)
  üzerinde precision/recall ile değerlendirilir; sezgiyle değil.
- **Yanlış-pozitif kritiktir.** Temiz metinde hata uydurmak en büyük kusurdur;
  bunu artıran değişikliklerden kaçın.
- **Bağımlılık eklerken** pinli aralık kullan ve air-gap uyumunu gözet.
- **Formatter/linter yok** — mevcut stil elle korunur (4 boşluk girinti, tip
  ipuçları, `from __future__ import annotations`, öz yorum).
- **Büyük güncellemelerde** "Büyük Güncellemeleri Raporla" kuralını uygula.

---

## Yapılmaması Gerekenler (Anti-pattern'ler)

- **`schema.py`'yi gevşetme** — katı yapılandırılmış çıktı sözleşmesini bozma.
- **LLM'e offset ürettirme** — offset yalnız `locate.py` ile kaynak metinden
  hesaplanır; LLM'e bırakmak uydurma konumlar üretir.
- **Kuralı ölçmeden değiştirme** — `eval/` üzerinde öncesi/sonrası bakmadan
  prompt/kural değiştirme.
- **Tutarlılık yargısını naif parçalama** — her parçaya AYRI "tutarlılık bul"
  sorma; kör nokta döner. Çözüm map-reduce'tur (bkz. docs/mimari-seamler.md).
- **Gözlemi (`observations`) findings hattına sokma / bulgu gibi gösterme /
  puanlamaya katma** — ayrı, doğrulanmamış, düşük-güvenli kanaldır.
- **Çıktı sırasını bozan değişiklik** — `_finalize` determinizmini bozarsan
  paralel/sıralı sonuçlar ayrışır.
- **Gizli dış çağrı / telemetri ekleme** — air-gap uyumunu kırar.
- **`.cache/`'i canlı sonuç kaynağı sanma** — bayat yanıt silinene dek döner.

---

## Bilinen Sınırlar (Özet — bug sanma)

Bilinçli olarak çözülmemiş, ölçülmüş boşluklar; tam gerekçeler:
[docs/bilinen-sinirlar.md](docs/bilinen-sinirlar.md). (Kural boşlukları ayrıca
`rules/rules.md` → "Bilinen Sınırlar".)

- **Model determinizmi yoktur** — `temperature=0`'da bile koşular arası küçük
  farklar normaldir; paralellik hatası değildir.
- **Bayat önbellek** — `.cache/` eski yanıtı döndürür; ilk kontrol
  `rm -rf .cache/`.
- **Sözlük-geçerli bağlamsal yazım hatası yakalanmaz** (ör. "günceleme") —
  bilinçli; prompt genişletme yanlış-pozitif riskini artırır.
- **Çapraz-geçiş çelişkisi daraltıldı** — atomik düzeltme çıkarılamayan
  örtüşen bulgular hâlâ İKİSİ DE korunur; bilinçli kalan sınır.
- **Uzun belge tutarlılık ölçeği** — map-reduce'un bilinen kaçakları vardır
  (eşanlam etiket farkı, >3 varyantlı küme, salt harf-farkı ürün adları);
  hepsi bilinçli takastır.
- **OCR/çıkarma gürültüsü** — "çöp girer, çöp çıkar"; temiz dijital `.docx`
  tercih edilir. Metin kutusu kırpıntıları sahte "cümle eksik" üretebilir.
- **4 harften kısa kelimeler imla denetimine girmez** — bilinçli eşik.
- **Tablo hücresi ve İçindekiler (TOC) dil denetimi dışıdır** — imla/dil
  bilgisi/ton muaf; tutarlılık geçişinde DAHİL. Bilinçli takas.
- **Kalıcı LLM hatasında TÜM analiz durur** — tek parçayı sessizce atlama
  yoktur; bilinçli tercih (eksik rapor riski).

---

## Kural Kimlikleri (Hızlı Sözlük)

Her bulgu mümkünse bir `rule_id` taşır; kuralların tam tanımı
`src/dilanaliz/rules/rules.md`'dedir. İmla (A) bölümündeki her madde **Tür A**
(TDK Yazım Kuralları sayfası, madde numaralı) veya **Tür B** (TDK Güncel
Türkçe Sözlük, madde numarasız) olarak etiketlidir — yeni imla maddesi
eklerken hangi türe girdiğini belirle, madde numarası UYDURMA.

- **İmla:** `IMLA-DE-DA`, `IMLA-KI`, `IMLA-MI`, `IMLA-BITISIK`, `IMLA-AYRI`,
  `IMLA-BAGLAMSAL-KARISTIRMA`, `IMLA-YALNIZ`, `IMLA-YANLIS`, `IMLA-HERKES`,
  `IMLA-HERSEY`, `IMLA-YABANCI`, `IMLA-SAAT`, `IMLA-KESME`, `IMLA-KISALTMA`,
  `IMLA-SIRA-SAYI`, `IMLA-DUZELTME-ISARETI`, `IMLA-TURKCE-KARAKTER`,
  `IMLA-NOKTALAMA`, `IMLA-BIRIM` (+ deterministik `HUNSPELL`).
- **Dil bilgisi:** `GRAMER-OZNE-YUKLEM`, `GRAMER-TAMLAMA`, `GRAMER-ANLATIM`
  (özne-araç mantık tersliği dâhil), `GRAMER-CATI`, `GRAMER-EK-FIIL`,
  `GRAMER-SAYI-UYUM`, `GRAMER-TEKRAR`, `GRAMER-BOLUNMUS-KELIME`,
  `GRAMER-BILDIRME-EKI`.
- **Ton:** `TON-RESMI`, `TON-NEZAKET`, `TON-HITAP-TUTARLILIK`, `TON-ACIKLIK`,
  `TON-KLISE`.
- **Tutarlılık:** belge-geneli terim/birim/kısaltma çakışması (`tutarlilik`).
