from __future__ import annotations

from pathlib import Path
from typing import Any

import requests


class IntervalsClientError(RuntimeError):
    pass


class IntervalsClient:
    def __init__(self, api_key: str, athlete_id: str = "999999", timeout: int = 60) -> None:
        self.api_key = api_key
        self.athlete_id = str(athlete_id).strip().lstrip("i")
        self.timeout = timeout
        self.base_url = "https://intervals.icu/api/v1"
        self.session = requests.Session()
        self.session.auth = ("API_KEY", api_key)

    def exists_external_id(self, external_id: str) -> bool:
        resp = self.session.get(
            f"{self.base_url}/athlete/{self.athlete_id}/activities",
            params={"oldest": "2000-01-01", "newest": "2100-01-01", "external_id": external_id},
            timeout=self.timeout,
        )
        if resp.ok:
            data = resp.json()
            if isinstance(data, list):
                return any(str(a.get("external_id") or a.get("externalId") or "") == external_id for a in data)
        return False

    def upload_fit(self, fit_path: Path, external_id: str | None = None, activity_type: str = "") -> dict[str, Any]:
        params: dict[str, str] = {}
        if external_id:
            params["external_id"] = external_id
        if activity_type:
            params["type"] = activity_type
        with fit_path.open("rb") as handle:
            files = {"file": (fit_path.name, handle, "application/octet-stream")}
            resp = self.session.post(
                f"{self.base_url}/athlete/{self.athlete_id}/activities",
                params=params,
                files=files,
                timeout=self.timeout,
            )
        if not resp.ok:
            raise IntervalsClientError(f"Upload Intervals fallito {resp.status_code}: {resp.text[:500]}")
        try:
            return resp.json()
        except ValueError:
            return {"status": "ok", "text": resp.text}
