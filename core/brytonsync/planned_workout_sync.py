from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from .bryton_client import BrytonClient
from .bryton_workout_client import BrytonWorkoutClient
from .intervals_client import IntervalsClient
from .workout_converter import intervals_event_to_bryton_info
from .workout_fit_builder import build_minimal_workout_fit


def _existing_bryton_workout_orgids(data: Any) -> set[str]:
    if not isinstance(data, dict):
        return set()

    workout_list = data.get("workout")
    if not isinstance(workout_list, list):
        return set()

    orgids: set[str] = set()

    for workout in workout_list:
        if isinstance(workout, dict) and workout.get("orgid"):
            orgids.add(str(workout["orgid"]))

    return orgids


def sync_planned_workouts(
    bryton_email: str,
    bryton_password: str,
    intervals_api_key: str,
    intervals_athlete_id: str = "0",
    days_ahead: int = 14,
    output_dir: Path = Path("planned_workouts"),
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    intervals = IntervalsClient(
        api_key=intervals_api_key,
        athlete_id=intervals_athlete_id,
    )

    oldest = date.today().isoformat()
    newest = (date.today() + timedelta(days=days_ahead)).isoformat()

    events = intervals.list_events(
        oldest=oldest,
        newest=newest,
        resolve=True,
    )

    bryton = BrytonClient()
    user_id, auth_token = bryton.login(
        bryton_email,
        bryton_password,
    )

    bryton_workouts = BrytonWorkoutClient(
        user_id=user_id,
        auth_token=auth_token,
    )

    existing = bryton_workouts.list_workouts()
    existing_orgids = _existing_bryton_workout_orgids(existing)

    results: list[dict[str, Any]] = []

    for event in events:
        event_id = str(event.get("id") or "")

        if not event_id:
            continue

        if event.get("category") != "WORKOUT":
            results.append(
                {
                    "event_id": event_id,
                    "name": event.get("name"),
                    "status": "skipped",
                    "reason": "not_workout",
                }
            )
            continue

        if not event.get("workout_doc"):
            results.append(
                {
                    "event_id": event_id,
                    "name": event.get("name"),
                    "status": "skipped",
                    "reason": "missing_workout_doc",
                }
            )
            continue

        if event_id in existing_orgids:
            results.append(
                {
                    "event_id": event_id,
                    "name": event.get("name"),
                    "status": "skipped",
                    "reason": "already_uploaded",
                }
            )
            continue

        info = intervals_event_to_bryton_info(event)

        fit_path = build_minimal_workout_fit(
            info,
            output_dir / f"{event_id}.fit",
        )

        if dry_run:
            results.append(
                {
                    "event_id": event_id,
                    "name": info["name"],
                    "status": "dry_run",
                    "fit_path": str(fit_path),
                }
            )
            continue

        upload_result = bryton_workouts.upload_workout_fit(
            fit_path=fit_path,
            name=info["name"],
            provider="bryton",
            org_id=event_id,
            info_json=json.dumps(info, ensure_ascii=False),
        )

        results.append(
            {
                "event_id": event_id,
                "name": info["name"],
                "status": "uploaded",
                "fit_path": str(fit_path),
                "bryton_result": upload_result,
            }
        )

    return results