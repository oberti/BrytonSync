from brytonsync.bryton_client import BrytonClient
from brytonsync.config import load_config

cfg = load_config()
client = BrytonClient()
user_id, token = client.login(cfg.bryton_email, cfg.bryton_password)
print("LOGIN OK")
print("userId:", user_id)
print("authToken prefix:", token[:8] + "...")
