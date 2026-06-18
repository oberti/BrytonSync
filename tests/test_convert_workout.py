from datetime import date, timedelta
from dotenv import load_dotenv
import json
import os
import sys

sys.path.insert(0, r"C:\BrytonSync_v2\core")

from brytonsync.intervals_client import IntervalsClient
from brytonsync.workout_converter import intervals_event_to_bryton_info

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
    if "FTP" in str(event.get("name", "")):
        info = intervals_event_to_bryton_info(event)
        print(json.dumps(info, indent=2, ensure_ascii=False))
        break