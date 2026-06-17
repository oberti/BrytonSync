from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import load_config
from .sync import sync


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bryton Active -> FIT -> intervals.icu")
    parser.add_argument("--env", default=".env", help="Percorso file .env")
    parser.add_argument("--json", action="store_true", help="Stampa risultato JSON finale")
    args = parser.parse_args(argv)

    try:
        config = load_config(args.env)
        results = sync(config)
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"ERRORE: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
