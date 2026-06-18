from __future__ import annotations

import time
from typing import Any


def _range_from(step: dict[str, Any], key: str) -> tuple[int | None, int | None]:
    data = step.get(key) or {}

    start = data.get("start")
    end = data.get("end")

    if start is None and data.get("value") is not None:
        start = data.get("value")
    if end is None and data.get("value") is not None:
        end = data.get("value")

    if start is None or end is None:
        return None, None

    return int(round(float(start))), int(round(float(end)))


def _simple_step_to_bryton(step: dict[str, Any]) -> dict[str, Any]:
    duration = int(step.get("duration") or 0)

    item: dict[str, Any] = {
        "duration_type": "time",
        "duration_value": duration,
    }

    if step.get("_power"):
        low, high = _range_from(step, "_power")
        item["target_type"] = "power"
    elif step.get("_hr"):
        low, high = _range_from(step, "_hr")
        item["target_type"] = "heart_rate"
    else:
        low, high = None, None
        item["target_type"] = ""

    if low is not None and high is not None:
        item["target_low"] = low
        item["target_high"] = high

    return item


def intervals_event_to_bryton_info(event: dict[str, Any]) -> dict[str, Any]:
    workout_doc = event.get("workout_doc") or {}
    steps = workout_doc.get("steps") or []

    bryton_intervals: list[dict[str, Any]] = []

    for step in steps:
        nested_steps = step.get("steps")
        reps = int(step.get("reps") or 0)

        if nested_steps and reps > 1:
            start_index = len(bryton_intervals)

            for child in nested_steps:
                bryton_intervals.append(_simple_step_to_bryton(child))

            bryton_intervals.append(
                {
                    "duration_type": "repeat_until_steps_cmplt",
                    "duration_step": start_index,
                    "repeat_steps": reps,
                }
            )
        else:
            bryton_intervals.append(_simple_step_to_bryton(step))

    return {
        "name": event.get("name") or "Intervals Workout",
        "description": event.get("description") or "",
        "provider": "bryton",
        "interval": bryton_intervals,
        "create_time": int(time.time() * 1000),
        "TSS": event.get("icu_training_load"),
        "IF": event.get("icu_intensity"),
        "plan": [],
        "ver": 5,
        "source": "intervals.icu",
        "intervals_event_id": str(event.get("id")),
        "intervals_uid": event.get("uid"),
        "ftp": workout_doc.get("ftp"),
        "lthr": workout_doc.get("lthr"),
        "target": workout_doc.get("target"),
    }