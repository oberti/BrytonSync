from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import requests

from .crypto import decrypt_bryton_aes, make_login_payload


BRYTON_BASE_URL = "https://m2.brytonactive.com"
ANNOUNCEMENT_URL = "https://www.brytonsport.com/download/Docs/announcement-nativeapp-v3.json?cache=false"


class BrytonClientError(RuntimeError):
    pass


class BrytonClient:
    def __init__(self, base_url: str = BRYTON_BASE_URL, timeout: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.user_id: str | None = None
        self.auth_token: str | None = None
        self.login_pwd_key: str | None = None

    def fetch_announcement(self) -> dict[str, Any]:
        resp = self.session.get(ANNOUNCEMENT_URL, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def get_login_pwd_key(self) -> str:
        data = self.fetch_announcement()
        encrypted = data.get("login")
        if not encrypted:
            raise BrytonClientError("Nel JSON announcement manca il campo 'login'.")
        self.login_pwd_key = decrypt_bryton_aes(str(encrypted))
        return self.login_pwd_key

    def login(self, email: str, password: str, login_pwd_key: str | None = None) -> tuple[str, str]:
        key = login_pwd_key or self.login_pwd_key or self.get_login_pwd_key()
        payload = make_login_payload(email=email, password=password, login_pwd_key=key)

        resp = self.session.post(
            f"{self.base_url}/api/login",
            json=payload,
            timeout=self.timeout,
        )

        if not resp.ok:
            raise BrytonClientError(f"Login fallito {resp.status_code}: {resp.text[:500]}")

        data = resp.json()
        user_data = data.get("data") or data
        user_id = user_data.get("userId")
        auth_token = user_data.get("authToken")

        if not user_id or not auth_token:
            raise BrytonClientError(f"Risposta login inattesa: {json.dumps(data)[:500]}")

        self.user_id = str(user_id)
        self.auth_token = str(auth_token)
        return self.user_id, self.auth_token

    @property
    def auth_headers(self) -> dict[str, str]:
        if not self.user_id or not self.auth_token:
            raise BrytonClientError("Non autenticato. Chiama login() prima.")
        return {
            "X-User-Id": self.user_id,
            "X-Auth-Token": self.auth_token,
        }

    def list_activities(self, since: int = 0, limit: int = 10) -> list[dict[str, Any]]:
        resp = self.session.get(
            f"{self.base_url}/api/activity",
            headers=self.auth_headers,
            params={"since": since, "limit": limit},
            timeout=self.timeout,
        )

        if not resp.ok:
            raise BrytonClientError(f"Lista attività fallita {resp.status_code}: {resp.text[:500]}")

        data = resp.json()

        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            for key in ("data", "activities", "list", "results"):
                value = data.get(key)
                if isinstance(value, list):
                    return value

        raise BrytonClientError(f"Formato lista attività inatteso: {json.dumps(data)[:500]}")

    def get_activity_detail(self, activity_id: str) -> dict[str, Any]:
        resp = self.session.get(
            f"{self.base_url}/api/activity",
            headers=self.auth_headers,
            params={"id": activity_id},
            timeout=self.timeout,
        )

        if not resp.ok:
            raise BrytonClientError(f"Dettaglio attività fallito {resp.status_code}: {resp.text[:500]}")

        content_type = resp.headers.get("content-type", "")
        content_disposition = resp.headers.get("content-disposition", "")

        print("DETAIL status:", resp.status_code)
        print("DETAIL content-type:", content_type)
        print("DETAIL content-disposition:", content_disposition)
        print("DETAIL headers:")
        for key, value in resp.headers.items():
            print(f"  {key}: {value}")
        print("DETAIL first bytes:", resp.content[:80])

        original_filename = self.filename_from_headers(resp.headers)

        if resp.content.startswith(b".FIT") or resp.content.startswith(b"\x0e\x10") or b".FIT" in resp.content[:20]:
            return {
                "_direct_fit": True,
                "raw_content_type": content_type,
                "raw_content_disposition": content_disposition,
                "raw_original_filename": original_filename,
                "raw_content": resp.content,
            }

        try:
            data = resp.json()
            if isinstance(data, dict) and original_filename:
                data["_raw_original_filename"] = original_filename
            return data if isinstance(data, dict) else {"data": data}
        except Exception:
            return {
                "raw_content_type": content_type,
                "raw_content_disposition": content_disposition,
                "raw_original_filename": original_filename,
                "raw_text": resp.text[:1000],
                "raw_bytes_prefix": resp.content[:80].hex(),
            }

    def find_fit_url(self, obj: Any) -> str | None:
        """Search recursively for a plausible FIT download URL in Bryton JSON."""
        if isinstance(obj, dict):
            if obj.get("_direct_fit"):
                return "__DIRECT_FIT__"

            preferred_keys = (
                "fitUrl",
                "fit_url",
                "fileUrl",
                "file_url",
                "downloadUrl",
                "download_url",
                "url",
                "fit",
                "file",
                "path",
            )

            for key in preferred_keys:
                if key in obj:
                    found = self.find_fit_url(obj[key])
                    if found:
                        return found

            for value in obj.values():
                found = self.find_fit_url(value)
                if found:
                    return found

        elif isinstance(obj, list):
            for value in obj:
                found = self.find_fit_url(value)
                if found:
                    return found

        elif isinstance(obj, str):
            low = obj.lower()
            if low.startswith("http") and (".fit" in low or "fit" in low or "download" in low):
                return obj

        return None

    def download_fit(self, file_url: str, output_path: Path, detail: dict[str, Any] | None = None) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if file_url == "__DIRECT_FIT__":
            if not detail or "raw_content" not in detail:
                raise BrytonClientError("FIT diretto trovato, ma raw_content mancante.")
            output_path.write_bytes(detail["raw_content"])
            return output_path

        headers = self.auth_headers if urlparse(file_url).netloc else {}

        resp = self.session.get(
            file_url,
            headers=headers,
            timeout=self.timeout,
        )

        if not resp.ok:
            raise BrytonClientError(f"Download FIT fallito {resp.status_code}: {resp.text[:500]}")

        output_path.write_bytes(resp.content)
        return output_path

    @staticmethod
    def activity_id(activity: dict[str, Any]) -> str:
        for key in ("_id", "id", "activityId", "activity_id", "trackId", "fileId", "rideId"):
            if activity.get(key) is not None:
                return str(activity[key])

        raise BrytonClientError(f"Impossibile trovare ID attività in: {activity}")

    @staticmethod
    def filename_from_headers(headers: Any) -> str | None:
        content_disposition = headers.get("content-disposition", "") or headers.get("Content-Disposition", "")
        if not content_disposition:
            return None

        match = re.search(r"filename\*=UTF-8''([^;]+)", content_disposition, flags=re.IGNORECASE)
        if match:
            return unquote(match.group(1)).strip().strip('"')

        match = re.search(r'filename="([^"]+)"', content_disposition, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()

        match = re.search(r"filename=([^;]+)", content_disposition, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip().strip('"')

        return None

    @staticmethod
    def safe_filename(name: str) -> str:
        name = name.strip()
        name = re.sub(r'[<>:"/\\|?*]+', "_", name)
        name = re.sub(r"\s+", " ", name)
        name = name.strip(" .")
        if not name:
            name = "activity"
        if not name.lower().endswith(".fit"):
            name += ".fit"
        return name

    def suggest_fit_filename(
        self,
        activity: dict[str, Any],
        detail: dict[str, Any] | None,
        fallback_id: str,
    ) -> str:
        candidates: list[str] = []

        if detail:
            for key in (
                "raw_original_filename",
                "_raw_original_filename",
                "filename",
                "fileName",
                "fitName",
                "fit_name",
                "name",
            ):
                value = detail.get(key)
                if isinstance(value, str) and value.strip():
                    candidates.append(value.strip())

        for key in ("fitName", "fit_name", "fileName", "filename", "name", "title"):
            value = activity.get(key)
            if isinstance(value, str) and value.strip():
                candidates.append(value.strip())

        candidates.append(fallback_id)

        return self.safe_filename(candidates[0])