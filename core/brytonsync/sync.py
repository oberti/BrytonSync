from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .bryton_client import BrytonClient
from .config import SyncConfig
from .dropbox_client import DropboxClient
from .intervals_client import IntervalsClient


def make_json_safe(value: Any) -> Any:
    if isinstance(value, bytes):
        return f"<bytes {len(value)}>"
    if isinstance(value, dict):
        return {k: make_json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [make_json_safe(v) for v in value]
    return value


def fit_filename_from_activity(activity: dict[str, Any], fallback_id: str) -> str:
    start_time = activity.get("start_time")

    if start_time:
        return datetime.fromtimestamp(
            int(start_time)
        ).strftime("%y%m%d%H%M%S.fit")

    return f"{fallback_id}.fit"


def sync(config: SyncConfig) -> list[dict[str, Any]]:
    bryton = BrytonClient()
    user_id, _token = bryton.login(config.bryton_email, config.bryton_password)
    print(f"Login Bryton OK: userId={user_id}")

    intervals = None
    if config.upload_intervals:
        if not config.intervals_api_key:
            raise ValueError("UPLOAD_INTERVALS=true ma INTERVALS_API_KEY non impostata")
        intervals = IntervalsClient(config.intervals_api_key, config.intervals_athlete_id)

    dropbox_client = None
    if config.upload_dropbox:
        if not config.dropbox_access_token:
            raise ValueError("UPLOAD_DROPBOX=true ma DROPBOX_ACCESS_TOKEN non impostato")
        dropbox_client = DropboxClient(config.dropbox_access_token, config.dropbox_folder)

    activities = bryton.list_activities(since=config.since, limit=config.max_activities)
    print(f"Attività trovate: {len(activities)}")

    results: list[dict[str, Any]] = []

    for activity in activities:
        activity_id = bryton.activity_id(activity)
        external_id = f"bryton_{activity_id}"

        row: dict[str, Any] = {
            "activity_id": activity_id,
            "external_id": external_id,
            "status": "listed",
        }

        if config.list_activities:
            print(f"- {activity_id}: {activity}")

        if intervals and not config.force_resync and intervals.exists_external_id(external_id):
            print(f"  skip: già presente su intervals.icu ({external_id})")
            row["status"] = "skipped_exists"
            results.append(row)
            continue

        if not config.get_download_url:
            results.append(row)
            continue

        detail = bryton.get_activity_detail(activity_id)
        fit_url = bryton.find_fit_url(detail)

        row["detail"] = make_json_safe(detail)
        row["fit_url"] = fit_url

        if not fit_url:
            print(f"  nessun URL FIT trovato per {activity_id}")
            row["status"] = "no_fit_url"
            results.append(row)
            continue

        print(f"  FIT URL: {fit_url}")

        if not config.download_fit:
            row["status"] = "fit_url_found"
            results.append(row)
            continue

        fit_filename = fit_filename_from_activity(activity, activity_id)
        fit_path: Path = config.download_dir / fit_filename

        bryton.download_fit(fit_url, fit_path, detail=detail)

        print(f"  scaricato: {fit_path}")

        row["fit_path"] = str(fit_path)
        row["fit_filename"] = fit_filename
        row["status"] = "downloaded"

        if dropbox_client:
            dropbox_path = dropbox_client.upload_file(fit_path)
            print(f"  caricato su Dropbox: {dropbox_path}")
            row["dropbox_path"] = dropbox_path
            row["status"] = "uploaded_dropbox"

        if intervals:
            uploaded = intervals.upload_fit(
                fit_path,
                external_id=external_id,
                activity_type=config.activity_type,
            )
            print(f"  caricato su intervals.icu: {external_id}")

            row["intervals_response"] = make_json_safe(uploaded)

            if row["status"] == "uploaded_dropbox":
                row["status"] = "uploaded_dropbox_intervals"
            else:
                row["status"] = "uploaded_intervals"

        if config.delete_after_upload and (intervals or dropbox_client):
            fit_path.unlink(missing_ok=True)
            row["deleted_after_upload"] = True

        results.append(row)

    return results