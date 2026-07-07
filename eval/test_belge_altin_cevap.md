# Altın Belge — Cevap Anahtarı (bilinen gömülü hatalar)

Belge: `eval/test_belge_altin.txt`. Aşağıdaki **15 bulgu + 1 gözlem** bilinçli gömüldü;
gerisi kasıtlı olarak temiz. Amaç: sistem kaçını yakalıyor (recall) ve temiz kısımda
uydurma bulgu üretiyor mu (precision).

## Beklenen BULGULAR (15)

| # | Bölüm | Alıntı | Beklenen | Eksen / Kural |
|---|---|---|---|---|
| 1 | 1 | "yanlız" | yalnız | imla / IMLA-YANLIS |
| 2 | 1 | "herşey" | her şey | imla / IMLA-HERSEY |
| 3 | 1 | "daha hızlı daha güvenli ve" | eksik virgül: "daha hızlı, daha güvenli ve" | imla / IMLA-NOKTALAMA |
| 4 | 2 | "yöneticiyede" | yöneticiye de (bağlaç ayrı) | imla / IMLA-DE-DA |
| 5 | 2 | "Unutmayınki" | Unutmayın ki (bağlaç ayrı) | imla / IMLA-KI |
| 6 | 2 | "Ankarada" | Ankara'da (özel ada çekim eki kesmeli) | imla / IMLA-KESME |
| 7 | 3 | "12.5 GB" | 12,5 GB (ondalık virgül) | imla / IMLA-BIRIM |
| 8 | 3 | "500mb" | 500 MB (boşluk + büyük harf) | imla / IMLA-BIRIM |
| 9 | 3 | "beş kullanıcılar" | beş kullanıcı (sayı+çoğul) | dil_bilgisi / GRAMER-SAYI-UYUM |
| 10 | 3 | "oluşturulurlar" | oluşturulur (cansız çoğul → tekil yüklem) | dil_bilgisi / GRAMER-OZNE-YUKLEM |
| 11 | 5 | "sunucuya sunucuya" | sunucuya (ardışık tekrar) | dil_bilgisi / GRAMER-TEKRAR |
| 12 | 5 | "Aktif'tir konumuna alınır" | 'Aktif' konumuna (bildirme eki yapısal) | dil_bilgisi / GRAMER-BILDIRME-EKI *(Görev 1)* |
| 13 | 5 | "Sunucu ... güç kaynağıyla soğutulmalıdır" | özne-araç mantık tersliği | dil_bilgisi / GRAMER-ANLATIM *(Görev 1)* |
| 14 | 2↔4 | "parola" ↔ "şifre" | terim tutarsızlığı (aynı kavram) | tutarlilik |
| 15 | 4 | "Rapor Ekranı" (çift tırnak) | 'Yönetim Paneli'/'Ayarlar Menüsü' (tek tırnak) baskın → stil tutarsızlığı | tutarlilik *(Görev 2)* |

## Beklenen GÖZLEM (1) — Görev 3

| # | Bölüm | Alıntı | Not | Kanal |
|---|---|---|---|---|
| G1 | 6 | "kullanıcı sayısı arttıkça yedekleme süresi kısalır ve sunucu yükü azalır" | mantıksal olarak ters/şüpheli iddia — dil hatası değil | observations |

## Bilinçli TEMİZ (uydurma bulgu ÇIKMAMALI)
- "Bulut Yedekleme Sistemi'nin" — özel ada kesme DOĞRU.
- "yalnızca üretici tarafından onaylanan" (Böl. 5) — cümlenin bu kısmı doğru; hata özne-araç ilişkisinde.
- "'Yönetim Paneli'nden", "Rapor Ekranı"nı" — tırnaklı ifadeye ek kesmesiz DOĞRU (yalnız stil karışıklığı bulgu #15).
- Sayı yazımı ("beş", "12,5 GB") tek biçimde → tutarsızlık DEĞİL.

## Notlar (tartışmalı / ikincil — sayılmayabilir)
- #12 "Aktif'tir" ayrıca bir IMLA-KESME sayılabilir (yapısal bulguyla aynı yerde); ikisinden biri yeterli.
- Model determinizmi yoktur: özellikle #13 (öznel/mantıksal) ve gözlem G1 çağrıdan çağrıya oynayabilir.
