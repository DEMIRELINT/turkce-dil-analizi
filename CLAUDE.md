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

Detaylı anlatım için [README.md](README.md) dosyasına bakın.

---

## Dizin Yapısı

```
cli.py                      # Elle deneme girişi (CLI)
pyproject.toml              # Bağımlılıklar (pinli, air-gap uyumlu)
src/dilanaliz/
  analyzer.py               # Ana orkestrasyon (build_default_analyzer)
  spell.py                  # Hunspell tabanlı deterministik imla tespiti
  prompt.py                 # LLM davranışı (yalnız davranış, kurallar ayrı)
  providers/                # LLM sağlayıcı soyutlaması (Gemini → vLLM değişebilir)
  rules/                    # RulesProvider + rules.md (kurallar koddan ayrı)
  schema.py                 # Pydantic v2 bulgu/çıktı şemaları
  locate.py                 # Alıntıyı kaynakta konumlama (offset)
  postprocess.py            # Birleştirme + tekilleştirme
  cache.py                  # Disk önbelleği (.cache/llm_cache.json)
  config.py                 # Ortam değişkenleri / yapılandırma
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

# Test (API gerektirmez)
pytest

# Ölçüm (altın set — API gerektirir)
EVAL_DELAY_SEC=0 python eval/run_eval.py
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
- **Air-gap uyumu** — bağımlılıklar pinli; telemetri kapalı; gizli dış çağrı
  ekleme.

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
