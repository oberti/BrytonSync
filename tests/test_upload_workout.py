from dotenv import load_dotenv
from pathlib import Path
import json
import os
import sys

sys.path.insert(0, r"C:\BrytonSync_v2\core")

from brytonsync.bryton_client import BrytonClient
from brytonsync.bryton_workout_client import BrytonWorkoutClient

load_dotenv()

fit_path = Path("planned_workouts") / "116712038.fit"
json_path = fit_path.with_suffix(".json")

info = json.loads(json_path.read_text(encoding="utf-8"))

bryton = BrytonClient()
user_id, auth_token = bryton.login(
    os.environ["BRYTON_EMAIL"],
    os.environ["BRYTON_PASSWORD"],
)

client = BrytonWorkoutClient(
    user_id=user_id,
    auth_token=auth_token,
)

result = client.upload_workout_fit(
    fit_path=fit_path,
    name=info["name"] + " TEST",
    provider="bryton",
    org_id=info["intervals_event_id"],
    info_json=json.dumps(info, ensure_ascii=False),
)

print("Upload risultato:")
print(json.dumps(result, indent=2, ensure_ascii=False))