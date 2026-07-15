# Bilinen Sınırlar — Tam Anlatım ve Gerekçeler

Bu dosya, [CLAUDE.md](../CLAUDE.md)'deki "Bilinen Sınırlar" özetinin tam
hâlidir. Bunlar bilinçli olarak çözülmemiş, ölçülmüş boşluklardır — model
bunları tekrar "bug" sanıp gereksiz uğraşmasın. (Kural boşlukları ayrıca
`src/dilanaliz/rules/rules.md` → "Bilinen Sınırlar" bölümünde.)

---

## Model determinizmi yoktur

Gemini `temperature=0`'da bile aynı isteme çağrı-çağrı farklı yanıt
verebilir; aynı metin iki koşuda biraz farklı bulgu üretebilir. Bu
paralellikten DEĞİL, modelin doğasındandır.

## Bayat önbellek

Bir kez üretilen (belki eksik) yanıt `.cache/`'e kalıcı yazılır; kod/kural
değişse de aynı metin için eski yanıt döner. Beklenmedik "eksik sonuç"ta ilk
kontrol: `rm -rf .cache/` ve tekrar dene.

## Sözlük-geçerli bağlamsal yazım hatası

Hunspell morfolojik olarak kurulabilen ama bağlamda yanlış kelimeleri
yakalayamaz (ör. "güncelleme" yerine "günceleme"). Prompt'u genişletmek
yanlış-pozitif riskini artırır; bilinçli olarak dokunulmadı (`golden.jsonl`'de
ölçülü FN örneği var).

## Çapraz-geçiş çelişkisi (daraltıldı)

Geçişler birbirini görmez; aynı ifade iki geçişten iki bulgu alabilir.
Örtüşen konum + (AYNI alıntı YA DA AYNI atomik düzeltme —
`_atomic_correction`: tek kelime farkı üzerinden "aynı hatayı mı düzeltiyor"
testi) taşıyan tip-kopyaları artık `postprocess.drop_cross_pass_duplicates`
ile teke iner (imla > dil_bilgisi > ton önceliği; tutarlılık muaf). Atomik
düzeltme çıkarılamayan (çok kelimeli/serbest yeniden yazım) örtüşen bulgular
hâlâ İKİSİ DE korunur — bilinçli kalan sınır budur.

## Uzun belge tutarlılık ölçeği

Küçük belgede tutarlılık tek çağrıyla çalışır; belge
`CONSISTENCY_MAP_REDUCE_CHARS`'ı aşınca map-reduce'a geçer (terim-indeksi +
aday kümeleme + tek yargı — tek dev çağrının zaman aşımı çözüldü). Kalan
sınırlar:

- (a) map bir kavramı parçalarda FARKLI `concept`'le etiketlerse eşanlam
  kümesi (PTT↔BK) kaçabilir;
- (b) gerçek bir eşanlam kümesi `_CONCEPT_CLUSTER_MAX`'tan (3) çok varyant
  taşırsa jenerik sanılıp atılır (nadir);
- (c) reduce ham metnin geniş bağlamı olmadan karar verir, ince bağlamsal
  çakışmaları kaçırabilir;
- (d) salt büyük/küçük harf farkıyla ayrılan kümeler bilinçli elendiğinden
  gerçek bir ürün-adı harf tutarsızlığı (örn. "iVOX" ↔ "IVOX") tutarlılık
  geçişinde YAKALANMAZ — bu, "standart pil" ↔ "Standart Pil" gibi
  başlık/düzyazı sahte-pozitiflerini kesmek için verilen bilinçli takastır.

Yine de eski "dev çağrı zaman aşımı → hiç sonuç yok" durumundan kesin daha
iyidir. Eşik ve küme sınırı sezgiseldir; `run_eval` + gerçek belgeyle
ayarlanabilir.

## OCR/çıkarma gürültüsü

Girdi OCR ürünüyse İ/I karışması, kelime-içi boşluk/nokta gibi bozulmalar
sahte bulgu üretir ("çöp girer, çöp çıkar"). Temiz dijital `.docx` tercih
edilir. PDF'ten çevrilmiş `.docx`'lerde çıkarma katmanı görsel işaretçilerini
(tam-satır görsel silinir; cümle içindeki satır-içi görsel `[görsel]` yer
tutucusuna dönüşür — LLM bunu yok sayar, cümleyi görsel yerindeymiş gibi
değerlendirir) ve ardışık tekrar başlıkları süzer; ama metin kutusu
kırpıntıları (yarım cümleler) metinde kalabilir ve "cümle eksik" bulguları
üretebilir — bu belge kalitesinin ürünüdür.

## 4 harften kısa kelimeler imla denetimine girmez

Kopuk ek parçaları ("nde", "nda") sahte bulgu üretmesin diye bilinçli eşik;
1-3 harfli gerçek kelime hatası bu katmanda yakalanmaz (bkz. `rules.md` →
Bilinen Sınırlar).

## Tablo verisi dil denetimi dışıdır

Etiketli bloklarda `tablo_hucresi` türü imla/dil bilgisi/ton geçişlerinden
muaftır; tablodaki ondalık-nokta kullanımı tek TEK değil belge-geneli tek
özet bulguyla raporlanır (N ≥ 3). Tablo hücresindeki bir yazım hatası bu
yüzden raporlanmayabilir (bilinçli takas — tablo verisi düzyazı değildir).
Gerçek belge ölçümü (60 sayfalık kılavuz): sorun giderme tablolarında ~400
kelimelik gerçek düzyazı da bu muafiyete girer — bilinçli olarak kabul
edildi (2026-07-04); ileride ölçümle (eval) yeniden değerlendirilebilir.

## İçindekiler (TOC) satırları dil denetimi dışıdır

`icindekiler` türü (blok deseni: `"Başlık<sekme><sayfa no>"`) tablo
hücresiyle aynı muameleyi görür: imla/dil bilgisi/ton geçişlerinden muaf,
tutarlılık geçişinde dahil. Gerekçe: TOC, Word'ün ürettiği metindir (başlığın
kendisi gövdede zaten denetlenir) ve uzun girdiler satır sonunda kopuk
parçalara bölünerek sahte "cümle eksik" bulgusu üretir.

## Bir parçanın LLM çağrısı kalıcı başarısız olursa TÜM analiz durur

`LLM_TIMEOUT_SEC` + kütüphane retry'ı geçici hataları çözer ve hata mesajı
artık anlaşılır (`LLMCallError`); ama paralel/sıralı hiçbir yol tek bir
parçayı "atla, diğerlerine devam et" şeklinde esnetmez — bilinçli tercih
(sessiz eksik sonuç, yanlış-pozitif kadar tehlikeli olan yanlış-negatif/
eksik rapor riski taşır). Kalıcı hata → kullanıcı net mesajla tekrar dener.
