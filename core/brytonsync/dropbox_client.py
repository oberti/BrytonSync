from __future__ import annotations

from pathlib import Path

import dropbox
from dropbox.files import WriteMode
from dropbox.oauth import DropboxOAuth2FlowNoRedirect


class DropboxClientError(RuntimeError):
    pass


def new_pkce_flow(app_key: str) -> DropboxOAuth2FlowNoRedirect:
    return DropboxOAuth2FlowNoRedirect(
        consumer_key=app_key,
        token_access_type="offline",
        use_pkce=True,
    )


def test_dropbox_connection(refresh_token: str, app_key: str) -> str:
    if not refresh_token:
        raise DropboxClientError("Refresh token Dropbox mancante.")

    dbx = dropbox.Dropbox(
        oauth2_refresh_token=refresh_token,
        app_key=app_key,
    )
    account = dbx.users_get_current_account()
    return account.email


class DropboxClient:
    def __init__(
        self,
        access_token: str | None = None,
        folder: str = "/BrytonSync",
        app_key: str | None = None,
        refresh_token: str | None = None,
    ) -> None:
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.app_key = app_key
        self.folder = self._normalize_folder(folder)

        if refresh_token and app_key:
            self.dbx = dropbox.Dropbox(
                oauth2_refresh_token=refresh_token,
                app_key=app_key,
            )
        elif access_token:
            self.dbx = dropbox.Dropbox(access_token)
        else:
            raise DropboxClientError("Imposta access_token oppure refresh_token + app_key Dropbox.")

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
            self.dbx.files_upload(
                handle.read(),
                dropbox_path,
                mode=WriteMode("overwrite"),
            )

        return dropbox_path