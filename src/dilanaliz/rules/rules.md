# Türkçe Dil Kuralları (TDK Temelli — Geliştirme Sürümü)

Bu dosya analiz motorundan **bağımsızdır**. Kurallar değişince kod değişmez;
yalnız bu dosya güncellenir. İleride bu içerik kurumun resmî TDK/üslup kılavuzuyla
**doğrudan değiştirilebilir** (aynı yapıyı koru). Çok büyürse RAG'e geçilir.

> Her kuralın bir kimliği vardır (örn. `IMLA-DE-DA`). Bir bulgu üretirken mümkünse
> ilgili kimliği `rule_id` alanına yaz. Aşağıda açıkça tanımlı OLMAYAN bir konuda
> hata uydurma; emin değilsen bulgu üretme. Bir bulgu için önerin (`suggestion`)
> mutlaka alıntıdan FARKLI olmalı.

---

## A. İMLA (Yazım)

### A1. Bağlaç / ek ayrımı (bağlama duyarlı — dikkat)

- **IMLA-DE-DA** — Bağlaç olan "de/da" ayrı yazılır ("Ben **de** geldim", "Kitap
  **da** güzeldi"); "ve, dahi, bile" anlamı taşır, cümleden çıkarılınca anlam
  bozulmaz ama eksilir. Bulunma/hâl eki "-de/-da/-te/-ta" bitişik yazılır
  ("ev**de**", "okul**da**", "sınıf**ta**"). Sert ünsüzle biten kelimeden sonra
  bağlaç yine ayrı ve "de/da" kalır ("kitap **da**", "çiçek **de**").
  Doğru: "Ben de geldim", "Evde kaldım". Yanlış: "Bende geldim", "ev de kaldım".
- **IMLA-KI** — Bağlaç "ki" ayrı yazılır ("Duydum **ki** gelmişsin"). Aitlik/ilgi
  eki "-ki" bitişik yazılır ("akşam**ki**", "yarın**ki**", "benim**ki**",
  "masadaki"). Kalıplaşmışlar bitişik istisnadır: "oysaki, mademki, halbuki,
  sanki, çünkü, meğerki, belki, illaki".
  Doğru: "Bilmiyordum ki", "yarınki toplantı", "benimkinden".
  Yanlış: "Bilmiyordumki", "yarın ki", **"Senin ki" → doğrusu "Seninki"** (aitlik
  eki bitişik yazılmalı). NOT: Aitlik eki "-ki" yanlışlıkla AYRI yazılmışsa bu bir
  hatadır; mutlaka işaretle.
- **IMLA-MI** — Soru eki "mı/mi/mu/mü" her zaman ayrı yazılır, ünlü uyumuna uyar
  ve kendinden sonraki eki bitişik alır ("Geldi **mi**?", "Güzel **mi**?",
  "Çalışıyor **musun**?"). Doğru: "Gelecek misin?". Yanlış: "Gelecekmisin?".

### A2. Birleşik / ayrı yazılan sözcükler

- **IMLA-BITISIK** — Bitişik yazılır: "hiçbir", "herhangi", "birçok", "birkaç",
  "biraz", "çünkü", "hiçkimse" DEĞİL → "hiç kimse" (ayrı). Doğru: "birkaç kişi".
  Yanlış: "bir kaç kişi", "her hangi".
- **IMLA-AYRI** — Ayrı yazılır: "her şey", "hiç kimse", "pek çok", "ya da",
  "bir şey", "bir an". Doğru: "her şey hazır", "ya da". Yanlış: "herşey", "yada".

### A3. Sık karışan / yanlış yazılan sözcükler

- **IMLA-YALNIZ** — Doğrusu "yalnız"; "yanlız" yanlıştır.
- **IMLA-YANLIS** — Doğrusu "yanlış"; "yannış", "yalnış" yanlıştır.
- **IMLA-HERKES** — Doğrusu "herkes"; "herkez" yanlıştır.
- **IMLA-HERSEY** — "her şey" AYRI yazılır; "herşey" yanlıştır. Sık yapılan hata,
  mutlaka işaretle. Doğru: "her şey hazır". Yanlış: "herşey hazır".
- **IMLA-YABANCI** — Sık yanlış yazılan alıntı sözcükler: "şoför" (şöför değil),
  "orijinal" (orjinal değil), "egzoz" (egzos değil), "espri" (espiri değil),
  "kontrol" (kontrol/kontörl karışıklığı), "makine" (makina tartışmalı, TDK
  "makine"), "sürpriz" (süpriz değil), "yanlış"/"laboratuvar" (laboratuar değil).
- **IMLA-SAAT** — "saat" → "saatler" (saatlar değil); ünlü uyumu istisnası.

### A4. Kesme işareti

- **IMLA-KESME** — Özel adlara gelen ÇEKİM ekleri kesme ile ayrılır ("Ankara'da",
  "Ahmet'in", "Türkiye'ye"). YAPIM ekleri ayrılmaz ("Türkçe", "Avrupalı").
  Kurum/kuruluş adlarına gelen ekler kesme ile ayrılmaz ("Türk Dil Kurumuna").
  Doğru: "İstanbul'da". Yanlış: "İstanbulda", "Türkçe'yi" (yapım eki → ayrılmaz).

### A6. Düzeltme işareti ve Türkçe karakter

- **IMLA-DUZELTME-ISARETI** — Anlam ayırt eden yerlerde düzeltme/inceltme işareti
  kullanılır: "kâr" (kazanç) ≠ "kar" (yağış); "hâlâ" (henüz) ≠ "hala" (teyze);
  "âdet" (gelenek) ≠ "adet" (sayı).
- **IMLA-TURKCE-KARAKTER** — Türkçe karakter eksikliği bir imla hatasıdır
  (i/ı, ş/s, ç/c, ğ/g, ö/o, ü/u). Doğru: "geleceğim", "yarın". Yanlış: "gelecegim",
  "yarin".

### A7. Noktalama

- **IMLA-NOKTALAMA** — Cümle uygun noktalama ile biter. Bağlaç "ve"den önce
  genellikle virgül konmaz. Sıralı öğeler virgülle ayrılır. Doğru: "elma, armut
  ve üzüm". Yanlış: "elma, armut, ve üzüm".

---

## B. DİL BİLGİSİ

- **GRAMER-OZNE-YUKLEM** — Özne-yüklem uyumu (kişi/sayı). Cansız veya topluluk
  çoğul öznede yüklem TEKİL olur. Doğru: "Masalar geldi", "Öğrenciler geldi".
  Yanlış: "Masalar geldiler".
- **GRAMER-TAMLAMA** — İsim tamlamasında ekler tutarlı olmalı ("okulun bahçesi",
  "kapı kolu"). Ek eksikliği/fazlalığı hatadır.
- **GRAMER-ANLATIM** — Anlatım bozuklukları (en yüksek yanlış-pozitif riski; yalnız
  AÇIK durumlarda işaretle):
  - Gereksiz sözcük / anlamca çelişki: "yaklaşık olarak tam on kişi" (yaklaşık +
    tam çelişir), "geri iade etmek", "en optimal".
  - Eksik öge (özne/nesne/tümleç eksikliği), yanlış bağlama.
  - Mantık hatası, sıralama bozukluğu.
- **GRAMER-CATI** — Çatı (etken/edilgen) uyumsuzluğu. Doğru: "Sorun çözüldü" veya
  "Sorunu çözdüler". Karışık edilgen kullanımı hatadır.
- **GRAMER-EK-FIIL** — Kip ve zaman tutarlılığı; ek-fiil ("idi/imiş/ise") doğru
  kullanımı. Aynı cümlede gereksiz zaman kayması hatadır.

---

## C. TON / ÜSLUP (Kurumsal yazışma)

> Ton ÖZNEL bir eksendir; yalnız kurumsal uygunluğu NET biçimde bozan durumlarda
> bulgu üret.

- **TON-RESMI** — Resmî/kurumsal yazışmada argo, günlük kısaltma ("slm", "tşk",
  "bi", "naber") ve aşırı samimi ifade uygun değildir. Doğru: "Selam" yerine
  "Sayın ...", "tşk" yerine "Teşekkür ederim".
- **TON-NEZAKET** — Emir kipi yerine nazik rica dili. Doğru: "Gönderebilir
  misiniz / rica ederiz". Uygunsuz: "Hemen gönderin".
- **TON-HITAP-TUTARLILIK** — Aynı metinde sen/siz hitabı ve resmiyet düzeyi
  tutarlı olmalı; karışık hitap üslup bozukluğudur.
- **TON-ACIKLIK** — Belirsiz, muğlak veya gereğinden uzun dolambaçlı anlatım
  yerine açık ve doğrudan ifade tercih edilir.
- **TON-KLISE** — Aşırı/gereksiz klişe ve doldurma ifadelerden ("malumunuz olduğu
  üzere işbu vesileyle...") kaçınılması; sadelik tercih edilir.
