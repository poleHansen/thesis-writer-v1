from __future__ import annotations

from datetime import datetime

from pydantic import Field

from core_types.common import IdentifiedModel, JsonDict
from core_types.enums import ExportFormat, ExportStatus, TaskStatus, TaskType


class ExportJob(IdentifiedModel):
    project_id: str
    artifact_id: str
    run_id: str
    export_format: ExportFormat = ExportFormat.PPTX
    export_path: str | None = None
    preview_pdf_path: str | None = None
    status: ExportStatus = ExportStatus.PENDING
    error_message: str | None = None
    metadata: JsonDict = Field(default_factory=dict)


class TaskRun(IdentifiedModel):
    project_id: str
    task_type: TaskType
    task_status: TaskStatus = TaskStatus.PENDING
    trigger_source: str = "api"
    payload: JsonDict = Field(default_factory=dict)
    result: JsonDict = Field(default_factory=dict)
    error_code: str | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
