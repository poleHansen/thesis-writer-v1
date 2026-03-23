from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from uuid import uuid4


class FileStorageService:
    def __init__(self, storage_root: str | Path) -> None:
        self._storage_root = Path(storage_root)

    def save_project_file(self, project_id: str, file_name: str, content: bytes) -> tuple[str, str, int]:
        project_dir = self._storage_root / "uploads" / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        sanitized_name = Path(file_name).name or f"upload-{uuid4().hex}"
        target_path = project_dir / f"{uuid4().hex}-{sanitized_name}"
        target_path.write_bytes(content)

        checksum = sha256(content).hexdigest()
        return str(target_path), checksum, len(content)