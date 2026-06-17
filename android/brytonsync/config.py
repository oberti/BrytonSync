from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ACTIVITY_TYPE_KEEP = ""
DEFAULT_DOWNLOAD_DIR = Path("downloads")
DEFAULT_DROPBOX_FOLDER = "/BrytonSync"
# App key pubblica usata dal flusso OAuth PKCE in stile igpsport-intervals.
# Non è un segreto: il segreto non serve con PKCE.
DEFAULT_DROPBOX_APP_KEY = "4e9vei57q5t2jnw"


@dataclass(slots=True)
class SyncConfig:
    bryton_email: str
    bryton_password: str
    intervals_api_key: str | None = None
    intervals_athlete_id: str = "999999"
    max_activities: int = 10
    since: int = 0
    download_dir: Path = DEFAULT_DOWNLOAD_DIR
    delete_after_upload: bool = False
    force_resync: bool = False
    activity_type: str = ACTIVITY_TYPE_KEEP
    list_activities: bool = True
    get_download_url: bool = True
    download_fit: bool = True
    upload_intervals: bool = False
    upload_dropbox: bool = False
    dropbox_access_token: str | None = None
    dropbox_app_key: str = DEFAULT_DROPBOX_APP_KEY
    dropbox_refresh_token: str | None = None
    dropbox_folder: str = DEFAULT_DROPBOX_FOLDER
