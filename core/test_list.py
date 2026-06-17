from brytonsync.bryton_client import BrytonClient
from brytonsync.config import load_config

cfg = load_config()
client = BrytonClient()
client.login(cfg.bryton_email, cfg.bryton_password)
activities = client.list_activities(since=cfg.since, limit=cfg.max_activities)
print("ATTIVITÀ:", len(activities))
for a in activities:
    print(a)
