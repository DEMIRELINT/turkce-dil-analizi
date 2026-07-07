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

> **Kaynak türü notu:** Bu bölümdeki maddeler iki farklı resmî TDK kaynağına
> dayanır. **Tür A** — TDK Yazım Kuralları sayfası (madde numarasıyla
> anılabilir, örn. "TDK Virgül md. 1"). **Tür B** — TDK Güncel Türkçe
> Sözlük (kelimenin doğru yazımı sözlükte bu biçimde geçer; bir "yazım
> KURALI" maddesi değildir, madde numarası UYDURULMAZ). Her iki tür de
> RESMÎ TDK kaynağıdır; yalnız atıf biçimi farklıdır.

### A1. Bağlaç / ek ayrımı (bağlama duyarlı — dikkat)

- **IMLA-DE-DA** *(Tür A — TDK Bağlaç Olan da/de'nin Yazılışı; TDK Bulunma
  Durumu Eki -da/-de/-ta/-te'nin Yazılışı)* — Bağlaç olan "de/da" ayrı
  yazılır ("Ben **de** geldim", "Kitap **da** güzeldi"); "ve, dahi, bile"
  anlamı taşır, cümleden çıkarılınca anlam bozulmaz ama eksilir. Bulunma/hâl
  eki "-de/-da/-te/-ta" bitişik yazılır ("ev**de**", "okul**da**",
  "sınıf**ta**"). Sert ünsüzle biten kelimeden sonra bağlaç yine ayrı ve
  "de/da" kalır, ASLA "ta/te" olmaz (TDK'nın kendi UYARI'sı: "gidip **de**
  gelmemek" — "gidip **te** gelmemek" DEĞİL): "kitap **da**", "çiçek **de**".
  Doğru: "Ben de geldim", "Evde kaldım". Yanlış: "Bende geldim", "ev de kaldım".
  **Bağlaç "da/de" kesme işaretiyle de ASLA ayrılmaz** (TDK'nın kendi UYARI'sı):
  Doğru: "Ayşe de geldi". Yanlış: "Ayşe'de geldi" (bağlaç anlamındaysa).
- **IMLA-KI** *(Tür A — TDK Bağlaç Olan ki'nin Yazılışı)* — Bağlaç "ki" ayrı
  yazılır ("Duydum **ki** gelmişsin"). Aitlik/ilgi eki "-ki" bitişik yazılır
  ("akşam**ki**", "yarın**ki**", "benim**ki**", "masadaki"). Kalıplaşmışlar
  bitişik istisnadır (TDK'nın kendi listesi, tam 7 kelime): "belki, çünkü,
  hâlbuki, mademki, meğerki, oysaki, sanki".
  Doğru: "Bilmiyordum ki", "yarınki toplantı", "benimkinden".
  Yanlış: "Bilmiyordumki", "yarın ki", **"Senin ki" → doğrusu "Seninki"** (aitlik
  eki bitişik yazılmalı). NOT: Aitlik eki "-ki" yanlışlıkla AYRI yazılmışsa bu bir
  hatadır; mutlaka işaretle. NOT: Kalıplaşmışlar listesi KAPALI ve TDK'nın
  kendi listesiyle SINIRLIDIR — listede olmayan bir kelimeyi ("illaki" gibi)
  bu 7'liye benzeterek bitişik "doğru" sayma.
- **IMLA-MI** *(Tür A — TDK Soru Eki mı/mi/mu/mü'nün Yazılışı)* — Soru eki
  "mı/mi/mu/mü" her zaman ayrı yazılır, ünlü uyumuna uyar ve kendinden
  sonraki eki bitişik alır ("Geldi **mi**?", "Güzel **mi**?", "Çalışıyor
  **musun**?"). Doğru: "Gelecek misin?". Yanlış: "Gelecekmisin?".

### A2. Birleşik / ayrı yazılan sözcükler

- **IMLA-BITISIK** *(Tür A — TDK Bitişik Yazılan Birleşik Kelimeler md. 1, 2, 3)*
  — Bitişik yazılır: "hiçbir", "herhangi", "birçok", "birkaç", "biraz",
  "çünkü", "hiçkimse" DEĞİL → "hiç kimse" (ayrı). Doğru: "birkaç kişi".
  Yanlış: "bir kaç kişi", "her hangi".
  Ayrıca aşağıdaki üç TDK grubu da bitişik yazılır (ayrı yazılmışsa hata):
  - **Ses düşmesine uğrayan birleşik kelimeler** (TDK md. 1): kaynana, kaynata,
    nasıl, niçin, pazartesi, sütlaç. Doğru: "kaynanam geldi". Yanlış: "kayın
    anam geldi" (bu birleşik kelimeler için ayrı yazım kullanılmaz).
  - **"etmek/olmak" ile ses olayına (türeme/düşme/değişme) uğrayan
    bileşikler** (TDK md. 2): affetmek, bahsetmek, emretmek, hissetmek,
    kahrolmak, kaybolmak, reddetmek, sabretmek, seyretmek, zannetmek. Doğru:
    "teklifi reddettik". Yanlış: "teklifi red ettik", "olayı fark etti"
    DEĞİL → doğrusu zaten ayrı olan "fark etmek" bu listeye dahil değildir
    (yalnız yukarıdaki 10 kelime bu kuralın kapsamındadır — listede
    olmayan "etmek/olmak" bileşiği için bulgu üretme).
  - **Sıfat-fiil ekiyle (-an/-en, -r/-ar/-er/-ır/-ir, -maz/-mez) kurulan
    kalıplaşmış birleşik kelimeler** (TDK md. 3, TDK'nın kendi örnekleri):
    gökdelen, cankurtaran, dalgakıran, basınçölçer. Doğru: "gökdelen inşaatı".
    Yanlış: "gök delen inşaatı".
- **IMLA-AYRI** — İki farklı kaynaklı alt-grup:
  - *(Tür A — TDK Ayrı Yazılan Birleşik Kelimeler, sıfat-fiil ekiyle kurulan
    sıfat tamlaması maddesi, TDK'nın kendi örnekleri)*: "döner sermaye",
    "yeter sayı", "tükenmez kalem" gibi kalıplar ayrı yazılır. Doğru:
    "döner sermaye işletmesi". Yanlış: "dönersermaye işletmesi".
  - *(Tür B — TDK Güncel Türkçe Sözlük; bu kelimeler TDK'nın "Ayrı Yazılan
    Birleşik Kelimeler" yazım-kuralı sayfasında YOKTUR, sözlükte iki ayrı
    sözcük olarak geçtikleri için ayrı yazılır)*: "her şey", "hiç kimse",
    "pek çok", "ya da", "bir şey", "bir an". Doğru: "her şey hazır", "ya da".
    Yanlış: "herşey", "yada".

### A3. Sık karışan / yanlış yazılan sözcükler

> Bu bölümdeki maddelerin tamamı **Tür B**'dir (TDK Güncel Türkçe Sözlük —
> kelimenin sözlükte hangi biçimde geçtiği bilgisi); TDK'nın Yazım Kuralları
> sitesinde bunlara karşılık gelen madde numaralı bir sayfa yoktur.

- **IMLA-BAGLAMSAL-KARISTIRMA** *(Tür B)* — Bağlamsal karıştırılabilir kelime
  çifti (SÖZLÜKTE HER İKİSİ DE geçerli, ama biri cümlede yanlış anlamda
  kullanılmış olabilir — normal tek-kelime yazım taraması bunu YAKALAYAMAZ,
  bu yüzden kapalı bir liste olarak burada AÇIKÇA tanımlanır):
  - "güncelleme" (bir şeyi güncel hâle getirme) ≠ "günceleme" (günlük tutma
    anlamında nadir/eskil bir kelime). Kurumsal/teknik metinde "günceleme
    dosyası", "yazılımı günceleme" gibi bir kullanım GENELDE "güncelleme"
    yanlış yazılmış hâlidir — bağlamdan (yazılım/teknik) NETSE düzelt.
  - "yarin" (nadir, "yâr"in tamlanan hâli — şiirsel) ≠ "yarın" (ertesi gün).
    Kurumsal/teknik metinde zaman belirten bir yerde "yarin" GENELDE "yarın"
    yanlış yazılmış hâlidir (eksik Türkçe karakter: ı→ harfsiz). Bağlam
    zaman belirtiyorsa düzelt.
  NOT: Bu liste KAPALI ve kısadır — yalnız yukarıdaki iki çift için geçerlidir,
  başka sözlük-geçerli kelimeleri bu gerekçeyle sorgulama (bkz. Bilinen
  Sınırlar → "Sözlük-geçerli ama bağlamda yanlış teknik terim").
- **IMLA-YALNIZ** *(Tür B)* — Doğrusu "yalnız"; "yanlız" yanlıştır.
- **IMLA-YANLIS** *(Tür B)* — Doğrusu "yanlış"; "yannış", "yalnış" yanlıştır.
- **IMLA-HERKES** *(Tür B)* — Doğrusu "herkes"; "herkez" yanlıştır.
- **IMLA-HERSEY** *(Tür B — "her şey"in ayrı yazımı IMLA-AYRI'daki Tür B
  grubuyla aynı gerekçeye dayanır)* — "her şey" AYRI yazılır; "herşey"
  yanlıştır. Sık yapılan hata, mutlaka işaretle. Doğru: "her şey hazır".
  Yanlış: "herşey hazır".
- **IMLA-YABANCI** *(Tür B)* — Sık yanlış yazılan alıntı sözcükler: "şoför"
  (şöför değil), "orijinal" (orjinal değil), "egzoz" (egzos değil), "espri"
  (espiri değil), "kontrol" (kontrol/kontörl karışıklığı), "makine" (makina
  tartışmalı, TDK "makine"), "sürpriz" (süpriz değil), "yanlış"/"laboratuvar"
  (laboratuar değil), "aksesuar" (aksesuvar değil), "antrenman" (antreman
  değil), "lisans" (lizans değil), "performans" (perfomans değil),
  "konfigürasyon" (konfigrasyon değil), "adaptör" (adaptor/adapter değil).
- **IMLA-SAAT** *(Tür A — TDK Büyük Ünlü Uyumu, "uyuma girmeyen kelimeler"
  listesi: "saat/saate" doğrudan TDK'nın kendi örneği)* — "saat" →
  "saatler" (saatlar değil); ünlü uyumu istisnası.

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
  **BULGU ÜRETME UYARISI:** "'Etiket'ne", "'Etiket'na", "'Etiket'ndan" gibi
  kapanış tırnağına DOĞRUDAN BİTİŞİK ek gördüğünde ("'Programlama Modu'na",
  "'Boşta' Programlama Modu'ndan") bu YUKARIDAKİ "Doğru" örneğinin ta
  kendisidir — buna ASLA hata deme, kesme EKLEMEYİ önerme, backtick veya
  başka bir işaretle "düzeltme" ÜRETME. Bu biçim zaten kuralın istediği
  DOĞRU biçimdir; dokunmadan geç.
  **Özel ad OLMAYANA kesme EKLETME** (TDK Kesme İşareti — kural yalnız özel
  adlara gelen ekler içindir): ürün/parça SINIFI adları ("kaynak telsiz",
  "standart pil", "yuvalı şarj aleti") özel ad değildir — büyük harfle
  yazılmış olsalar bile bunlara gelen eke kesme işareti EKLEMEYİ önerme
  ("Kaynak Telsizde" doğrudur; "Kaynak Telsiz'de" önerisi YANLIŞTIR). Kesme
  yalnız gerçek özel adlara (kişi, yer, kurum, marka: "Motorola'nın") ve
  tırnaklı/rakamlı biçimlere uygulanır.
  **Rakamla biten sayıya gelen ek, TDK Kesme İşareti'nin "Sayılara getirilen
  ekleri ayırmak için konur" maddesine göre sayının OKUNUŞUNA uyar** (TDK'nin
  kendi örneği: "1985'te, 8'inci madde, 2'nci kat"): "21'deki" (yirmi bir →
  -deki), "446'dan" (dört yüz kırk altı → -dan), "0'a" (sıfır → -a). Yanlış:
  "21'daki", "446'den".

### A5. Kısaltmalar ve sıra sayıları

- **IMLA-KISALTMA** — Kısaltmaya gelen ek, TDK Kısaltmalar sayfasındaki üç
  kurala göre belirlenir:
  1. **Küçük harfli kısaltma** → açılımın (kelimenin) okunuşu esas alınır:
     "cm'yi" (santimetreyi), "kg'dan" (kilogramdan).
  2. **Büyük harfli, HARF HARF okunan kısaltma** → kısaltmanın SON HARFİNİN
     okunuşu esas alınır (TDK'nin kendi örnekleri): "TBMM'nin", "TDK'nin",
     "BM'de", "ABD'de", "TV'ye", "THY'de", "TRT'den", "TL'nin", "BDT'ye".
     Sık yapılan hata: kısaltmanın son harfi ince okunuyorsa (K, T, S, L gibi
     çoğu ünsüz harfin adı incedir: "ke, te, se, le") ek de İNCE olmalı —
     "TDK'nın" YANLIŞTIR, doğrusu "TDK'nin"dir (TDK'nin kendi resmî örneği).
  3. **Büyük harfli ama KELİME GİBİ okunan kısaltma** (NATO, UNESCO, ASELSAN,
     BOTAŞ gibi) → kısaltmanın kelime-okunuşu esas alınır: "NATO'dan",
     "UNESCO'ya", "ASELSAN'da", "BOTAŞ'ın".
  Karar, kısaltmanın belgede/konuşmada harf harf mi yoksa tek kelime gibi mi
  okunduğuna bağlıdır — emin değilsen (kısaltmanın okunuş biçimi belgeden
  anlaşılmıyorsa) bulgu üretme. Aynı kısaltmanın belgede farklı ek
  biçimleriyle gezmesi (aynı kısaltma bir yerde 2. kuralla bir yerde 3.
  kuralla çekimlenmiş) tutarsızlıktır — baskın biçimi öner.
  **Noktalı kısaltmaya (bkz., örn., vb., Alm., İng.) gelen ek KESMESİZ
  yazılır** (TDK'nin kendi örneği): "vb.leri", "Alm.dan", "İng.yi". Yaygın
  noktalı kısaltmalar: "bkz.", "örn.", "vb.", "vs.".
- **IMLA-SIRA-SAYI** — Sıra sayısı rakamla gösterilirken YA rakamdan sonra
  nokta konur YA DA rakamdan sonra kesme işaretiyle derece eki yazılır —
  **ikisi birden ASLA kullanılmaz** (TDK Sayıların Yazılışı md. 9 UYARI:
  "Sıra sayıları ekle gösterildiklerinde rakamdan sonra sadece kesme işareti
  ve ek yazılır, ayrıca nokta konmaz"). Yanlış: "8.'inci", "2.'nci" → Doğru:
  "8'inci" (ya da yalnız "8."), "2'nci" (ya da yalnız "2."). NOT: Bu kural
  yalnız NET bozuk (nokta + kesme+ek birlikte) kalıplar içindir; "sıra
  sayısı nokta ile mi kesme+ek ile mi yazılmalı" tarzı stil tercihine
  karışma — TDK ikisine de izin verir, yalnız KARIŞTIRILMASINI yasaklar.

### A6. Düzeltme işareti ve Türkçe karakter

- **IMLA-DUZELTME-ISARETI** *(Tür A — TDK Düzeltme İşareti md. 1; "hâlâ/hala"
  ve "âdet/adet" TDK'nın kendi örnekleridir. "kâr/kar" TDK'nın örnek
  listesinde YOK ama AYNI ilkenin — yazılışı bir, anlamı ayrı kelimeleri
  ayırt etme — doğrudan bir genellemesidir)* — Anlam ayırt eden yerlerde
  düzeltme/inceltme işareti kullanılır: "kâr" (kazanç) ≠ "kar" (yağış);
  "hâlâ" (henüz/şimdiye dek) ≠ "hala" (teyze); "âdet" (gelenek) ≠ "adet"
  (sayı). Bağlamdan kastedilen anlam NETSE eksik düzeltme işaretini öner.
  Örn. "Telsiz hala açıksa" → "Telsiz **hâlâ** açıksa" (henüz anlamı). NOT:
  Anlam belirsizse bulgu üretme (yanlış-pozitif riski).
- **IMLA-TURKCE-KARAKTER** *(kaynak gerektirmez — temel Türk alfabesi
  gerçeği, TDK'nın kendi yazım kılavuzu/sözlüğü zaten Türkçe karakterle
  yazılıdır)* — Türkçe karakter eksikliği bir imla hatasıdır (i/ı, ş/s, ç/c,
  ğ/g, ö/o, ü/u). Doğru: "geleceğim", "yarın". Yanlış: "gelecegim", "yarin".

### A7. Noktalama

- **IMLA-NOKTALAMA** — Cümle uygun noktalama ile biter. Bağlaç "ve"den önce
  genellikle virgül konmaz. Sıralı öğeler virgülle ayrılır. Doğru: "elma, armut
  ve üzüm". Yanlış: "elma, armut, ve üzüm".
  (Kaynak: TDK Noktalama İşaretleri, Virgül md. 1 ve UYARI'lar —
  tdk.gov.tr/icerik/yazim-kurallari/noktalama-isaretleri-aciklamalar.)
  - **EKSİK virgül de hatadır** (TDK Virgül md. 1 — "birbiri ardınca sıralanan
    eş görevli kelime ve kelime gruplarının arasına konur"): çok ögeli bir
    sıralamada öğeler arasında virgül yoksa ekle. Yanlış: "aynı bant (UHF veya
    VHF) tür (Ekranlı veya Ekransız) ve bölgeden olmalıdır" → Doğru: "aynı
    bant (UHF veya VHF), tür (Ekranlı veya Ekransız) ve bölgeden olmalıdır".
  - **Zarf-fiil eki (-arak/-ıp/-ınca/-dıkça/-ken vb.) almış TEK bir kelimeden
    sonra virgül konmaz** (TDK Virgül md. 13 UYARI — bu kural YALNIZ zarf-fiil
    içindir, başka yapıları kapsamaz). Yanlış: "Kapıyı açarak, içeri girdi."
    → Doğru: "Kapıyı açarak içeri girdi." ANCAK art arda BİRDEN FAZLA
    zarf-fiil varsa aralarına virgül konur (TDK md. 13 asıl madde, TDK'nin
    kendi örneği): "Ancak yemekte bir karara varıp, arkadaşına dikkatli
    dikkatli bakarak konuştu." NOT (temkinli istisna — Sülükçü 2018'in
    TDK'ya önerdiği düzeltmeyle uyumlu): Virgülün kaldırılması cümlede anlam
    karışıklığı yaratacaksa (uzun/iç içe cümlede hangi öğenin neyi
    nitelediği belirsizleşiyorsa) virgülü kaldırmayı önerme.
  - **"İçin" edatı bu kuralın KAPSAMI DIŞINDADIR** — edat, zarf-fiil
    değildir; TDK'nin virgül kurallarında "için"e özgü bir madde YOKTUR.
    "X yapmak için," gibi yapılardaki virgüle dair bulgu ÜRETME (ne ekleme
    ne kaldırma) — kaynağı belirsiz bir alanda sessiz kalmak doğrusu. **BU
    İSTİSNA MUTLAKTIR:** "...için," kalıbını gördüğünde zarf-fiil kuralını
    (yukarıdaki madde) "için"e UYGULAMA — "için" bir zarf-fiil eki DEĞİL, bir
    EDATTIR; iki kural birbirine KARIŞTIRILAMAZ. Yanlış davranış örneği (ASLA
    yapma): "...öğrenmek için, bkz. ... sayfa 12." cümlesindeki virgülü
    "zarf-fiil kuralı" gerekçesiyle kaldırmayı önermek — bu cümlede zarf-fiil
    YOKTUR, "için" vardır; sessiz kal.
  - **LİSTE VİRGÜLÜNE DOKUNMA** (TDK Virgül md. 1): Cümle başındaki öğe bir
    listenin parçasıysa virgül ZORUNLUDUR; kaldırılması anlamı bozar. Örn.
    "CPS, Yuvalı Şarj Cihazı ve Programlama Kablosuna ihtiyacınız olacak."
    cümlesindeki ilk virgül üç öğeli listenin ayracıdır — kaldırılırsa "CPS
    Yuvalı Şarj Cihazı" diye tek bir aygıt varmış anlamı çıkar. Virgül
    kaldırma önerisi vermeden önce virgülün LİSTE ayracı olup olmadığını
    kontrol et.
  - **Noktalı virgülden sonra küçük harf DOĞRUDUR** (TDK: virgül ve noktalı
    virgülden sonra gelen kelime, normalde büyük yazılması gerekmiyorsa
    küçük yazılır): "...basılı tutun; dinlemek için ise serbest bırakın."
    kuruluşunda ne noktalı virgül ne de sonrasındaki küçük harf hatadır —
    ikisi için de bulgu üretme.
  - **Etiket sözcüğü + iki nokta (:) DOĞRUDUR — noktaya çevirme.** Bir notu,
    uyarıyı veya açıklamayı TANITAN etiket sözcüğünden sonra iki nokta üst üste
    kullanımı TDK'ya göre doğrudur (iki nokta, kendisinden sonra açıklama/örnek
    geleceğini bildirir). "Not:", "Notlar:", "Uyarı:", "Dikkat:", "Önemli:",
    "Örnek:", "İpucu:" gibi kullanımları "Not." biçiminde noktaya çevirmeyi
    ÖNERME — bu sahte-pozitiftir; iki nokta burada beklenen işarettir.
  - **Literal KARAKTER/SİMGE KÜMESİNE virgül ekleme.** Bir teknik metinde izin
    verilen karakterlerin/simgelerin literal dökümü (örn. kanal adı için
    kullanılabilen küme: "0 - 9 * {}? &%. + / - _ ' ' \") bir düzyazı
    SIRALAMASI DEĞİL, VERİDİR. Aralarına virgül ekleme önerme — "eş görevli
    öğeler virgülle ayrılır" kuralı bu literal karakter kümelerine uygulanmaz.
  - **Başlık/etiket satırına son noktalama EKLEME:** Nokta ile bitmeyen kısa
    başlık, düğme açıklaması veya şekil etiketi ("Kanal 1'i önceden ayarlamak
    için varsayılan ayar") cümle değildir; sonuna nokta eklemeyi önerme.
    **Bu madde yalnız EKLEME yönündedir — var olan bir noktayı SİLMEYİ
    önermek için kullanma.** Özellikle "bkz. "X" sayfa N." kalıbında sayfa
    numarasından sonra gelen nokta, cümlenin kendi bitiş noktalama işaretidir
    (cümle "Daha fazla bilgi için bkz. ... sayfa 7." ile biter) — bunu bir
    "etiket sonu fazlalık nokta" sanıp kaldırma. Bir noktanın kaldırılmasını
    önermeden önce o noktanın cümlenin GERÇEK bitişi olup olmadığını kontrol
    et; öyleyse dokunma.

### A8. Sayı ve ölçü birimi yazımı

- **IMLA-BIRIM** — Ondalık ayracı VİRGÜLDÜR ("12,5"; "12.5" yanlıştır). Ölçü birimi
  simgeleri doğru büyük/küçük harfle yazılır: "kHz" (Khz/KHz değil), "MHz"
  (Mhz/mhz değil), "GHz", "W", "kW", "kg", "mm". Sayı ile birim simgesi arasında
  bir boşluk bulunur ("5 W", "12,5 kHz"). Doğru: "12,5 kHz", "136-174 MHz",
  "5 W". Yanlış: "12.5 KHz", "136-174 Mhz", "5W".
  **İSTİSNA (tablo/çizelge verisi):** Salt sayıdan (± kısa birim simgesi) oluşan
  tablo/çizelge hücrelerindeki ondalık noktaları TEK TEK işaretleme — bir
  frekans çizelgesindeki onlarca hücre için ayrı ayrı bulgu üretmek raporu
  boğar. Bu durum sistem tarafından belge-geneli TEK özet bulgu olarak
  deterministik raporlanır; senin işin yalnız DÜZYAZI içindeki ondalık/birim
  hatalarıdır.

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
    tam çelişir), "geri iade etmek", "en optimal". "vb." zaten "ve benzeri"
    demektir; "vb. gibi" veya "vs. gibi" bu yüzden FAZLALIKTIR — doğrusu
    yalnız "vb." ya da yalnız "gibi"dir (örn. "pil türü, VOX seviyesi vs.
    gibi özellikler" → "...VOX seviyesi vb. özellikler").
  - Eksik öge (özne/nesne/tümleç eksikliği), yanlış bağlama.
  - Mantık hatası, sıralama bozukluğu.
  - Özne-araç mantık tersliği (yalnız FİZİKSEL/MANTIKSAL olarak olanaksız
    eşleşmede): cümlenin öznesi ile "-la/-le/-yla" ya da "tarafından" aracının
    rolleri ters kurulup talimatı çelişkili/uygulanamaz kıldığında. Yanlış:
    "Şarj cihazı, yalnızca üretici tarafından onaylanan orijinal aksesuarlarla
    kullanılmalıdır." (özne = şarj cihazı; oysa kastedilen, CİHAZIN onaylı şarj
    cihazıyla şarj edilmesidir) → Doğru: "Cihaz yalnızca onaylı orijinal şarj
    cihazıyla şarj edilmelidir." SINIR (yanlış-pozitif kapısı): Özne ile araç
    GERÇEKTEN tutarlı ve cümle uygulanabilir bir talimatsa ("Cihaz yalnızca
    onaylı aksesuarlarla kullanılmalıdır" — özne/araç uyumlu) ASLA işaretleme;
    yalnız rollerin ters kurulduğu, sonucun mantıken olanaksız olduğu AÇIK
    durumları işaretle.
- **GRAMER-CATI** — Çatı (etken/edilgen) uyumsuzluğu: bağlı cümlelerde çatı
  TUTARLI olmalı, ortasında sebepsiz değişmemeli. Doğru (ikisi de edilgen):
  "Rapor hazırlandı ve yönetime sunuldu." Doğru (ikisi de etken, özne belli):
  "Ekip raporu hazırladı ve yönetime sundu." Yanlış (edilgenden etkene
  sebepsiz geçiş — kimin sunduğu belirsizleşir): "Rapor hazırlandı ve
  yönetime sundular." (→ "...yönetime sunuldu." ya da baştan "Ekip raporu
  hazırladı ve sundu.") NOT: Yalnız gerçekten karışık/belirsiz özneli
  durumları işaretle; açık öznesi olan meşru etken cümleleri ("Ekip
  hazırladı ve sundu") çatı hatası SAYMA.
  **İkinci kalıp — belirtme ekli nesne + edilgen yüklem:** Edilgen yüklem
  ("-nabilir", "-ndı", "-nmıştır") belirtme ekli ("-i/-ı/-u/-ü") nesneyle
  kullanılamaz; ya nesne yalın hâle döner ya yüklem etkene. Yanlış:
  "Telsizleri CPS kullanarak programlanabilir." → Doğru: "Telsizler CPS
  kullanılarak programlanabilir." (ya da "Telsizleri CPS kullanarak
  programlayabilirsiniz."). Bu kalıp çeviri metinlerde sık görülür; cümlede
  "-i ekli nesne + edilgen çekim" birlikteyse işaretle.
- **GRAMER-EK-FIIL** — Kip ve zaman tutarlılığı; ek-fiil ("idi/imiş/ise") doğru
  kullanımı. Aynı cümlede (özellikle bağlaçla bağlı iki eylemde) gereksiz
  zaman kayması hatadır. Doğru (tutarlı geçmiş zaman): "Toplantı saat 10'da
  başladı ve katılımcılar konuyu tartıştı." Yanlış (geçmişten şimdiki zamana
  sebepsiz kayma): "Toplantı saat 10'da başladı ve katılımcılar konuyu
  tartışıyor." (→ "...tartıştı.") NOT: Genel geçer/her zaman doğru olan bir
  durumu belirtmek için ikinci eylemin geniş zaman/şimdiki zaman olması
  MEŞRUDUR (örn. "Cihaz açıldı ve ekranda ana menü görünür." — burada
  "görünür" davranışı her zaman geçerli bir kural bildirir, hata SAYMA);
  yalnız TEK SEFERLİK, geçmişte yaşanmış bir olayı anlatan cümlede zaman
  tutarsızlığı varsa işaretle.
- **GRAMER-SAYI-UYUM** — Sayı belirteciyle (üç, beş, birkaç, çeşitli, birçok
  vb.) kullanılan isim ÇOĞUL eki ALMAZ; sayı zaten çokluğu belirtir. Doğru:
  "üç kullanıcı", "beş çalışan", "birkaç belge". Yanlış: "üç kullanıcılar"
  (→ "üç kullanıcı"), "beş çalışanlar" (→ "beş çalışan"). NOT: Sayı
  belirteci OLMADAN kullanılan çoğul tamamen normaldir ("kullanıcılar
  bilgilendirildi" doğrudur) — yalnız sayı/miktar belirteciyle YAN YANA
  duran çoğul ekini işaretle.
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
  **İSTİSNA (yapısal artık):** BAŞLIK/bölüm adı niteliğindeki bir satırın alt
  alta iki kez tekrarı ("BAŞLARKEN / BAŞLARKEN" gibi) yazarın hatası değil,
  belge dönüştürmesinin (PDF→Word, sayfa başlığı) artığıdır — bulgu ÜRETME.
  Bu kural yalnız CÜMLE İÇİNDEKİ kelime tekrarları içindir.
- **GRAMER-BOLUNMUS-KELIME** — Yan yana duran iki kısa kelime, TEK BAŞLARINA
  geçerli olsalar bile, cümle bağlamında anlamsız durabilir ve birleştirilince
  anlamlı TEK bir kelime oluşturabilir (örn. "kapı dayım" → aslında
  "kapıdayım"; "baş vuru formu" → aslında "başvuru formu"). Sözlük bu durumu
  ayırt edemez (her iki parça da tek başına geçerlidir); yalnız cümlenin
  anlamına bakarak karar ver. Böyle bir durum tespit edilirse `dil_bilgisi`
  bulgusu üret, `suggestion` alanına birleşik doğru biçimi yaz. Yan yana duran
  iki kelime cümlede GERÇEKTEN ayrı ayrı anlamlıysa (örn. "Ali kapıda
  bekliyordu") bulgu ÜRETME.
  **SINIR (uydurma birleştirme yasak):** Önerdiğin birleşik biçim, TDK
  sözlüğünde GERÇEKTEN VAR OLAN tek bir kelime olmalıdır ("kapıdayım" =
  kapı+da+yım çekimi; "başvuru" sözlükte var). İki kelimenin ayrı yazımı
  Türkçede ZATEN DOĞRUYSA ("pil ölçer", "veri tabanı" gibi) sözlükte
  bulunmayan bitişik biçimler ("pilölçer") UYDURMA — böyle öneri ASLA üretme.
- **GRAMER-BILDIRME-EKI** — Bu kural yalnız ŞU YAPISAL ÇAKIŞMAYI hedefler:
  bildirme eki (-dır/-dir/-dur/-dür) bir DURUM/KONUM/ETİKET adını sözde-yükleme
  çevirmiş VE AYNI cümlede bu sözde-yüklemin hemen ardından başka bir asıl
  yüklem ("getirilir", "alınır", "seçilir", "getirilmelidir") geliyor — iki
  yüklem çakışması. Yanlış: "cihaz yeniden Kapalı'dır konumuna
  getirilmelidir" (→ "'Kapalı' konumuna getirilmelidir") — burada -dır etiketi
  sözde yüklem yapıp hemen ardından gelen "getirilmelidir" ile YAPISAL çelişki
  üretir (iki asıl yüklem). **Bu kural etikete tırnak eklemeyi GENEL bir kural
  olarak ÖNERMEZ** — tırnaklama yalnız bu -dır çakışmasını çözerken ortaya
  çıkan bir YAN ETKİDİR, kuralın amacı DEĞİLDİR.
  NOT (yanlış-pozitif kapısı): Bildirme eki bir cümlenin GERÇEK ve TEK
  yükleminde ise tamamen doğrudur ("Cihaz kapalıdır.", "Bu ayar
  varsayılandır.") — bunları ASLA işaretleme; yalnız etiketin -dır ile
  yüklemleşip AYNI cümlede İKİNCİ bir asıl yüklemle (getirilir/alınır/seçilir
  vb.) çakıştığı durumu işaretle. Aynı sözcükteki olası kesme işareti hatası
  ("Kapalı'dır") AYRI bir imla bulgusudur; bu madde yalnız YAPISAL çakışmayı
  hedefler.
  NOT-2 (yanlış-pozitif kapısı — ÖNEMLİ): Bu madde YALNIZ -dır bindirmesi (etiket
  sözde-yüklem + AYNI cümlede ikinci asıl yüklem) varsa işler. -dır eki OLMAYAN
  sade bir cümlede ("Telsizi Kapalı konuma getirin.", "Kapalı konumdayken")
  durum/etiket sözcüğüne SIRF tırnak eklemek için bulgu ÜRETME — tırnak burada
  ÜSLUP tercihidir, dil bilgisi hatası DEĞİLDİR. Yapısal -dır çakışması yoksa bu
  eksende sessiz kal.

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

> (Bu bölüm geliştirici dokümantasyonudur; modele GÖNDERİLMEZ —
> `StaticRulesProvider` yalnız A/B/C bölümlerini kesitler.)

Bu bölüm bilinçli olarak ÇÖZÜLMEYEN, ölçülmüş boşlukları belgeler — kural
genişletmesi burada YAPILMAZ (bkz. `eval/golden.jsonl`'deki ilgili FN örneği).

- **Bitişik/ayrı/yabancı kelime kapsamı hâlâ kapalı bir liste** — Faz 1'de
  (bkz. `eval/tdk_kelime_taslagi.md`) `IMLA-BITISIK`/`IMLA-AYRI`/`IMLA-YABANCI`
  üç TDK grubuyla (ses düşmesi + etmek/olmak bileşikleri, yabancı kelime
  çiftleri, sıfat-fiil kalıpları) genişletildi ve her grup `eval/run_eval.py`
  ile ölçülüp kabul edildi. Ancak bu hâlâ TDK Yazım Kılavuzu'nun TAMAMI
  değil — yalnız kurumsal metinde olası, ölçülmüş, güvenli bir alt küme.
  Taslaktaki "ertelenen" gruplar (anlam kayması bitki/hayvan adları, renk
  adları, yön/konum sözcükleri) yanlış-pozitif riski yüksek olduğu için
  bilinçli olarak dışarıda bırakıldı. Listede olmayan bir bitişik/ayrı/
  yabancı-kelime hatası için bulgu üretilmeyebilir — bu, rastgele bir eksik
  değil, "açıkça tanımlı olmayana hata uydurma" tasarım kararının sonucu.
  Genişletme yalnız ölçülerek (yeni grup + `golden.jsonl` örneği +
  öncesi/sonrası precision/recall) yapılmalı.
- **Sözlük-geçerli ama bağlamda yanlış teknik terim** — Hunspell'in ek-tabanlı
  morfolojik analizi, anlamca yanlış olsa da GEÇERLİ bir sözcük kuruluşuna
  sahip yazım hatalarını genel olarak yakalayamaz. Prompt'u "sözlükte geçerli
  ama bağlamda şüpheli kelimeleri de sorgula" yönünde GENEL olarak genişletmek
  yanlış-pozitif riskini (geçerli teknik terimleri gereksiz sorgulama)
  belirsiz biçimde artırabilir; bu yüzden genel taramaya dokunulmuyor.
  **Kısmi/dar istisna:** `IMLA-BAGLAMSAL-KARISTIRMA` (yukarıda A3) yalnız İKİ
  ölçülmüş, yüksek-güven çift için (günceleme/güncelleme, yarin/yarın) bu
  sınırı kapalı bir liste olarak deler — genel çözüm değil, nokta atışı.
- **4 harften kısa kelimeler denetlenmez** — Hunspell katmanı 1-3 harflik
  "kelimeleri" atlar: bunlar pratikte hep belge dönüştürmesinden kopan ek
  parçalarıdır ("nde", "nda", "nın") ve sözlük denetimine sokulduklarında
  anlamsız bulgular üretirler. Gerçek 1-3 harfli Türkçe kelimelerde yazım
  hatası kayda değer değildir (bilinçli takas).
- **Hunspell öneri üretmez (yalnız tespit)** — Sözlük katmanı "sözlükte yok"
  demekle yetinir; düzeltme önerisi bağlamı gören LLM'den gelir. LLM karar
  vermezse bulgu "(öneri yok ...)" yer tutucusuyla kalır — bu, bağlamdan
  habersiz sözlük önerisinin ("nde"→"ned" gibi) uydurmasından iyidir.
- **PDF-kökenli .docx gürültüsü** — PDF'ten Word'e çevrilmiş belgelerde metin
  kutusu kırpıntıları (yarım cümleler), satır-içi görsel işaretçileri ve
  tekrar eden sayfa başlıkları kalır. Çıkarma katmanı bunların çoğunu süzer
  (satır-içi işaretçi temizliği, ardışık tekrar tekilleştirme, blok türü
  etiketleme) ama kopuk cümle parçaları metinde kalabilir; bunlara üretilen
  "cümle eksik" bulguları belge kalitesinin, sistemin değil, ürünüdür.
  Temiz dijital .docx tercih edilir.
