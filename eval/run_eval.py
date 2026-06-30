"""Altın set üzerinde eksen-bazlı precision/recall ölçümü.

Çalıştırma (GEMINI_API_KEY gerekli):
    python eval/run_eval.py

Eşleştirme: bir tahmin, aynı eksende (type) ve alıntısı beklenen alıntıyla
örtüşen (biri diğerini içeren, büyük/küçük harf duyarsız) bir beklenen bulguya
denk geliyorsa Doğru Pozitif (TP) sayılır. Artan tahminler FP, eşleşmeyen
beklenenler FN'dir. TEMİZ metinlerdeki tüm tahminler FP'dir (yanlış pozitif).
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
    clean_fp = 0

    # Gemini ücretsiz katman dakikada 5 istekle sınırlı. Çağrılar arasına bekleme
    # koyarak 429'u önleriz. Ücretli katmanda EVAL_DELAY_SEC=0 ile kapatılabilir.
    delay = float(os.getenv("EVAL_DELAY_SEC", "13"))

    examples = [json.loads(line) for line in GOLDEN.read_text(encoding="utf-8").splitlines() if line.strip()]
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
            clean_fp += len(result.findings)
        dump.append(
            {
                "id": ex["id"],
                "text": ex["text"],
                "expected": ex["expected"],
                "predicted": [
                    {"type": f.type.value, "excerpt": f.excerpt, "suggestion": f.suggestion}
                    for f in result.findings
                ],
            }
        )
        processed += 1
        print(f"- {ex['id']}: bulgu={len(result.findings)} beklenen={len(ex['expected'])}")

    # Hata olsa bile eldeki tahminleri kalibrasyon için diske yaz.
    DUMP.write_text(json.dumps(dump, ensure_ascii=False, indent=2), encoding="utf-8")
    if aborted:
        print(f"\n[Kısmi çalışma] {processed}/{len(examples)} örnek işlendi. "
              f"Sonuçlar {DUMP.name}'a yazıldı; kalanlar önbellekten devam edecek.")

    print("\n=== Eksen bazlı ===")
    print(f"{'eksen':<14}{'precision':>10}{'recall':>9}{'TP':>5}{'FP':>5}{'FN':>5}")
    for ax in AXES:
        tp, fp, fn = total_tp[ax], total_fp[ax], total_fn[ax]
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        print(f"{ax:<14}{prec:>10.2f}{rec:>9.2f}{tp:>5}{fp:>5}{fn:>5}")

    g_tp = sum(total_tp.values())
    g_fp = sum(total_fp.values())
    g_fn = sum(total_fn.values())
    g_prec = g_tp / (g_tp + g_fp) if (g_tp + g_fp) else 0.0
    g_rec = g_tp / (g_tp + g_fn) if (g_tp + g_fn) else 0.0
    print(f"{'GENEL':<14}{g_prec:>10.2f}{g_rec:>9.2f}{g_tp:>5}{g_fp:>5}{g_fn:>5}")
    print(f"\nTEMİZ metinlerde yanlış pozitif sayısı: {clean_fp}")


if __name__ == "__main__":
    main()
