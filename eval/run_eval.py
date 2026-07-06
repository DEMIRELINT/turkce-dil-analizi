"""Altın set üzerinde eksen-bazlı precision/recall ölçümü.

Çalıştırma (GEMINI_API_KEY gerekli):
    python eval/run_eval.py

Eşleştirme: bir tahmin, aynı eksende (type) ve alıntısı beklenen alıntıyla
örtüşen (biri diğerini içeren, büyük/küçük harf duyarsız) bir beklenen bulguya
denk geliyorsa Doğru Pozitif (TP) sayılır. Artan tahminler FP, eşleşmeyen
beklenenler FN'dir. TEMİZ metinlerdeki tüm tahminler FP'dir (yanlış pozitif).

ÇEKİRDEK vs TON: Özet skor (ÇEKİRDEK) yalnız imla + dil bilgisi + tutarlılıktan
hesaplanır; ton AYRI raporlanır (bkz. CORE_AXES). Ton öznel ve gürültülü bir
eksendir, özellikle kılavuz/talimat metninde (emir kipi normaldir) yanlış-
pozitif baskındır — çekirdek precision'a katılırsa güçlü eksenlerin gerçek
başarısını maskeler.

Kısmi/ucuz koşu: EVAL_FILTER ortam değişkeniyle yalnız belirli id'leri (veya
id ön eklerini) çalıştır — ücretli API'de her küçük kural değişikliğinde tüm
örnekleri göndermemek için. Tam koşu yalnız büyük kilometre taşlarında (bir
Faz'ın sonu, PR öncesi) önerilir.
    EVAL_FILTER=imla-yabanci,temiz EVAL_DELAY_SEC=0 python eval/run_eval.py
"""

from __future__ import annotations

import json
import os
import time
from collections import defaultdict
from pathlib import Path

from dilanaliz.analyzer import build_default_analyzer
from dilanaliz.schema import AnalysisResult

GOLDEN = Path(__file__).with_name("golden.jsonl")
DUMP = Path(__file__).with_name("last_predictions.json")
AXES = ["imla", "dil_bilgisi", "ton", "tutarlilik"]
# "GENEL" (çekirdek) skoru YALNIZ bu eksenlerden hesaplanır. Ton bilinçli olarak
# DIŞARIDA: öznel + gürültülü bir eksendir ve özellikle kılavuz/talimat
# metninde (emir kipi normaldir) yanlış-pozitif baskındır; çekirdek precision'a
# katılırsa güçlü eksenlerin gerçek başarısını maskeler. Ton ayrı raporlanır.
CORE_AXES = ["imla", "dil_bilgisi", "tutarlilik"]


def _norm(s: str) -> str:
    return " ".join(s.lower().split())


def _overlap(a: str, b: str) -> bool:
    na, nb = _norm(a), _norm(b)
    return na in nb or nb in na


def _match(expected: list[dict], result: AnalysisResult):
    """Eksen-bazlı TP/FP/FN sözlükleri döndürür."""
    tp = defaultdict(int)
    fp = defaultdict(int)
    fn = defaultdict(int)

    preds = [(f.type.value, f.excerpt) for f in result.findings]
    used = [False] * len(preds)

    # Tür YUMUŞAK: eşleştirme yalnız alıntı örtüşmesine bakar (tür bilgiseldir).
    # Böylece "Slm = imla mı ton mu" gibi savunulabilir tür farkları ceza yazmaz.
    # Eksen bucket'ı için beklenen (ground-truth) tür kullanılır.
    for exp in expected:
        etype, eexc = exp["type"], exp["excerpt"]
        hit = False
        for i, (ptype, pexc) in enumerate(preds):
            if not used[i] and _overlap(eexc, pexc):
                used[i] = True
                tp[etype] += 1
                hit = True
                break
        if not hit:
            fn[etype] += 1

    for i, (ptype, _) in enumerate(preds):
        if not used[i]:
            fp[ptype] += 1

    return tp, fp, fn


