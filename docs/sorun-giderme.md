# Sorun Giderme

Hata alınca buraya bak — her seferinde önden çalıştırma.

- **Beklenmedik "eksik/bayat sonuç":** önce `rm -rf .cache/` ve tekrar dene
  (bkz. [bilinen-sinirlar.md](bilinen-sinirlar.md) → bayat önbellek).
- **Sözlük/`HunspellChecker` hatası veya imla bulgusu hiç çıkmıyor:**
  `dicts/tr_TR.dic` var mı? Yoksa Hunspell katmanı sessizce kapanır.
- **`GEMINI_API_KEY` / kimlik hatası:** `.env` dolu mu, `.venv` aktif mi?
- **Bağlantı donuyor/timeout (kurumsal ağ):** `GOOGLE_GENAI_TRANSPORT=rest` dene.
- **"Model kullanımdan kaldırılmış" / 404 "no longer available":** `.env`'deki
  `MODEL_ID` şu an erişilemiyor. Bu KESİN kapanış olmayabilir — 2026-07-09'da
  `gemini-2.5-flash` birkaç saatliğine bu hatayı verdi, ertesi gün kendi
  kendine düzeldi (ilan edilen resmi kapanışı 16 Ekim 2026); dokümandaki/
  Google'ın kendi listesindeki tarih GERÇEK durumu yansıtmayabilir, canlı hata
  mesajı esas alınır. Yine de projede varsayılan `gemini-3.5-flash`'tır ve
  "lite" sınıfı KULLANILMAZ (kalıcı karar — 96 örneklik altın sette ölçülü
  kalite kaybı var, bkz. README §11 model kıyası).
- **Ev Mac'inde web paneli bayat kod sunuyor:** eski bir `server.py` süreci
  arka planda kalmış olabilir; süreci öldür veya taze portta başlat.
