from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


ACTIVITY_TYPE_KEEP = ""
DEFAULT_DOWNLOAD_DIR = Path("downloads")
DEFAULT_DROPBOX_FOLDER = "/BrytonSync"

# Dropbox OAuth PKCE
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

    # Dropbox legacy
    dropbox_access_token: str | None = None

    # Dropbox OAuth PKCE
    dropbox_app_key: str = DEFAULT_DROPBOX_APP_KEY
    dropbox_refresh_token: str | None = None

    dropbox_folder: str = DEFAULT_DROPBOX_FOLDER

    sync_planned_workouts: bool = False
    planned_days_ahead: int = 14


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in (
        "1",
        "true",
        "yes",
        "y",
        "on",
    )


def load_config(env_file: str | Path | None = ".env") -> SyncConfig:
    if load_dotenv is not None and env_file:
        load_dotenv(env_file)

    email = os.getenv("BRYTON_EMAIL", "").strip()
    password = os.getenv("BRYTON_PASSWORD", "").strip()

    if not email or not password:
        raise ValueError("Imposta BRYTON_EMAIL e BRYTON_PASSWORD nel file .env")

    return SyncConfig(
        bryton_email=email,
        bryton_password=password,

        intervals_api_key=os.getenv("INTERVALS_API_KEY") or None,
        intervals_athlete_id=os.getenv(
            "INTERVALS_ATHLETE_ID",
            "999999",
        ).strip().lstrip("i"),

        max_activities=int(os.getenv("MAX_ACTIVITIES", "10")),
        since=int(os.getenv("BRYTON_SINCE", "0")),
        download_dir=Path(
            os.getenv("DOWNLOAD_DIR", str(DEFAULT_DOWNLOAD_DIR))
        ),

        delete_after_upload=env_bool(
            "DELETE_AFTER_UPLOAD",
            False,
        ),
        force_resync=env_bool(
            "FORCE_RESYNC",
            False,
        ),
        activity_type=os.getenv(
            "ACTIVITY_TYPE",
            ACTIVITY_TYPE_KEEP,
        ),

        list_activities=env_bool(
            "LIST_ACTIVITIES",
            True,
        ),
        get_download_url=env_bool(
            "GET_DOWNLOAD_URL",
            True,
        ),
        download_fit=env_bool(
            "DOWNLOAD_FIT",
            True,
        ),
        upload_intervals=env_bool(
            "UPLOAD_INTERVALS",
            False,
        ),

        upload_dropbox=env_bool(
            "UPLOAD_DROPBOX",
            False,
        ),

        dropbox_access_token=os.getenv(
            "DROPBOX_ACCESS_TOKEN"
        ) or None,

        dropbox_app_key=os.getenv(
            "DROPBOX_APP_KEY",
            DEFAULT_DROPBOX_APP_KEY,
        ),

        dropbox_refresh_token=os.getenv(
            "DROPBOX_REFRESH_TOKEN"
        ) or None,

        dropbox_folder=os.getenv(
            "DROPBOX_FOLDER",
            DEFAULT_DROPBOX_FOLDER,
        ).strip() or DEFAULT_DROPBOX_FOLDER,

        sync_planned_workouts=env_bool(
            "SYNC_PLANNED_WORKOUTS",
            False,
        ),

        planned_days_ahead=int(
            os.getenv("PLANNED_DAYS_AHEAD", "14")
        ),
    )