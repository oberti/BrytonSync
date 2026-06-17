from __future__ import annotations

from pathlib import Path

import dropbox
from dropbox.files import WriteMode


class DropboxClientError(RuntimeError):
    pass


class DropboxClient:
    def __init__(self, access_token: str, folder: str = "/BrytonSync") -> None:
        self.access_token = access_token
        self.folder = self._normalize_folder(folder)
        self.dbx = dropbox.Dropbox(access_token)

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