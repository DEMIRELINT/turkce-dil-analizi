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
bilgisi** ve **ton** eksenlerinde inceleyip her sorun için *gerekçe + düzeltme
önerisi* üreten hibrit bir sistem. Sistem **önerir, düzeltmez**; son söz
kullanıcıdadır.

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
cli.py                      # Elle deneme girişi (CLI; metin veya .docx)
pyproject.toml              # Bağımlılıklar (pinli, air-gap uyumlu)
src/dilanaliz/
  analyzer.py               # Ana orkestrasyon (kademeli geçişler, build_default_analyzer)
  spell.py                  # Hunspell tabanlı deterministik imla tespiti
  extract.py                # .docx → eksiksiz metin (docx2python; tablo/dipnot dahil)
  chunk.py                  # Uzun metni deterministik paragraf parçalarına böler (taşan paragraf cümleye iner)
  progress.py               # Geçiş ilerleme olayları (CLI stderr / web SSE)
  prompt.py                 # LLM davranışı (geçiş başına system prompt; kurallar ayrı)
  providers/                # LLM sağlayıcı soyutlaması (Gemini → vLLM değişebilir)
  rules/                    # RulesProvider + rules.md (kurallar koddan ayrı)
  schema.py                 # Pydantic v2 bulgu/çıktı şemaları (imla/dil_bilgisi/ton/tutarlilik)
  locate.py                 # Alıntıyı kaynakta konumlama (offset)
  postprocess.py            # Birleştirme + tekilleştirme + öneri doğrulama
  cache.py                  # Disk önbelleği (.cache/llm_cache.json)
  config.py                 # Ortam değişkenleri / yapılandırma
web/                        # Yerel web paneli (stdlib http.server + SSE; docx yükle)
tests/                      # pytest birim testleri (API gerektirmez)
eval/                       # Altın set + precision/recall ölçüm betiği
```

---

## Sık Kullanılan Komutlar

```bash
# Kurulum
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env        # GEMINI_API_KEY girin

# Çalıştırma
python cli.py "Bu cümlede ki hata var ve yanlız yazılmış."
echo "uzun metin..." | python cli.py
python cli.py belge.docx > sonuc.json     # .docx → çıkar + parçala + analiz

# Web paneli (docx yükle / metin yapıştır + canlı ilerleme)
python web/server.py                       # http://127.0.0.1:8765

# Test (API gerektirmez)
pytest

# Ölçüm (altın set — API gerektirir)
EVAL_DELAY_SEC=0 python eval/run_eval.py

# Sıralı vs paralel karşılaştırma (hız + eşdeğerlik; API gerektirir)
python eval/compare_parallel.py belge.docx   # küçük belgeyle: belgeyi 3× analiz eder
```

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
- **Air-gap uyumu** — bağımlılıklar pinli; telemetri kapalı; gizli dış çağrı
  ekleme. `docx2python` ve web paneli (stdlib) dahil her şey yereldir.

---

## Çalışma Kuralları

- **Türkçe yaz.** Kod yorumları, commit mesajları ve dokümantasyon Türkçe
  olmalı (mevcut tarz korunsun).
- **Ölçerek karar ver.** Prompt/kural değişiklikleri altın set (`eval/`)
  üzerinde precision/recall ile değerlendirilir; sezgiyle değil.
- **Yanlış-pozitif kritiktir.** Kurumsal denetçide temiz metinde hata uydurmak
  en büyük kusurdur; bunu artıran değişikliklerden kaçın.
- **Bağımlılık eklerken** pinli aralık kullan ve air-gap uyumunu gözet.
- **Push hedefi:** Değişiklikler ilgili çalışma dalına yapılır; doğrudan `main`'e
  izinsiz push yapılmaz.
- **Büyük güncellemelerde** yukarıdaki "Büyük Güncellemeleri Raporla" kuralını
  uygula.
