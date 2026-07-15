# Mimari "Seam"leri — Tam Anlatım ve Gerekçeler

Bu dosya, [CLAUDE.md](../CLAUDE.md)'deki "Mimari Seam'leri" özetinin tam
hâlidir: her seam'in gerekçesi, iç işleyişi ve tarihçesi burada tutulur.
**Demir kurallar (ne yapılmalı/yapılmamalı) CLAUDE.md'de özet olarak durur;
bir seam'e dokunmadan önce buradaki ilgili bölümü oku.**

---

## Davranış / Bilgi ayrımı

`prompt.py` yalnız modelin *davranışını* tutar; *kurallar* `RulesProvider`
üzerinden ayrı gelir. Kural değişikliği `rules.md` veya `.env`'deki
`RULES_PATH` ile yapılır, **kod değişmeden**. Sağlayıcı **geçiş-farkındadır**:
`get_context(text, purpose)` — yerel geçiş yalnız A+B (imla + dil bilgisi),
ton geçişi yalnız C bölümünü alır; `rules.md`'nin "Bilinen Sınırlar" bölümü
geliştirici notudur, modele HİÇ gönderilmez. Tanınan başlığı olmayan harici
`RULES_PATH` dosyasında kesitleme devre dışı kalır (tam metin gider — kural
sessizce kaybolmaz). Yeni geçiş eklerken purpose eşlemesini
(`rules/static.py` → `_PURPOSE_KINDS`) güncelle.

## Sağlayıcı soyutlaması

`providers/build_chat_model` bir LangChain `BaseChatModel` döndürür.
Gemini'yi yerel vLLM ile değiştirmek analyzer'ı etkilememeli.

## Katı JSON çıktı

`with_structured_output` parse hatasını engeller; çıktı şeması
`schema.py`'dedir, gevşetme.

## Gözlem kanalı (`observations`) findings'ten AYRIDIR

Model "kurala bağlayamadığı ama şüphelendiği" yerleri `findings`'e DEĞİL
`AnalysisResult.observations`'a (`schema.Observation`: excerpt + note,
offset/öneri YOK) yazar. Ayrı bir LLM çağrısı DEĞİL; yalnız **yerel geçişin**
çıktı şemasına eklenen bir alan (ton/tutarlılık boş bırakır, tıpkı `spelling`
gibi). Gözlem, findings boru hattına (locate/`drop_unlocated`/
`drop_cross_pass_duplicates`/`_sort_key`/`_dedup`) HİÇ girmez → determinizm
sözleşmesi (findings) değişmez; gözlemin kendisi `_finalize`'da
`_dedup_sort_observations` ile `(excerpt, note)` anahtarıyla ayrıca
tekilleştirilip sıralanır (paralel toplamadan bağımsız). Ölçüme GİRMEZ:
`run_eval._match` yalnız `result.findings` okur; gözlem precision/recall'a
katılmaz (bilinçli — doğrulanmamış kanal). Web/rapor gözlemi "doğrulanmamış —
editör değerlendirmesi gerekir" etiketiyle AYRI bölümde gösterir, bulgularla
asla karışmaz. Model bu kanalı ancak prompt'ta SOMUT ÖRNEK varsa kullanır
(örneksiz → sessiz; bkz. Görev 1 tezi). Uzun vadede yeni kuralların keşif
hattıdır (gözlem → editör onayı → rules.md kuralı).

## Konumlanamayan bulgu sessizce elenir

`postprocess.drop_unlocated_findings` (`_finalize` içinde çağrılır)
`locate.py`'nin offset veremediği (kaynakta BİREBİR/normalize bulunamayan)
bulguları atar. Bunlar çoğunlukla LLM'in `rules.md`'deki bir "Yanlış:"
örneğini analiz edilen metnin DOĞRU yazılmış hâliyle karıştırıp var olmayan
bir alıntı üretmesinden kaynaklanır (halüsinasyon). `locate.py`'nin kendisi
None bırakmaya devam eder (yalnız konumlama, politika değil); eleme kararı
`_finalize`'dadır — yeni bir geçiş eklerken bu sözleşmeyi koru.

