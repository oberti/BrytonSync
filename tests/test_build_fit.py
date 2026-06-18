from datetime import date, timedelta
from dotenv import load_dotenv
from pathlib import Path
import os
import sys

sys.path.insert(0, r"C:\BrytonSync_v2\core")

from brytonsync.intervals_client import IntervalsClient
from brytonsync.workout_converter import intervals_event_to_bryton_info
from brytonsync.workout_fit_builder import build_minimal_workout_fit

load_dotenv()

client = IntervalsClient(
    api_key=os.environ["INTERVALS_API_KEY"],
    athlete_id="0",
)

events = client.list_events(
    oldest=date.today().isoformat(),
    newest=(date.today() + timedelta(days=14)).isoformat(),
    resolve=True,
)

for event in events:
    if "Fartlek" in str(event.get("name", "")):
        info = intervals_event_to_bryton_info(event)
        fit_path = build_minimal_workout_fit(
            info,
            Path("planned_workouts") / f"{event['id']}.fit",
        )
        print("FIT creato:", fit_path)
        print("JSON debug:", fit_path.with_suffix(".json"))
        print("Dimensione FIT:", fit_path.stat().st_size, "bytes")
        break