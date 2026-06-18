from datetime import date, timedelta
from dotenv import load_dotenv
import os
import sys
import json

sys.path.insert(0, r"C:\BrytonSync_v2\core")

from brytonsync.intervals_client import IntervalsClient

load_dotenv()

client = IntervalsClient(
    api_key=os.environ["INTERVALS_API_KEY"],
    athlete_id="0",
)

events = client.list_events(
    oldest=date.today().isoformat(),
    newest=(date.today() + timedelta(days=60)).isoformat(),
    resolve=True,
)

print(f"Eventi trovati: {len(events)}")

found = False

for e in events:
    if e.get("category") != "WORKOUT":
        continue

    workout_doc = e.get("workout_doc") or {}
    target = str(workout_doc.get("target", "")).upper()
    raw = json.dumps(workout_doc, ensure_ascii=False).lower()

    is_hr_workout = (
        target in ("HR", "HEARTRATE", "HEART_RATE")
        or '"_hr"' in raw
        or '"hr"' in raw
        or '"heart_rate"' in raw
    )

    if is_hr_workout:
        print(json.dumps(e, indent=2, ensure_ascii=False))
        found = True
        break

if not found:
    print("Nessun workout FC/HR trovato nei prossimi 60 giorni.")
    print("Workout disponibili:")

    for e in events:
        if e.get("category") == "WORKOUT":
            workout_doc = e.get("workout_doc") or {}
            print(
                "-",
                e.get("id"),
                e.get("start_date_local"),
                e.get("name"),
                "target=" + str(workout_doc.get("target")),
            )