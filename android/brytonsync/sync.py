from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from .bryton_client import BrytonClient
from .config import SyncConfig
from .dropbox_client import DropboxClient
from .intervals_client import IntervalsClient

LogFn = Callable[[str], None]


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
        return datetime.fromtimestamp(int(start_time)).strftime("%y%m%d%H%M%S.fit")
    return f"{fallback_id}.fit"


def is_deleted_activity(activity: Any) -> bool:
    if activity is None:
        return True
    if isinstance(activity, str):
        return activity.strip().lower() == "_deleted"
    if not isinstance(activity, dict):
        return True
    if activity.get("_deleted") is True:
        return True
    if activity.get("deleted") is True:
        return True
    if str(activity.get("status", "")).lower() == "_deleted":
        return True
    if str(activity.get("state", "")).lower() == "_deleted":
        return True
    if str(activity.get("name", "")).lower() == "_deleted":
        return True
    return False


def sync(config: SyncConfig, log: LogFn | None = None) -> list[dict[str, Any]]:
    log = log or print

    counters = {
        "downloaded": 0,
        "dropbox": 0,
        "intervals": 0,
        "skipped": 0,
        "errors": 0,
    }

    results: list[dict[str, Any]] = []

    log("Connessione Bryton...")
    bryton = BrytonClient(debug=False)
    user_id, _token = bryton.login(config.bryton_email, config.bryton_password)
    log("✓ Login Bryton OK")

    intervals = None
    if config.upload_intervals:
        if not config.intervals_api_key:
            raise ValueError("UPLOAD_INTERVALS=true ma INTERVALS_API_KEY non impostata")
        intervals = IntervalsClient(config.intervals_api_key, config.intervals_athlete_id)
        log("✓ Intervals.icu abilitato")

    dropbox_client = None
    if config.upload_dropbox:
        if not config.dropbox_refresh_token and not config.dropbox_access_token:
            raise ValueError("Dropbox non configurato: serve refresh token oppure access token")
        dropbox_client = DropboxClient(
            access_token=config.dropbox_access_token,
            folder=config.dropbox_folder,
            app_key=config.dropbox_app_key,
            refresh_token=config.dropbox_refresh_token,
        )
        log("✓ Dropbox abilitato")

    activities_raw = bryton.list_activities(
        since=config.since,
        limit=config.max_activities,
    )

    activities = [
        a for a in activities_raw
        if not is_deleted_activity(a)
    ]

    deleted_count = len(activities_raw) - len(activities)

    log("")
    log(
        f"Attività trovate: {len(activities_raw)} "
        f"(valide: {len(activities)}, eliminate: {deleted_count})"
    )

    if not activities:
        log("")
        log("Nessuna attività valida da sincronizzare.")
        return [
            {
                "status": "nothing_to_sync",
                "total": len(activities_raw),
                "valid": 0,
                "deleted": deleted_count,
            }
        ]

    log("")

    for index, activity in enumerate(activities, start=1):
        row: dict[str, Any] = {
            "index": index,
            "status": "started",
        }

        try:
            if not isinstance(activity, dict):
                counters["skipped"] += 1
                row["status"] = "skipped_invalid"
                row["raw"] = str(activity)
                results.append(row)
                log(f"{index}/{len(activities)} skip: attività non valida")
                continue

            activity_id = bryton.activity_id(activity)
            external_id = f"bryton_{activity_id}"
            fit_filename = fit_filename_from_activity(activity, activity_id)

            row.update(
                {
                    "activity_id": activity_id,
                    "external_id": external_id,
                    "fit_filename": fit_filename,
                }
            )

            log(f"{index}/{len(activities)} {fit_filename}")

            if intervals and not config.force_resync and intervals.exists_external_id(external_id):
                counters["skipped"] += 1
                row["status"] = "skipped_exists"
                results.append(row)
                log("  • già presente su intervals.icu")
                continue

            if not config.get_download_url:
                row["status"] = "listed"
                results.append(row)
                log("  • solo lista")
                continue

            try:
                detail = bryton.get_activity_detail(activity_id)
            except Exception as exc:
                counters["errors"] += 1
                row["status"] = "detail_error"
                row["error"] = str(exc)
                results.append(row)
                log(f"  ✗ dettaglio non disponibile: {exc}")
                continue

            fit_url = bryton.find_fit_url(detail)
            row["fit_url"] = fit_url

            if not fit_url:
                counters["skipped"] += 1
                row["status"] = "no_fit_url"
                results.append(row)
                log("  • nessun FIT trovato")
                continue

            if not config.download_fit:
                row["status"] = "fit_url_found"
                results.append(row)
                log("  • FIT trovato")
                continue

            fit_path: Path = config.download_dir / fit_filename

            try:
                bryton.download_fit(fit_url, fit_path, detail=detail)
                counters["downloaded"] += 1
                row["fit_path"] = str(fit_path)
                row["status"] = "downloaded"
                log("  ✓ FIT scaricato")
            except Exception as exc:
                counters["errors"] += 1
                row["status"] = "download_error"
                row["error"] = str(exc)
                results.append(row)
                log(f"  ✗ errore download: {exc}")
                continue

            if dropbox_client:
                try:
                    dropbox_path = dropbox_client.upload_file(fit_path)
                    counters["dropbox"] += 1
                    row["dropbox_path"] = dropbox_path
                    row["status"] = "uploaded_dropbox"
                    log("  ✓ Dropbox")
                except Exception as exc:
                    counters["errors"] += 1
                    row["dropbox_error"] = str(exc)
                    log(f"  ✗ Dropbox: {exc}")

            if intervals:
                try:
                    uploaded = intervals.upload_fit(
                        fit_path,
                        external_id=external_id,
                        activity_type=config.activity_type,
                    )
                    counters["intervals"] += 1
                    row["intervals_response"] = make_json_safe(uploaded)

                    if row["status"] == "uploaded_dropbox":
                        row["status"] = "uploaded_dropbox_intervals"
                    else:
                        row["status"] = "uploaded_intervals"

                    log("  ✓ intervals.icu")
                except Exception as exc:
                    counters["errors"] += 1
                    row["intervals_error"] = str(exc)
                    log(f"  ✗ intervals.icu: {exc}")

            if config.delete_after_upload and (intervals or dropbox_client):
                fit_path.unlink(missing_ok=True)
                row["deleted_after_upload"] = True
                log("  • FIT locale cancellato")

            results.append(row)

        except Exception as exc:
            counters["errors"] += 1
            row["status"] = "error"
            row["error"] = str(exc)
            results.append(row)
            log(f"  ✗ errore imprevisto: {exc}")

    log("")
    log("Riepilogo")
    log(f"  FIT scaricati: {counters['downloaded']}")
    log(f"  Dropbox: {counters['dropbox']}")
    log(f"  intervals.icu: {counters['intervals']}")
    log(f"  Saltate: {counters['skipped']}")
    log(f"  Errori: {counters['errors']}")

    return results