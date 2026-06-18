from dotenv import load_dotenv
import json
import os
import sys

sys.path.insert(0, r"C:\BrytonSync_v2\core")

from brytonsync.planned_workout_sync import sync_planned_workouts

load_dotenv()

results = sync_planned_workouts(
    bryton_email=os.environ["BRYTON_EMAIL"],
    bryton_password=os.environ["BRYTON_PASSWORD"],
    intervals_api_key=os.environ["INTERVALS_API_KEY"],
    intervals_athlete_id="0",
    days_ahead=14,
    dry_run=False,
)

print(json.dumps(results, indent=2, ensure_ascii=False))