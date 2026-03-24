from __future__ import annotations

import json
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

    def save_project_artifact(self, project_id: str, artifact_name: str, payload: dict[str, object]) -> str:
        artifact_dir = self._storage_root / "projects" / project_id / "artifacts"
        artifact_dir.mkdir(parents=True, exist_ok=True)

        target_path = artifact_dir / artifact_name
        target_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(target_path)

    def ensure_render_directories(self, project_id: str, artifact_id: str) -> tuple[str, str]:
        base_dir = self._storage_root / "projects" / project_id / "render" / artifact_id
        output_dir = base_dir / "svg_output"
        final_dir = base_dir / "svg_final"
        output_dir.mkdir(parents=True, exist_ok=True)
        final_dir.mkdir(parents=True, exist_ok=True)
        return str(output_dir), str(final_dir)

    def save_render_context(self, project_id: str, artifact_id: str, file_name: str, payload: dict[str, object]) -> str:
        context_dir = self._storage_root / "projects" / project_id / "render" / artifact_id
        context_dir.mkdir(parents=True, exist_ok=True)
        target_path = context_dir / file_name
        target_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(target_path)

    def save_svg_page(self, directory: str | Path, file_name: str, svg_content: str) -> str:
        target_dir = Path(directory)
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / file_name
        target_path.write_text(svg_content, encoding="utf-8")
        return str(target_path)

    def save_export_file(self, project_id: str, artifact_id: str, run_id: str, file_name: str, content: bytes) -> str:
        export_dir = self._storage_root / "projects" / project_id / "exports" / artifact_id / run_id
        export_dir.mkdir(parents=True, exist_ok=True)
        target_path = export_dir / file_name
        target_path.write_bytes(content)
        return str(target_path)

    def build_export_path(self, project_id: str, artifact_id: str, run_id: str, file_name: str) -> str:
        export_dir = self._storage_root / "projects" / project_id / "exports" / artifact_id / run_id
        export_dir.mkdir(parents=True, exist_ok=True)
        return str(export_dir / file_name)

    def save_export_context(self, project_id: str, artifact_id: str, run_id: str, file_name: str, payload: dict[str, object]) -> str:
        export_dir = self._storage_root / "projects" / project_id / "exports" / artifact_id / run_id
        export_dir.mkdir(parents=True, exist_ok=True)
        target_path = export_dir / file_name
        target_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(target_path)