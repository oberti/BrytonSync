from __future__ import annotations

from pathlib import Path
from typing import Any

import requests


class BrytonWorkoutClientError(RuntimeError):
    pass


class BrytonWorkoutClient:
    def __init__(
        self,
        user_id: str,
        auth_token: str,
        base_url: str = "https://m2.brytonactive.com",
        timeout: int = 30,
    ) -> None:
        self.user_id = user_id
        self.auth_token = auth_token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-User-Id": user_id,
                "X-Auth-Token": auth_token,
            }
        )

    def list_workouts(self) -> Any:
        resp = self.session.get(
            f"{self.base_url}/api/files",
            timeout=self.timeout,
        )

        if not resp.ok:
            raise BrytonWorkoutClientError(
                f"Bryton workout list fallita "
                f"{resp.status_code}: {resp.text[:500]}"
            )

        try:
            return resp.json()
        except ValueError:
            return resp.text

    def upload_workout_fit(
        self,
        fit_path: Path,
        name: str,
        info_json: str,
        provider: str = "bryton",
        org_id: str | None = None,
    ) -> dict[str, Any]:
        if not fit_path.exists():
            raise BrytonWorkoutClientError(f"FIT non trovato: {fit_path}")

        data = {
            "name": name,
            "provider": provider,
            "info": info_json,
        }

        if org_id:
            data["orgid"] = org_id

        with fit_path.open("rb") as handle:
            files = {
                "track": (
                    fit_path.name,
                    handle,
                    "application/octet-stream",
                )
            }

            resp = self.session.post(
                f"{self.base_url}/workout/upload/{self.user_id}",
                data=data,
                files=files,
                timeout=self.timeout,
            )

        if not resp.ok:
            raise BrytonWorkoutClientError(
                f"Upload workout Bryton fallito "
                f"{resp.status_code}: {resp.text[:1000]}"
            )

        try:
            return resp.json()
        except ValueError:
            return {"status": "ok", "text": resp.text}