from __future__ import annotations

import json
import webbrowser
from pathlib import Path
from typing import Any

import flet as ft

from brytonsync.config import SyncConfig
from brytonsync.dropbox_client import new_pkce_flow, test_dropbox_connection
from brytonsync.planned_workout_sync import sync_planned_workouts
from brytonsync.sync import sync

DEFAULT_DROPBOX_APP_KEY = "4e9vei57q5t2jnw"

SETTINGS_FILE = Path("brytonsync_settings.json")


def load_settings() -> dict[str, Any]:
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_settings(data: dict[str, Any]) -> None:
    SETTINGS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main(page: ft.Page) -> None:
    page.title = "BrytonSync"
    page.theme_mode = ft.ThemeMode.SYSTEM
    page.scroll = ft.ScrollMode.AUTO
    page.window_width = 470
    page.window_height = 900

    settings = load_settings()
    oauth_flow: dict[str, Any] = {"flow": None}

    def field(label: str, key: str, password: bool = False, default: str = "") -> ft.TextField:
        return ft.TextField(
            label=label,
            value=str(settings.get(key, default)),
            password=password,
            can_reveal_password=password,
            dense=True,
            text_size=12,
            height=48,
        )

    bryton_email = field("Bryton email", "bryton_email")
    bryton_password = field("Bryton password", "bryton_password", password=True)

    intervals_api_key = field("Intervals API key", "intervals_api_key", password=True)
    intervals_athlete_id = field(
        "Intervals Athlete ID",
        "intervals_athlete_id",
        default="999999",
    )

    planned_days_ahead = field(
        "Giorni futuri workout",
        "planned_days_ahead",
        default="14",
    )

    dropbox_auth_code = ft.TextField(
        label="Codice autorizzazione Dropbox",
        dense=True,
        text_size=12,
        height=48,
    )
    dropbox_refresh_token = field("Dropbox refresh token", "dropbox_refresh_token", password=True)
    dropbox_folder = field("Cartella Dropbox", "dropbox_folder", default="/BrytonSync")

    max_activities = field("Numero attività", "max_activities", default="5")

    upload_intervals = ft.Checkbox(
        label="Carica attività su intervals.icu",
        value=bool(settings.get("upload_intervals", False)),
    )
    upload_dropbox = ft.Checkbox(
        label="Carica attività su Dropbox",
        value=bool(settings.get("upload_dropbox", False)),
    )
    force_resync = ft.Checkbox(
        label="Forza re-sync attività",
        value=bool(settings.get("force_resync", False)),
    )
    delete_after_upload = ft.Checkbox(
        label="Cancella FIT locale dopo upload",
        value=bool(settings.get("delete_after_upload", False)),
    )

    log_view = ft.TextField(
        label="Log",
        value="",
        multiline=True,
        min_lines=8,
        max_lines=10,
        read_only=True,
        text_size=10,
    )

    sync_activities_btn = ft.ElevatedButton("Sync uscite")
    sync_workouts_btn = ft.ElevatedButton("Sync workout")
    sync_all_btn = ft.ElevatedButton("Sync tutto")
    save_btn = ft.OutlinedButton("Salva impostazioni")
    connect_dropbox_btn = ft.ElevatedButton("Collega Dropbox")
    save_dropbox_code_btn = ft.OutlinedButton("Salva codice Dropbox")
    test_dropbox_btn = ft.OutlinedButton("Test Dropbox")

    def append_log(text: str) -> None:
        log_view.value = (log_view.value or "") + text + "\n"
        page.update()

    def get_cfg() -> SyncConfig:
        try:
            max_n = int(max_activities.value or "5")
        except ValueError:
            max_n = 5

        return SyncConfig(
            bryton_email=(bryton_email.value or "").strip(),
            bryton_password=(bryton_password.value or "").strip(),
            intervals_api_key=(intervals_api_key.value or "").strip() or None,
            intervals_athlete_id=(intervals_athlete_id.value or "999999").strip().lstrip("i"),
            max_activities=max_n,
            download_dir=Path("downloads"),
            delete_after_upload=bool(delete_after_upload.value),
            force_resync=bool(force_resync.value),
            list_activities=True,
            get_download_url=True,
            download_fit=True,
            upload_intervals=bool(upload_intervals.value),
            upload_dropbox=bool(upload_dropbox.value),
            dropbox_app_key=DEFAULT_DROPBOX_APP_KEY,
            dropbox_refresh_token=(dropbox_refresh_token.value or "").strip() or None,
            dropbox_folder=(dropbox_folder.value or "/BrytonSync").strip(),
        )

    def get_days_ahead() -> int:
        try:
            return int(planned_days_ahead.value or "14")
        except ValueError:
            return 14

    def current_settings() -> dict[str, Any]:
        return {
            "bryton_email": bryton_email.value or "",
            "bryton_password": bryton_password.value or "",
            "intervals_api_key": intervals_api_key.value or "",
            "intervals_athlete_id": intervals_athlete_id.value or "999999",
            "planned_days_ahead": planned_days_ahead.value or "14",
            "dropbox_refresh_token": dropbox_refresh_token.value or "",
            "dropbox_folder": dropbox_folder.value or "/BrytonSync",
            "max_activities": max_activities.value or "5",
            "upload_intervals": bool(upload_intervals.value),
            "upload_dropbox": bool(upload_dropbox.value),
            "force_resync": bool(force_resync.value),
            "delete_after_upload": bool(delete_after_upload.value),
        }

    def save_clicked(e: ft.ControlEvent | None = None) -> None:
        save_settings(current_settings())
        append_log("Impostazioni salvate.")

    async def connect_dropbox_clicked(e: ft.ControlEvent) -> None:
        try:
            flow = new_pkce_flow(DEFAULT_DROPBOX_APP_KEY)
            oauth_flow["flow"] = flow
            auth_url = flow.start()

            append_log("Apro Dropbox nel browser. Autorizza l'app e copia il codice qui sotto.")
            append_log(f"URL Dropbox: {auth_url}")

            try:
                await page.launch_url(auth_url)
                append_log("Apertura browser richiesta.")
            except Exception:
                try:
                    opened = webbrowser.open(auth_url, new=2)
                    if opened:
                        append_log("Browser aperto tramite fallback.")
                    else:
                        append_log("Apri manualmente questo URL:")
                        append_log(auth_url)
                except Exception:
                    append_log("Apri manualmente questo URL:")
                    append_log(auth_url)

        except Exception as exc:
            append_log(f"ERRORE Dropbox OAuth: {exc}")

    def save_dropbox_code_clicked(e: ft.ControlEvent) -> None:
        flow = oauth_flow.get("flow")
        if flow is None:
            append_log("Prima premi 'Collega Dropbox'.")
            return

        code = (dropbox_auth_code.value or "").strip()
        if not code:
            append_log("Incolla il codice autorizzazione Dropbox.")
            return

        try:
            result = flow.finish(code)
            refresh = getattr(result, "refresh_token", None)

            if not refresh:
                append_log("ERRORE: Dropbox non ha restituito refresh_token.")
                return

            dropbox_refresh_token.value = refresh
            upload_dropbox.value = True
            save_settings(current_settings())
            append_log("Dropbox collegato. Refresh token salvato.")
            page.update()

        except Exception as exc:
            append_log(f"ERRORE salvataggio codice Dropbox: {exc}")

    def test_dropbox_clicked(e: ft.ControlEvent) -> None:
        try:
            email = test_dropbox_connection(
                (dropbox_refresh_token.value or "").strip(),
                DEFAULT_DROPBOX_APP_KEY,
            )
            append_log(f"Dropbox OK: {email}")
        except Exception as exc:
            append_log(f"ERRORE Dropbox: {exc}")

    def set_buttons(disabled: bool) -> None:
        sync_activities_btn.disabled = disabled
        sync_workouts_btn.disabled = disabled
        sync_all_btn.disabled = disabled
        page.update()

    def run_activities_sync() -> None:
        set_buttons(True)
        try:
            save_clicked(None)
            log_view.value = ""
            append_log("Avvio sync uscite...")

            cfg = get_cfg()
            results = sync(cfg)

            append_log("Sync uscite completata.")
            append_log(json.dumps(results, indent=2, ensure_ascii=False))

        except Exception as exc:
            append_log(f"ERRORE sync uscite: {exc}")

        finally:
            set_buttons(False)
            append_log("Completato.")


    def run_workouts_sync() -> None:
        set_buttons(True)
        try:
            save_clicked(None)
            log_view.value = ""
            append_log("Avvio sync workout pianificati...")

            cfg = get_cfg()
            if not cfg.intervals_api_key:
                raise ValueError("Intervals API key mancante.")

            results = sync_planned_workouts(
                bryton_email=cfg.bryton_email,
                bryton_password=cfg.bryton_password,
                intervals_api_key=cfg.intervals_api_key,
                intervals_athlete_id="0",
                days_ahead=get_days_ahead(),
                output_dir=Path("planned_workouts"),
                dry_run=False,
            )

            append_log("Sync workout completata.")
            append_log(json.dumps(results, indent=2, ensure_ascii=False))

        except Exception as exc:
            append_log(f"ERRORE sync workout: {exc}")


        finally:
            set_buttons(False)
            append_log("Completato.")
            

    def run_all_sync() -> None:
        set_buttons(True)
        try:
            save_clicked(None)
            log_view.value = ""
            append_log("Avvio sync completa...")

            cfg = get_cfg()
            results: dict[str, Any] = {}

            append_log("Sync uscite...")
            results["activities"] = sync(cfg)

            if not cfg.intervals_api_key:
                raise ValueError("Intervals API key mancante per sync workout.")

            append_log("Sync workout...")
            results["workouts"] = sync_planned_workouts(
                bryton_email=cfg.bryton_email,
                bryton_password=cfg.bryton_password,
                intervals_api_key=cfg.intervals_api_key,
                intervals_athlete_id="0",
                days_ahead=get_days_ahead(),
                output_dir=Path("planned_workouts"),
                dry_run=False,
            )

            append_log("Sync completa terminata.")
            append_log(json.dumps(results, indent=2, ensure_ascii=False))

        except Exception as exc:
            append_log(f"ERRORE sync completa: {exc}")


        finally:
            set_buttons(False)
            append_log("Completato.")


    def sync_activities_clicked(e: ft.ControlEvent) -> None:
        page.run_thread(run_activities_sync)

    def sync_workouts_clicked(e: ft.ControlEvent) -> None:
        page.run_thread(run_workouts_sync)

    def sync_all_clicked(e: ft.ControlEvent) -> None:
        page.run_thread(run_all_sync)

    save_btn.on_click = save_clicked
    sync_activities_btn.on_click = sync_activities_clicked
    sync_workouts_btn.on_click = sync_workouts_clicked
    sync_all_btn.on_click = sync_all_clicked
    connect_dropbox_btn.on_click = connect_dropbox_clicked
    save_dropbox_code_btn.on_click = save_dropbox_code_clicked
    test_dropbox_btn.on_click = test_dropbox_clicked

    page.add(
        ft.SafeArea(
            ft.Column(
                controls=[
                    ft.Text("BrytonSync v2.0.0", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        "Bryton uscite → Intervals/Dropbox | Intervals workout → Bryton Active",
                        size=11,
                    ),
                    ft.Divider(height=6),
                    bryton_email,
                    bryton_password,
                    ft.Divider(height=6),
                    upload_intervals,
                    intervals_api_key,
                    intervals_athlete_id,
                    planned_days_ahead,
                    ft.Divider(height=6),
                    upload_dropbox,
                    ft.Text("Dropbox OAuth PKCE", size=12, weight=ft.FontWeight.BOLD),
                    ft.Text("L'app apre Dropbox e salva il refresh token.", size=10),
                    ft.Row([connect_dropbox_btn, test_dropbox_btn], wrap=True),
                    dropbox_auth_code,
                    save_dropbox_code_btn,
                    dropbox_refresh_token,
                    dropbox_folder,
                    ft.Divider(height=6),
                    max_activities,
                    force_resync,
                    delete_after_upload,
                    ft.Row([save_btn], wrap=True),
                    ft.Row([sync_activities_btn, sync_workouts_btn], wrap=True),
                    ft.Row([sync_all_btn], wrap=True),
                    log_view,
                ],
                spacing=4,
            )
        )
    )


ft.app(target=main)