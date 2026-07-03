"""Elle deneme girişi.

Kullanım:
    python cli.py "Bu cümlede ki hata var ve yanlız yazılmış."
    echo "uzun metin..." | python cli.py
    python cli.py belge.docx        # .docx → çıkar + parçala + analiz et
"""

from __future__ import annotations

import json
import sys

from dilanaliz.analyzer import LLMCallError, build_default_analyzer


def _read_input(argv: list[str]) -> tuple[str, list | None]:
    """(metin, blok-span'leri) döner; span'ler yalnız .docx girdisinde vardır."""
    if len(argv) > 1:
        arg = argv[1]
        if arg.lower().endswith(".docx"):
            from dilanaliz.extract import extract_docx_blocks

            text, spans, report = extract_docx_blocks(arg)
            # Kapsam özeti + okunamayan içerik uyarıları stderr'e (stdout JSON saf kalsın).
            print(f"  … {report.describe()}", file=sys.stderr)
            for warning in report.warnings:
                print(f"  ⚠ {warning}", file=sys.stderr)
            return text, spans
        return " ".join(argv[1:]), None
    data = sys.stdin.read()
    if not data.strip():
        print("Hata: analiz edilecek metin verilmedi.", file=sys.stderr)
        raise SystemExit(2)
    return data, None


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
    text, spans = _read_input(sys.argv)
    analyzer = build_default_analyzer()
    # Uzun belgeleri parçalayarak analiz eder; kısa metinde tek parça olur,
    # davranış `analyze` ile aynıdır. İlerleme stderr'e akar (terminalde görünür),
    # JSON sonucu stdout'a yazılır. .docx girdisinde blok türü haritası (spans)
    # tablo/başlık kaynaklı yapay bulguları süzer.
    try:
        result = analyzer.analyze_document(text, progress=_stderr_progress, spans=spans)
    except LLMCallError as exc:
        print(f"Hata: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
