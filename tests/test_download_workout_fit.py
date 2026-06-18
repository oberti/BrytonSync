# test_download_workout_fit.py
from dotenv import load_dotenv
from pathlib import Path
import os
import sys
import requests

sys.path.insert(0, r"C:\BrytonSync_v2\core")

from brytonsync.bryton_client import BrytonClient
from brytonsync.bryton_workout_client import BrytonWorkoutClient

load_dotenv()

bryton = BrytonClient()
user_id, auth_token = bryton.login(
    os.environ["BRYTON_EMAIL"],
    os.environ["BRYTON_PASSWORD"],
)

client = BrytonWorkoutClient(user_id=user_id, auth_token=auth_token)
data = client.list_workouts()

for workout in data.get("workout", []):
    if workout.get("name") == "HIIT 30/15":
        url = workout["url"]
        out = Path("planned_workouts") / "HIIT_30_15_original.fit"
        r = requests.get(url, headers=bryton.auth_headers, timeout=30)
        r.raise_for_status()
        out.write_bytes(r.content)
        print("Scaricato:", out)
        print("Dimensione:", out.stat().st_size)
        break