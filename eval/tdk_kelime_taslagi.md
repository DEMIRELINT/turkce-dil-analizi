# TDK Kelime Taslağı — Faz 1 Adım 1 Ham Girdi

Bu dosya **üretim kodunun parçası değildir**; `rules.md`'ye grup grup
aktarılacak ham malzemedir (bkz. `CLAUDE.md` → Faz 1 planı, Adım 4).
Doğrudan `rules.md`'ye kopyalanmaz — her grup önce buradan seçilir, sonra
`eval/run_eval.py` ile ölçülerek eklenir.

**Kaynak yöntemi:** `tdk.gov.tr/icerik/yazim-kurallari/...` sayfalarına
doğrudan otomatik erişim (WebFetch) 403 döndürdüğü için, madde madde
`WebSearch` sorgusuyla TDK'nin kural metni + örnek kelimeleri (arama
motoru snippet'i üzerinden) derlendi. Her blok altında hangi sorgudan
geldiği not edilmiştir. Şüpheli/az bilinen kelimeler `rules.md`'ye
aktarılmadan önce `sozluk.gov.tr` ile tek tek teyit edilmeli.

---

## 1. Bitişik yazılan birleşik kelimeler (A2 → IMLA-BITISIK)

### 1a. Ses düşmesine uğrayanlar
birbiri, kaynana, kaynata, nasıl, niçin, pazartesi, sütlaç

*(Kaynak: TDK "Bitişik Yazılan Birleşik Kelimeler" sayfası özeti)*

### 1b. etmek/edilmek/olmak/olunmak ile ses olayına uğrayanlar
affetmek, bahsetmek, emretmek, hissetmek, kahrolmak, kaybolmak,
reddetmek, sabretmek, seyretmek, zannetmek, hükmetmek, şükretmek,
cemetmek, dercetmek, hamdetmek, menolunmak

