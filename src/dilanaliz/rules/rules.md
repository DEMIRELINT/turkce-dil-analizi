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
  Tırnak içine alınan bir ifadeye ek geldiğinde (tırnak TEK ' ya da ÇİFT "
  fark etmez), kesme işareti EKLENMEZ — ek doğrudan kapanış tırnağına
  bitişik yazılır. Tırnağın kendisi zaten bir sınırlayıcı görevi gördüğünden
  ayrıca kesmeye gerek yoktur (TDK: tırnak içine alınan sözlerden sonra
  gelen ekleri ayırmak için kesme işareti kullanılmaz — ör. eser adlarında
  "Sinekli Bakkal"ı, "Bit Palas"ını). Doğru: "Tarama Modu"nu, 'Tarama
  Modu'nu, "Bakım Modu"na. **Yanlış: "Tarama Modu"'nu, 'Tarama Modu''nu
  (kapanış tırnağının yanına GEREKSİZ bir kesme/tırnak daha eklenmiş —
  böyle yan yana iki kesme/tırnak İŞARETİ ASLA ÜRETME, bu bozuk bir
  öneridir).**

### A6. Düzeltme işareti ve Türkçe karakter

- **IMLA-DUZELTME-ISARETI** — Anlam ayırt eden yerlerde düzeltme/inceltme işareti
  kullanılır: "kâr" (kazanç) ≠ "kar" (yağış); "hâlâ" (henüz/şimdiye dek) ≠ "hala"
  (teyze); "âdet" (gelenek) ≠ "adet" (sayı). Bağlamdan kastedilen anlam NETSE eksik
  düzeltme işaretini öner. Örn. "Telsiz hala açıksa" → "Telsiz **hâlâ** açıksa"
  (henüz anlamı). NOT: Anlam belirsizse bulgu üretme (yanlış-pozitif riski).
- **IMLA-TURKCE-KARAKTER** — Türkçe karakter eksikliği bir imla hatasıdır
  (i/ı, ş/s, ç/c, ğ/g, ö/o, ü/u). Doğru: "geleceğim", "yarın". Yanlış: "gelecegim",
  "yarin".

### A7. Noktalama

- **IMLA-NOKTALAMA** — Cümle uygun noktalama ile biter. Bağlaç "ve"den önce
  genellikle virgül konmaz. Sıralı öğeler virgülle ayrılır. Doğru: "elma, armut
  ve üzüm". Yanlış: "elma, armut, ve üzüm".

### A8. Sayı ve ölçü birimi yazımı

- **IMLA-BIRIM** — Ondalık ayracı VİRGÜLDÜR ("12,5"; "12.5" yanlıştır). Ölçü birimi
  simgeleri doğru büyük/küçük harfle yazılır: "kHz" (Khz/KHz değil), "MHz"
  (Mhz/mhz değil), "GHz", "W", "kW", "kg", "mm". Sayı ile birim simgesi arasında
  bir boşluk bulunur ("5 W", "12,5 kHz"). Doğru: "12,5 kHz", "136-174 MHz",
  "5 W". Yanlış: "12.5 KHz", "136-174 Mhz", "5W".

---

## B. DİL BİLGİSİ

- **GRAMER-OZNE-YUKLEM** — Özne-yüklem uyumu (kişi/sayı). Cansız veya topluluk
  çoğul öznede yüklem TEKİL olur. Doğru: "Masalar geldi", "Öğrenciler geldi".
  Yanlış: "Masalar geldiler".
- **GRAMER-TAMLAMA** — İsim tamlamasında ekler tutarlı olmalı ("okulun bahçesi",
  "kapı kolu"). Ek eksikliği/fazlalığı hatadır. Belirtisiz isim tamlamasında
  tamlanan (ikinci sözcük) "-ı/-i/-u/-ü" iyelik ekini DÜŞÜRMEZ: Doğru "pil
  bölmesi kapağı", "cihaz menüsü", "ayar düğmesi". Yanlış "pil bölme kapağı"
  (→ "pil bölmesi kapağı"), "cihaz menü".
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
- **GRAMER-TEKRAR** — Ardışık, birebir aynı kelimenin tekrarı çoğunlukla belge
  çıkarma/kopyalama sırasında oluşan bir kusurdur (örn. "Rx Rx değerine göre",
  "işlem şekilde şekilde tamamlanır"); bu durumda tekrarı TEK kelimeye indiren
  bir `dil_bilgisi` bulgusu üret. ANCAK Türkçede zarf ikilemesi MEŞRU bir
  yapıdır ("yavaş yavaş", "adım adım", "azar azar", "teker teker", "tek tek",
  "ikişer ikişer" gibi) — cümle anlamlı bir vurgu/derece ikilemesiyse bulgu
  ÜRETME. Karar, kelimenin kendisine değil CÜMLE BAĞLAMINA (anlamlı bir
  ikileme mi, yoksa anlamsız/kopuk bir tekrar mı) dayanmalıdır. Ancak "yanıp
  yanıp sönmeye" gibi bir kullanım MEŞRU ikileme DEĞİLDİR — burada tek fiil
  "yanıp sönmek" sabit bir deyim/eylemdir, kelimenin ikinci kez tekrarı
  anlamsızdır (doğrusu: "yanıp sönmeye"). Karar kriteri: tekrarlanan kelime
  BAĞIMSIZ bir zarf/sıfat mı (ikileme, meşru) yoksa sabit bir deyim/fiilin
  PARÇASI mı (tekrar hatalı)?