## Bağlamca zaten karşılanmış öneri elenir

`postprocess.drop_context_satisfied_findings` (`_finalize` içinde,
`drop_unlocated_findings`'in hemen ardından çağrılır) alıntının kaynaktaki
HEMEN ARDINDAN gelen karakterleriyle önerinin fazladan kısmı birebir aynıysa
bulguyu atar (örn. cümle zaten "...sunuyoruz." diye bitmişken, model alıntıyı
noktadan önce kesip "sunuyoruz." öneriyor — nokta zaten alıntının hemen
ardında var, öneri hiçbir şey değiştirmiyor). `is_noop_suggestion` bunu
YAKALAYAMAZ çünkü yalnız excerpt/suggestion metnini karşılaştırır, kaynak
bağlamına bakmaz — bu yüzden ayrı bir fonksiyon ve offset (konumlama sonrası)
gerektirir.

## Kademeli geçiş + parçalama

Orkestrasyon (`analyzer.py`) her kontrolü kendi bazında ayrı geçişte
çalıştırır; parçalama (`chunk.py`) deterministik koddur. Parça-içi offsetler
kaynağa geri taşınır (rebasing) — yeni geçiş/baz eklerken bu sözleşmeyi koru.

## Paralel ama deterministik

Parçalar `CONCURRENCY` kadar eşzamanlı işlenir (ThreadPoolExecutor); ama
çıktı işlenme sırasından BAĞIMSIZ olmalı. `_finalize` bulguları tam-sıra
anahtarıyla (`_sort_key`) önce sıralar, sonra tekilleştirir — böylece
`CONCURRENCY` ne olursa olsun sonuç birebir aynıdır. Yeni geçiş/bulgu
eklerken bu deterministiklik sözleşmesini koru; önbellek (`cache.py`) ve
ilerleme yayını thread-safe'tir (kilitli).

## Belge-geneli tutarlılık: küçük belgede tek çağrı, büyük belgede map-reduce

Tutarlılık geçişi (terim/kısaltma çakışması) bütünsel görüş gerektirir; ham
metni naif parçalayıp her parçaya AYRI sorarsan "AI"↔"Artificial
Intelligence" gibi çapraz-parça çakışmaları göremezsin (kör nokta). Bu
yüzden: **küçük belge** (≤ `CONSISTENCY_MAP_REDUCE_CHARS`) tek çağrıda
görülür (`_consistency_pass` → `build_consistency_message` +
`CONSISTENCY_SYSTEM_PROMPT`). **Büyük belge** (uzun belgede tek dev çağrı
Google'da zaman aşımına uğrar) `_consistency_map_reduce` ile çalışır:

1. **MAP** — her parçadan yalnız sabit terim/kısaltma/birim/etiket çıkarılır
   (paralel; ayrı şema `LLMTermExtraction`, `TERM_EXTRACT_SYSTEM_PROMPT`);
2. **ADAY KÜMELEME** — `_build_term_index` gürültüyü (`_is_indexable_term`:
   sayı/değer/ölçüm yüzeyleri) eler, sonra yüzeyleri YALNIZ TUTARSIZLIK ADAYI
   kümelere indirger: ya yüzey-anahtarı (`_norm_surface_key`:
   harf/tırnak/boşluk-duyarsız → yazım varyantı) ya kavram-anahtarı
   (`_norm_concept_key` → eşanlam) altında ≥2 farklı yüzey. Jenerik kavram
   kümeleri (`_CONCEPT_CLUSTER_MAX` üstü — "özellik adı", "bölüm başlığı")
   atılır. SALT büyük/küçük harf farkıyla ayrılan kümeler de ELENİR (başlık
   "Başlık Düzeni" ↔ düzyazı küçük harf DOĞAL farktır — en sık sahte-pozitif
   kaynağıydı; birim harfi kHz↔Khz zaten yerel IMLA-BIRIM'de yakalanır,
   burada tekrar üretme). TEK biçimde geçen terim hiç gönderilmez (tutarsız
   olamaz) → reduce girdisi belge boyutundan BAĞIMSIZ küçük kalır;
3. **REDUCE** — LLM'e ham metin DEĞİL bu aday kümeler gönderilir
   (`CONSISTENCY_REDUCE_SYSTEM_PROMPT`), her küme için "gerçekten aynı mı?"
   yargısı `tutarlilik` bulguları üretir.

Aday kümeleme belgenin tamamından toplandığından bütünsel görüş korunur (kör
nokta gelmez); her adımın girdisi küçük olduğundan zaman aşımı tavanı kalkar.
Offset yine `enrich_with_offsets` ile (LLM offset üretmez); reduce
`excerpt`'i kümedeki bir `surface` ile birebir olmalıdır ki konumlanabilsin.
İlerleme (`on_progress` → web SSE) map k/N + reduce adımını canlı bildirir.
**Naif "böl ve her parçaya ayrı tutarlılık sor" hâlâ yasak** — reduce'un tek
yargı adımı bütün adayları bir arada görür, çözüm budur.

## Etiketli blok sözleşmesi

`extract_docx_blocks` blok türü haritası (`BlockSpan`) döndürür; offsetler
birleşik metinle birebir hizalıdır (`text[s.start:s.end]` bloğun kendisi).
`analyzer.analyze_document(spans=...)` bu haritayla yapısal süzme yapar;
süzme `_finalize` sıralamasından ÖNCE ve tamamen deterministiktir. Yeni blok
türü/süzme kuralı eklerken bu hizalamayı ve determinizmi koru. Tutarlılık
bulguları tablo aralıklarında da KORUNUR (birim çakışması tabloda geçerli) —
bunu süzmeye dahil etme.

## Hunspell yalnız tespitçidir

`spell.py` öneri üretmez (`suggest()` çağrısı bilinçli kaldırıldı); öneri
`_resolve_spelling`'de LLM'den gelir ve alıntının harf düzenine giydirilir
(`match_case`). Hunspell'e yeniden öneri ürettirme — bağlamdan habersiz
sözlük önerisi kopuk parçalara uydurma üretir.

## Air-gap uyumu

Bağımlılıklar pinli; telemetri kapalı; gizli dış çağrı ekleme. `docx2python`,
Hunspell ve web paneli (stdlib) dahil her şey yereldir.

## LLM çağrısı: zaman aşımı + SINIFLANDIRILMIŞ hata

`providers/gemini.py` istemciye `LLM_TIMEOUT_SEC` (varsayılan 60sn) +
`max_retries=2` geçer (kütüphane retry'ı kalıcı 404'ü de körlemesine dener,
o yüzden düşük). Asıl savunma `analyzer._call_structured`'dadır ve hataları
SINIFLANDIRIR:

- (a) **KALICI** (kapatılmış/yok model — `_is_permanent_model_error`) →
  yeniden deneme YOK, `LLMCallError(permanent=True)` net "MODEL_ID güncelle"
  mesajıyla;
- (b) **GEÇİCİ** (timeout/ağ) → 3 deneme, sonra "bağlantı" mesajlı
  `LLMCallError`;
- (c) model yapılandırılmış çıktı üretemezse (`None` yanıt — json_mode ile
  nadir) → geçici gibi yeniden denenir.

CLI (`cli.py`) hatayı tek satır mesajla gösterir, web paneli (`server.py`)
SSE'ye basar. Bir parçanın çağrısı kalıcı başarısız olursa TÜM analiz durur
(bilinçli — bkz. [bilinen-sinirlar.md](bilinen-sinirlar.md)); bu davranışı
sessiz-atlamaya çevirme. (`eval/run_eval.py` örnek-bazında farklıdır: geçici
hatada örneği atlar + KISMİ SONUÇ damgası basar; kalıcıda o da durur.)
