"""Paralellik ÖNCESİ (sıralı) vs SONRASI (paralel): süre ve çıktı karşılaştırması.

İki fazda çalışır, çünkü iki soru ayrıdır:

  FAZ 1 — HIZ (önbellek KAPALI): Aynı belgeyi CONCURRENCY=1 ve CONCURRENCY=N ile
    gerçekten analiz eder; wall-clock süre + hızlanma katsayısını verir.

  FAZ 2 — EŞDEĞERLİK (önbellek PAYLAŞIMLI): Sıralı koşu önbelleği doldurur,
    paralel koşu AYNI model yanıtlarını okur. Böylece modelin çağrı-çağrı
    değişkenliği elenir ve YALNIZ orkestrasyonun (sıralı vs paralel) çıktıya
    etkisi ölçülür → birebir aynı olmalı.

NEDEN iki faz? LLM'ler (Gemini dahil) temperature=0 olsa bile aynı isteme
çağrıdan çağrıya birebir aynı yanıtı vermez. Bu yüzden iki AYRI canlı koşunun
çıktısı doğal olarak biraz farklı çıkabilir — bu paralellikten DEĞİL, modelin
kendisindendir. Paralelliğin çıktıyı değiştirmediğini görmek için aynı yanıtları
(önbellek) iki yola da vermek gerekir.

Kullanım (GEMINI_API_KEY gerekli):
    python eval/compare_parallel.py "kısa metin..."
    python eval/compare_parallel.py belge.docx
    echo "uzun metin" | python eval/compare_parallel.py
    CONCURRENCY=8 python eval/compare_parallel.py belge.docx   # paralel kademe

UYARI — MALİYET: Belge 3 kez analiz edilir (hız: sıralı+paralel; eşdeğerlik:
sıralı). KÜÇÜK bir belgeyle çalıştırın.
"""

from __future__ import annotations

import sys
import tempfile
import time
from dataclasses import replace
from pathlib import Path

from dilanaliz.analyzer import Analyzer
from dilanaliz.cache import DiskCache
from dilanaliz.config import Settings
from dilanaliz.providers import build_chat_model
from dilanaliz.rules import StaticRulesProvider
from dilanaliz.schema import AnalysisResult
from dilanaliz.spell import HunspellChecker


def _read_input(argv: list[str]) -> str:
    if len(argv) > 1:
        arg = argv[1]
        if arg.lower().endswith(".docx"):
            from dilanaliz.extract import extract_docx_with_report

            text, report = extract_docx_with_report(arg)
            print(f"  … {report.describe()}", file=sys.stderr)
            return text
        return " ".join(argv[1:])
    data = sys.stdin.read()
    if not data.strip():
        print("Hata: analiz edilecek metin verilmedi.", file=sys.stderr)
        raise SystemExit(2)
    return data


def _make(settings: Settings, max_workers: int, cache: DiskCache | None) -> Analyzer:
    speller = None
    if settings.dict_path and Path(f"{settings.dict_path}.dic").exists():
        speller = HunspellChecker(settings.dict_path)
    return Analyzer(
        chat_model=build_chat_model(settings),
        rules_provider=StaticRulesProvider(),
        model_id=settings.model_id,
        cache=cache,
        speller=speller,
        max_workers=max_workers,
    )


def _timed(analyzer: Analyzer, text: str) -> tuple[AnalysisResult, float]:
    t0 = time.perf_counter()
    result = analyzer.analyze_document(text)
    return result, time.perf_counter() - t0


def _view(result: AnalysisResult) -> dict:
    # Hem bulgular hem gözlemler (ayrı kanal) sıralı/paralel arasında birebir
    # aynı olmalı — determinizm sözleşmesi ikisini de kapsar.
    return {
        "findings": [f.model_dump() for f in result.findings],
        "observations": [o.model_dump() for o in result.observations],
    }


def main() -> None:
    text = _read_input(sys.argv)
    base = Settings.from_env()
    n = base.max_workers if base.max_workers > 1 else 6
    if base.max_workers <= 1:
        print("  … CONCURRENCY=1; paralel kademe 6 alındı (CONCURRENCY ile değiştirin).",
              file=sys.stderr)

    print(f"Model: {base.model_id} | belge: {len(text)} karakter", file=sys.stderr)
    print("UYARI: belge 3× analiz edilecek (hız: sıralı+paralel, eşdeğerlik: sıralı).\n",
          file=sys.stderr)

    # --- FAZ 1: HIZ (önbellek kapalı, gerçek çağrılar) ----------------------
    print("FAZ 1 — Hız ölçümü (önbellek kapalı)…", file=sys.stderr)
    print("  Sıralı (1) çalışıyor…", file=sys.stderr)
    seq_result, seq_time = _timed(_make(replace(base, max_workers=1), 1, None), text)
    print(f"  Paralel ({n}) çalışıyor…", file=sys.stderr)
    par_result, par_time = _timed(_make(replace(base, max_workers=n), n, None), text)
    speedup = (seq_time / par_time) if par_time > 0 else float("inf")

    # --- FAZ 2: EŞDEĞERLİK (paylaşımlı önbellek = aynı model yanıtları) ------
    print("FAZ 2 — Eşdeğerlik (paylaşımlı önbellek; modelin oynaklığı elenir)…",
          file=sys.stderr)
    shared = DiskCache(Path(tempfile.mkdtemp()) / "shared.json")
    eq_seq = _make(base, 1, shared).analyze_document(text)  # önbelleği doldurur
    eq_par = _make(base, n, shared).analyze_document(text)  # aynı yanıtları okur
    identical = _view(eq_seq) == _view(eq_par)

    # --- Özet ----------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  HIZ (önbellek kapalı, gerçek çağrılar):")
    print(f"    Seri    (1) : {seq_time:6.2f} s   | {len(seq_result.findings)} bulgu")
    print(f"    Paralel ({n}) : {par_time:6.2f} s   | {len(par_result.findings)} bulgu")
    print(f"    Hızlanma    : {speedup:5.2f}x")
    print("  EŞDEĞERLİK (aynı model yanıtlarıyla, sıralı vs paralel):")
    print(f"    Çıktı birebir aynı mı? : {'AYNI ✓' if identical else 'FARKLI ✗'}")
    print("=" * 60)
    print("  Not: Faz 1'de bulgu sayıları farklı olabilir — bu PARALELLİKTEN değil,")
    print("  modelin (temperature=0 olsa da) çağrı-çağrı doğal oynaklığındandır.")
    print("  Paralelliğin çıktıyı değiştirmediğini Faz 2 (AYNI ✓) kanıtlar.")

    if not identical:
        # Bu gerçek bir sorun olurdu (orkestrasyon determinizmi bozulmuş).
        print("\n! UYARI: Aynı yanıtlarla bile çıktı farklı — orkestrasyon "
              "determinizmi bozulmuş olabilir.", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
