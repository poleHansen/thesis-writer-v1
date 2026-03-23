from __future__ import annotations

from pydantic import Field

from core_types.common import IdentifiedModel, JsonDict
from core_types.enums import ProjectFileType, ProjectStatus, FileUploadStatus, ParseStatus, SourceMode


class Project(IdentifiedModel):
    name: str
    description: str | None = None
    status: ProjectStatus = ProjectStatus.CREATED
    source_mode: SourceMode = SourceMode.MIXED
    owner_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    current_template_id: str | None = None
    latest_source_bundle_id: str | None = None
    latest_brief_id: str | None = None
    latest_outline_id: str | None = None
    latest_slide_plan_id: str | None = None
    latest_artifact_id: str | None = None
    last_error_code: str | None = None
    metadata: JsonDict = Field(default_factory=dict)


class ProjectFile(IdentifiedModel):
    project_id: str
    file_name: str
    file_type: ProjectFileType = ProjectFileType.AUTO_DETECTED
    storage_path: str
    mime_type: str | None = None
    size_bytes: int = 0
    checksum: str | None = None
    upload_status: FileUploadStatus = FileUploadStatus.UPLOADED
    parse_status: ParseStatus = ParseStatus.PENDING
    parse_error: str | None = None
    extracted_summary: str | None = None
    metadata: JsonDict = Field(default_factory=dict)
