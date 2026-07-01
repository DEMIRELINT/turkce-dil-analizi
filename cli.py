"""Elle deneme girişi.

Kullanım:
    python cli.py "Bu cümlede ki hata var ve yanlız yazılmış."
    echo "uzun metin..." | python cli.py
    python cli.py belge.docx        # .docx → çıkar + parçala + analiz et
"""

from __future__ import annotations

import json
import sys

from dilanaliz.analyzer import Analyzer, build_default_analyzer


def _read_input(argv: list[str], analyzer: Analyzer) -> str:
    if len(argv) > 1:
        arg = argv[1]
        if arg.lower().endswith(".docx"):
            from dilanaliz.extract import extract_docx_with_report

            text, report = extract_docx_with_report(arg, speller=analyzer.speller)
            # Kapsam özeti + okunamayan içerik uyarıları stderr'e (stdout JSON saf kalsın).
            print(f"  … {report.describe()}", file=sys.stderr)
            for warning in report.warnings:
                print(f"  ⚠ {warning}", file=sys.stderr)
            return text
        return " ".join(argv[1:])
    data = sys.stdin.read()
    if not data.strip():
        print("Hata: analiz edilecek metin verilmedi.", file=sys.stderr)
        raise SystemExit(2)
    return data


def _stderr_progress(event) -> None:
    """Analiz adımlarını stderr'e basar; stdout'taki JSON saf kalır (boru hattı bozulmaz).

    Uzun belgede her parça "başladı/bitti" iki olay yayar; CLI'da gürültüyü
    azaltmak için yalnız "bitti" + kilometre taşlarını basıyoruz (başlama olayını
    atlıyoruz). Web paneli iki olayı da kullanır (canlı paralellik görünümü).
    """
    if event.stage == "chunk_start":
        return
    print(f"  … {event.message}", file=sys.stderr)


def main() -> None:
    analyzer = build_default_analyzer()
    text = _read_input(sys.argv, analyzer)
    # Uzun belgeleri parçalayarak analiz eder; kısa metinde tek parça olur,
    # davranış `analyze` ile aynıdır. İlerleme stderr'e akar (terminalde görünür),
    # JSON sonucu stdout'a yazılır.
    result = analyzer.analyze_document(text, progress=_stderr_progress)
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
