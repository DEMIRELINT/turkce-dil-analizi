"""Elle deneme girişi.

Kullanım:
    python cli.py "Bu cümlede ki hata var ve yanlız yazılmış."
    echo "uzun metin..." | python cli.py
"""

from __future__ import annotations

import json
import sys

from dilanaliz.analyzer import build_default_analyzer


def _read_input(argv: list[str]) -> str:
    if len(argv) > 1:
        return " ".join(argv[1:])
    data = sys.stdin.read()
    if not data.strip():
        print("Hata: analiz edilecek metin verilmedi.", file=sys.stderr)
        raise SystemExit(2)
    return data


def main() -> None:
    text = _read_input(sys.argv)
    analyzer = build_default_analyzer()
    result = analyzer.analyze(text)
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