def main() -> None:
    analyzer = build_default_analyzer()

    total_tp = defaultdict(int)
    total_fp = defaultdict(int)
    total_fn = defaultdict(int)
    clean_fp = 0       # çekirdek eksenler (imla + dil bilgisi + tutarlılık)
    clean_fp_tone = 0  # ton — ayrı sayılır (çekirdeğe katılmaz)

    # Gemini ücretsiz katman dakikada 5 istekle sınırlı. Çağrılar arasına bekleme
    # koyarak 429'u önleriz. Ücretli katmanda EVAL_DELAY_SEC=0 ile kapatılabilir.
    delay = float(os.getenv("EVAL_DELAY_SEC", "13"))

    examples = [json.loads(line) for line in GOLDEN.read_text(encoding="utf-8").splitlines() if line.strip()]

    filt = os.getenv("EVAL_FILTER", "").strip()
    if filt:
        full_count = len(examples)
        prefixes = [p.strip() for p in filt.split(",") if p.strip()]
        examples = [ex for ex in examples if any(ex["id"] == p or ex["id"].startswith(p) for p in prefixes)]
        print(f"[EVAL_FILTER={filt!r}] {len(examples)} örnek seçildi (tam set {full_count}).")

    dump: list[dict] = []
    processed = 0
    aborted = False
    for i, ex in enumerate(examples):
        if i > 0 and delay > 0:
            time.sleep(delay)
        try:
            # "document" modu uzun belge yolunu (parçalama + kademeli geçiş)
            # ölçer; diğerleri kısa metni tek parça olarak değerlendirir.
            if ex.get("mode") == "document":
                result = analyzer.analyze_document(ex["text"])
            else:
                result = analyzer.analyze(ex["text"])
        except Exception as exc:  # kota (429) vb. — eldekini kaybetme
            print(f"! {ex['id']}: çağrı başarısız ({type(exc).__name__}). Durduruluyor.")
            aborted = True
            break

        tp, fp, fn = _match(ex["expected"], result)
        for ax in AXES:
            total_tp[ax] += tp[ax]
            total_fp[ax] += fp[ax]
            total_fn[ax] += fn[ax]
        if not ex["expected"]:
            clean_fp += sum(1 for f in result.findings if f.type.value != "ton")
            clean_fp_tone += sum(1 for f in result.findings if f.type.value == "ton")
        dump.append(
            {
                "id": ex["id"],
                "text": ex["text"],
                "expected": ex["expected"],
                "predicted": [
                    {"type": f.type.value, "excerpt": f.excerpt, "suggestion": f.suggestion}
                    for f in result.findings
                ],
                # Gözlemler skora GİRMEZ (ayrı kanal); yalnız elle denetim +
                # keşif hattı görünürlüğü için dökülür.
                "observations": [
                    {"excerpt": o.excerpt, "note": o.note} for o in result.observations
                ],
            }
        )
        processed += 1
        n_obs = len(result.observations)
        obs_note = f" gözlem={n_obs}" if n_obs else ""
        print(
            f"- {ex['id']}: bulgu={len(result.findings)} "
            f"beklenen={len(ex['expected'])}{obs_note}"
        )

    # Hata olsa bile eldeki tahminleri kalibrasyon için diske yaz.
    DUMP.write_text(json.dumps(dump, ensure_ascii=False, indent=2), encoding="utf-8")
    if aborted:
        print(f"\n[Kısmi çalışma] {processed}/{len(examples)} örnek işlendi. "
              f"Sonuçlar {DUMP.name}'a yazıldı; kalanlar önbellekten devam edecek.")

    def _line(label: str, tp: int, fp: int, fn: int) -> None:
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        print(f"{label:<14}{prec:>10.2f}{rec:>9.2f}{tp:>5}{fp:>5}{fn:>5}")

    print("\n=== Eksen bazlı ===")
    print(f"{'eksen':<14}{'precision':>10}{'recall':>9}{'TP':>5}{'FP':>5}{'FN':>5}")
    for ax in AXES:
        _line(ax, total_tp[ax], total_fp[ax], total_fn[ax])

    # ÇEKİRDEK skoru (imla + dil bilgisi + tutarlılık) — ton hariç. Ton öznel/
    # gürültülü olduğundan ayrı raporlanır; çekirdek precision'ı maskelememesi
    # için toplama katılmaz (bkz. CORE_AXES yorumu).
    c_tp = sum(total_tp[ax] for ax in CORE_AXES)
    c_fp = sum(total_fp[ax] for ax in CORE_AXES)
    c_fn = sum(total_fn[ax] for ax in CORE_AXES)
    print("-" * 43)
    _line("ÇEKİRDEK", c_tp, c_fp, c_fn)  # GENEL yerine: ton'suz çekirdek
    _line("(ton ayrı)", total_tp["ton"], total_fp["ton"], total_fn["ton"])

    print(f"\nTEMİZ metinlerde yanlış pozitif — çekirdek: {clean_fp}  |  ton: {clean_fp_tone}")


if __name__ == "__main__":
    main()