- **GRAMER-BOLUNMUS-KELIME** — Yan yana duran iki kısa kelime, TEK BAŞLARINA
  geçerli olsalar bile, cümle bağlamında anlamsız durabilir ve birleştirilince
  anlamlı TEK bir kelime oluşturabilir (örn. "kapı dayım" → aslında
  "kapıdayım"; "baş vuru formu" → aslında "başvuru formu"). Sözlük bu durumu
  ayırt edemez (her iki parça da tek başına geçerlidir); yalnız cümlenin
  anlamına bakarak karar ver. Böyle bir durum tespit edilirse `dil_bilgisi`
  bulgusu üret, `suggestion` alanına birleşik doğru biçimi yaz. Yan yana duran
  iki kelime cümlede GERÇEKTEN ayrı ayrı anlamlıysa (örn. "Ali kapıda
  bekliyordu") bulgu ÜRETME.

---

## C. TON / ÜSLUP (Kurumsal yazışma)

> Ton ÖZNEL bir eksendir; yalnız kurumsal uygunluğu NET biçimde bozan durumlarda
> bulgu üret.

- **TON-RESMI** — Resmî/kurumsal yazışmada argo, günlük kısaltma ("slm", "tşk",
  "bi", "naber") ve aşırı samimi ifade uygun değildir. Doğru: "Selam" yerine
  "Sayın ...", "tşk" yerine "Teşekkür ederim".
- **TON-NEZAKET** — Bu kural YALNIZ gerçek kişiler-arası YAZIŞMADA (e-posta,
  resmi yazı, iç yazışma — kişisel hitap taşıyan: "Sayın ...", "bana",
  "sizden rica ederim" gibi işaretler içeren metin) işler: kişiye yöneltilen
  emir kipi yerine nazik rica dili tercih edilir. Doğru: "Gönderebilir
  misiniz / rica ederiz". Uygunsuz: "Hemen gönderin".
  **İSTİSNA (kapsamlı):** Kullanım kılavuzu, teknik talimat, prosedür/adım
  adım işlem tarifi gibi metinlerde emir kipi — CİHAZ/İŞLEM adımı olsun
  ("düğmeye basın", "kabloyu takın") İDARİ/kurumsal adım olsun ("servis
  formunu doldurup gönderin", "garanti belgesini saklayın") FARK ETMEZ —
  STANDART ve DOĞRU bir anlatım biçimidir, bulgu ÜRETME. Gerçek Türkçe
  kılavuzlarda idari/kurumsal adımlar da AYNI doğrudan emir kipiyle yazılır;
  "nazik rica dili" yalnız kişiler-arası yazışmaya özgü bir konvansiyondur,
  kılavuzun HİÇBİR bölümüne uygulanmaz. Ayırt edici soru artık "kime
  yöneltilmiş" DEĞİL, "bu metin NE TÜR bir metin": bir KILAVUZ/TALİMAT/
  PROSEDÜR mü (baştan sona emir kipi doğaldır, hiç işaretleme) yoksa gerçek
  bir kişiler-arası YAZIŞMA mı (kişisel hitap/imza içerir, o zaman kural
  işler)? Kural gerçekten uygulanacaksa (yazışmada kişiye yöneltilmiş emir),
  TEK bir hedef kalıp kullan: "...-ebilir misiniz?" ya da "...rica ederiz" —
  aynı fiil için farklı öneri biçimleri (örn. "basınız", "basmanız
  gerekmektedir", "basabilirsiniz" gibi birbirinden farklı biçimler)
  ÜRETME; tutarsızlık yaratır.
- **TON-HITAP-TUTARLILIK** — Aynı metinde sen/siz hitabı ve resmiyet düzeyi
  tutarlı olmalı; karışık hitap üslup bozukluğudur.
- **TON-ACIKLIK** — Belirsiz, muğlak veya gereğinden uzun dolambaçlı anlatım
  yerine açık ve doğrudan ifade tercih edilir.
- **TON-KLISE** — Aşırı/gereksiz klişe ve doldurma ifadelerden ("malumunuz olduğu
  üzere işbu vesileyle...") kaçınılması; sadelik tercih edilir.

---

## Bilinen Sınırlar

Bu bölüm bilinçli olarak ÇÖZÜLMEYEN, ölçülmüş boşlukları belgeler — kural
genişletmesi burada YAPILMAZ (bkz. `eval/golden.jsonl`'deki ilgili FN örneği).

- **Sözlük-geçerli ama bağlamda yanlış teknik terim** — Hunspell'in ek-tabanlı
  morfolojik analizi, anlamca yanlış olsa da GEÇERLİ bir sözcük kuruluşuna
  sahip yazım hatalarını yakalayamaz (örn. "güncelleme" yerine yanlışlıkla
  yazılan "günceleme" — "günce"+"-le"+"-me" olarak morfolojik açıdan geçerli
  sayılır). Bunu yakalamak için prompt'u "sözlükte geçerli ama bağlamda şüpheli
  kelimeleri de sorgula" yönünde genişletmek yanlış-pozitif riskini
  (geçerli teknik terimleri gereksiz sorgulama) belirsiz biçimde artırabilir;
  bu yüzden şimdilik genişletilmiyor.
