from __future__ import annotations

from pathlib import Path

import dropbox
from dropbox.files import WriteMode

from .config import DEFAULT_DROPBOX_APP_KEY


class DropboxClientError(RuntimeError):
    pass


class DropboxClient:
    def __init__(
        self,
        access_token: str | None = None,
        folder: str = "/BrytonSync",
        app_key: str | None = None,
        refresh_token: str | None = None,
    ) -> None:
        self.folder = self._normalize_folder(folder)
        app_key = (app_key or DEFAULT_DROPBOX_APP_KEY).strip()

        if refresh_token:
            self.dbx = dropbox.Dropbox(
                oauth2_refresh_token=refresh_token.strip(),
                app_key=app_key,
            )
        elif access_token:
            self.dbx = dropbox.Dropbox(access_token.strip())
        else:
            raise DropboxClientError("Serve Dropbox refresh token oppure access token")

    @staticmethod
    def _normalize_folder(folder: str) -> str:
        folder = (folder or "/BrytonSync").strip().replace("\\", "/")
        if not folder.startswith("/"):
            folder = "/" + folder
        return folder.rstrip("/") or "/BrytonSync"

    def upload_file(self, local_path: Path, remote_name: str | None = None) -> str:
        if not local_path.exists():
            raise DropboxClientError(f"File non trovato: {local_path}")
        remote_name = remote_name or local_path.name
        dropbox_path = f"{self.folder}/{remote_name}".replace("\\", "/")
        with local_path.open("rb") as handle:
            self.dbx.files_upload(handle.read(), dropbox_path, mode=WriteMode("overwrite"))
        return dropbox_path


def new_pkce_flow(app_key: str = DEFAULT_DROPBOX_APP_KEY) -> dropbox.DropboxOAuth2FlowNoRedirect:
    return dropbox.DropboxOAuth2FlowNoRedirect(
        consumer_key=app_key.strip(),
        token_access_type="offline",
        use_pkce=True,
        scope=[
            "account_info.read",
            "files.metadata.read",
            "files.content.write",
        ],
    )


def test_dropbox_connection(refresh_token: str, app_key: str = DEFAULT_DROPBOX_APP_KEY) -> str:
    dbx = dropbox.Dropbox(
        oauth2_refresh_token=refresh_token.strip(),
        app_key=app_key.strip(),
    )
    account = dbx.users_get_current_account()
    return getattr(account, "email", "Dropbox collegato")