*(Bunlar mevcut `dosyalar/tr_TR.dic` sözlüğünde muhtemelen zaten geçerli
kelimeler olarak var — Hunspell'in yakalayamadığı asıl durum bunların
YANLIŞLIKLA AYRI yazılmış hâlleri: "af etmek", "his setmek" değil "hiss
etmek" gibi. `rules.md`'ye eklerken örnek cümleyi "ayrı yazılmış yanlış
biçim → bitişik doğru biçim" olarak vermek gerekir.)*

### 1c. Sıfat-fiil ekleriyle kurulan kalıplaşmışlar (-an/-en, -r/-ar/-er/-ır/-ir, -maz/-mez, -mış/-miş)
alaybozan, cankurtaran, çöpçatan, dalgakıran, demirkapan, gökdelen,
yelkesen, akımtoplar, altıpatlar, barışsever, basınçölçer, özezer,
pürüzalır, baştanımaz, değerbilmez, etyemez, hacıyatmaz, kadirbilmez,
karıncaezmez, kuşkonmaz, külyutmaz, tanrıtanımaz, varyemez, çokbilmiş,
güngörmüş

*(Kurumsal metinlerde bunlardan en olası pratik değeri olanlar:
gökdelen, cankurtaran, dalgakıran, basınçölçer — geri kalanı düşük
frekanslı, ilk grupta öncelik bunlara verilebilir.)*

### 1d. Anlam kayması olan birleşik kelimeler (bitki/hayvan/nesne adları)
ayakkabı, hanımeli, keçiboynuzu, kuşburnu, turnagagası, açıkağız,
akkuyruk, alabaş, altınbaş, çobançantası, karnıkara, katırtırnağı,
kuşyemi, şeytanarabası, yılanyastığı, akşamsefası, camgüzeli

*(Düşük öncelik — kurumsal/teknik metinlerde nadiren geçer; Faz 1'in ilk
grubuna dahil ETME, gerekirse sonraki turda.)*

### 1e. Üretken kalıp — SÖZLÜK DEĞİL, KURAL (not, kelime listesi değil)
"-a/-e + bil-/gel-/kal-/dur-/yaz-/ver-" ile kurulan tasvirî/yeterlilik
fiilleri (gidebilmek, yazabilmek, düşünedurmak, öleyazmak) **kapalı bir
kelime listesi değildir** — herhangi bir fiil kökü + bu ekle üretilebilir
(açık uçlu, üretken bir morfolojik kural). Bu yüzden `IMLA-BITISIK`'e
kelime kelime eklenmez; ayrı bir KURAL cümlesi olarak ("fiil + a/e-bil
öbeği her zaman bitişik yazılır") rules.md'ye tek satır not düşülebilir.
Bunu Faz 1 Adım 4'te ayrıca değerlendir — plan kapsamının "kapalı küme"
varsayımına tam uymuyor, dikkatli ele alınmalı.

---

## 2. Ayrı yazılan birleşik kelimeler (A2 → IMLA-AYRI)

### 2a. Sıfat-fiil ekleriyle kurulan sıfat tamlaması yapısındakiler
bakar kör, çalar saat, çıkar yol, döner sermaye, güler yüz, koşar adım,
yazar kasa, yeter sayı, çıkmaz sokak, geçmez akçe, görünmez kaza, ölmez
çiçek, tükenmez kalem

*(Kurumsal metinde en olası: "çalar saat" değil ama "döner sermaye",
"yeter sayı", "tükenmez kalem" gibi kalemler idari/mali metinlerde
geçebilir.)*

### 2b. Renk adı + "rengi/mavisi/sarısı" vb. ile kurulanlar
bal rengi, duman rengi, gümüş rengi, portakal rengi, saman rengi, ateş
kırmızısı, çivit mavisi, gece mavisi, limon sarısı

*(Düşük öncelik — kurumsal metinde nadiren geçer.)*

### 2c. Yön/konum bildiren sözcükler (mevcut yer adı bağlamında)
batı, doğu, güney, kuzey, güneybatı, güneydoğu, kuzeybatı, kuzeydoğu,
aşağı, yukarı, orta, iç, yakın, uzak — bunlar bir yer adına sıfat olarak
geldiğinde ayrı yazılır (İ.Ö. "Güney Kore" gibi; bileşik özel ad
oluşturmadıkları sürece).

*(Bu grup DÜŞÜK öncelikli ve büyük ölçüde özel ad bağlamına bağlı — Faz
1'in ilk turuna alınması riskli, yanlış-pozitif üretebilir. Ertelenmesi
önerilir.)*

---

## 3. Yabancı kökenli kelimelerin doğru yazımı (A3/A6 → IMLA-YABANCI genişletmesi)

Mevcut `rules.md` A3'te zaten: şoför, orijinal, egzoz, espri, kontrol,
makine, sürpriz, laboratuvar var. Aşağıdakiler ek aday (yanlış → doğru):

- aksesuvar → **aksesuar**
- antreman → **antrenman**
- aktivasyon (aktifasyon değil) → **aktivasyon**
- profösör / profesör → **profesör**
- egzersiz (egzersize/ekzersiz değil) → **egzersiz**
- transfer (transger değil) → **transfer**
- şarj (şarz değil) → **şarj**
- kapasite (kapasiteli değil, "kapasite" doğru; sık hata "kapesite") →
  **kapasite**
- adaptör (adapter değil) → **adaptör**
- performans (perfomans değil) → **performans**
- sertifika (sertifikasyon karışıklığı; "sertifika" doğru) → **sertifika**
- lisans (lizans değil) → **lisans**
- entegrasyon (entregasyon değil) → **entegrasyon**
- konfigürasyon (konfigrasyon değil) → **konfigürasyon**

**NOT — güven düzeyi düşük liste:** Bu son grup, TDK'nin resmî sayfası
yerine ikincil "en çok karıştırılan kelimeler" derlemelerinden geldi;
`rules.md`'ye eklenmeden önce her biri `sozluk.gov.tr`'de tek tek teyit
edilmeli (bazıları TDK sözlüğünde yer almayabilir / güncel yazım farklı
olabilir — özellikle "adaptör", "konfigürasyon" gibi teknik terimler).

**Yabancı kelimede "ğ" kullanılmaz** kuralı (grup - gurup değil, film -
filim değil) mevcut A3'e genel bir alt-not olarak eklenebilir.

---

## Öncelik Sırası Önerisi (Faz 1 Adım 4 için gruplama)

1. **Grup 1 (en güvenli, yüksek TDK teyit güveni):** 1a + 1b (ses
   düşmesi + etmek/olmak bileşikleri) — az sayıda, kesin, örnek cümle
   üretimi kolay.
2. **Grup 2:** 3'teki mevcut A3 genişletmesi (yabancı kelime), önce
   `sozluk.gov.tr` teyidi yapılmış alt küme.
3. **Grup 3:** 1c (sıfat-fiil kalıpları) — yalnız kurumsal metinde
   olası olanlar (gökdelen, cankurtaran, dalgakıran, basınçölçer,
   tükenmez, döner sermaye, yeter sayı).
4. **Ertelenen (ölçülmeden eklenmeyecek, yanlış-pozitif riski yüksek):**
   1d (anlam kayması bitki/hayvan adları), 2b (renk adları), 2c
   (yön/konum sözcükleri) — kurumsal metinde düşük frekans, bağlam
   duyarlılığı yüksek.
5. **Ayrı ele alınacak (kelime listesi değil, kural notu):** 1e (üretken
   -a/-e bil/gel/kal/dur/yaz/ver kalıbı).
