from dotenv import load_dotenv
import os
import sys
import json

sys.path.insert(0, r"C:\BrytonSync_v2\core")

from brytonsync.bryton_client import BrytonClient
from brytonsync.bryton_workout_client import BrytonWorkoutClient

load_dotenv()

bryton = BrytonClient()

user_id, auth_token = bryton.login(
    os.environ["BRYTON_EMAIL"],
    os.environ["BRYTON_PASSWORD"],
)

print("=== LOGIN OK ===")
print("User ID:", user_id)

client = BrytonWorkoutClient(
    user_id=user_id,
    auth_token=auth_token,
)

data = client.list_workouts()

print("\n=== TIPO RISPOSTA ===")
print(type(data))

if isinstance(data, dict):

    print("\n=== CHIAVI ===")
    for k in data.keys():
        print(k)

    print("\n=== CONTEGGI ===")
    for k, v in data.items():
        if isinstance(v, list):
            print(f"{k}: {len(v)} elementi")

    if "workout" in data:
        print("\n=== WORKOUT ===")
        print(json.dumps(data["workout"], indent=2, ensure_ascii=False))

else:
    print(data)