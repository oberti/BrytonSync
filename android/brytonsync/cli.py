from __future__ import annotations

import argparse
import json
import sys

from .config import load_config
from .planned_workout_sync import sync_planned_workouts
from .sync import sync


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="BrytonSync")
    parser.add_argument(
        "command",
        choices=["activities", "workouts", "all"],
        nargs="?",
        default="activities",
        help="activities = sync uscite, workouts = sync workout pianificati, all = entrambi",
    )
    parser.add_argument("--env", default=".env", help="Percorso file .env")
    parser.add_argument("--json", action="store_true", help="Stampa risultato JSON finale")
    parser.add_argument("--days", type=int, default=None, help="Giorni futuri workout da sincronizzare")

    args = parser.parse_args(argv)

    try:
        config = load_config(args.env)
        results: dict[str, object] = {}

        if args.command in ("activities", "all"):
            results["activities"] = sync(config)

        if args.command in ("workouts", "all"):
            if not config.intervals_api_key:
                raise ValueError("INTERVALS_API_KEY non impostata")

            days = args.days if args.days is not None else config.planned_days_ahead

            results["workouts"] = sync_planned_workouts(
                bryton_email=config.bryton_email,
                bryton_password=config.bryton_password,
                intervals_api_key=config.intervals_api_key,
                intervals_athlete_id="0",
                days_ahead=days,
                dry_run=False,
            )

        print(json.dumps(results, indent=2, ensure_ascii=False))
        return 0

    except Exception as exc:  # noqa: BLE001
        print(f"ERRORE: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())