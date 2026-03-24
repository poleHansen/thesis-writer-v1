from __future__ import annotations

from pydantic import BaseModel, Field

from core_types import ExportJob, Outline, PresentationBrief, Project, ProjectFile, SlideArtifact, SlidePlan, SourceBundle, TaskRun, TemplateMeta, UserIntent
from core_types.enums import ExportFormat, ProjectFileType, SourceMode


class CreateProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    source_mode: SourceMode = SourceMode.MIXED
    tags: list[str] = Field(default_factory=list)


class ProjectResponse(BaseModel):
    project: Project


class ProjectDetailResponse(BaseModel):
    project: Project
    latest_source_bundle: SourceBundle | None = None
    latest_brief: PresentationBrief | None = None
    latest_outline: Outline | None = None
    latest_slide_plan: SlidePlan | None = None
    latest_artifact: SlideArtifact | None = None
    latest_export: ExportJob | None = None


class ProjectStatusResponse(BaseModel):
    project_id: str
    project_status: str
    current_task: TaskRun | None = None
    recent_tasks: list[TaskRun] = Field(default_factory=list)


class RegisterProjectFileRequest(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    file_type: ProjectFileType = ProjectFileType.AUTO_DETECTED
    storage_path: str = Field(min_length=1, max_length=512)
    mime_type: str | None = Field(default=None, max_length=128)
    size_bytes: int = Field(default=0, ge=0)
    checksum: str | None = Field(default=None, max_length=128)
    extracted_summary: str | None = None
    metadata: dict = Field(default_factory=dict)


class UploadProjectFileRequest(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    content_base64: str = Field(min_length=1)
    file_type: ProjectFileType = ProjectFileType.AUTO_DETECTED
    mime_type: str | None = Field(default=None, max_length=128)
    metadata: dict = Field(default_factory=dict)


class ProjectFileResponse(BaseModel):
    file: ProjectFile


class ProjectFilesResponse(BaseModel):
    files: list[ProjectFile] = Field(default_factory=list)


class GenerateBriefRequest(BaseModel):
    force_regenerate: bool = False
    user_intent_override: UserIntent | None = None


class BriefResponse(BaseModel):
    brief: PresentationBrief
    task_run: TaskRun | None = None


class UpdateBriefRequest(BaseModel):
    brief_id: str | None = None
    presentation_goal: str | None = None
    target_audience: str | None = None
    core_message: str | None = None
    storyline: str | None = None
    recommended_page_count: int | None = Field(default=None, ge=1)
    tone: str | None = None
    style_preferences: list[str] | None = None
    risks: list[str] | None = None
    assumptions: list[str] | None = None
    metadata: dict | None = None


class UpdateBriefResponse(BaseModel):
    brief: PresentationBrief


class SourceBundleResponse(BaseModel):
    source_bundle: SourceBundle


class ParseProjectFilesRequest(BaseModel):
    file_ids: list[str] | None = None
    rebuild_bundle: bool = True
    user_intent: UserIntent | None = None


class ParseProjectFilesResponse(BaseModel):
    files: list[ProjectFile] = Field(default_factory=list)
    source_bundle: SourceBundle | None = None
    task_run: TaskRun


class GenerateOutlineRequest(BaseModel):
    brief_id: str | None = None
    force_regenerate: bool = False


class OutlineResponse(BaseModel):
    outline: Outline
    task_run: TaskRun | None = None


class UpdateOutlineRequest(BaseModel):
    outline_id: str | None = None
    title: str | None = None
    chapters: list[dict] | None = None
    summary: str | None = None
    metadata: dict | None = None


class UpdateOutlineResponse(BaseModel):
    outline: Outline


class GenerateSlidePlanRequest(BaseModel):
    outline_id: str | None = None
    preferred_template_id: str | None = None
    force_regenerate: bool = False


class SlidePlanResponse(BaseModel):
    slide_plan: SlidePlan
    task_run: TaskRun | None = None


class GenerateSlideArtifactRequest(BaseModel):
    slide_plan_id: str | None = None
    template_id: str | None = None


class SlideArtifactResponse(BaseModel):
    artifact: SlideArtifact
    task_run: TaskRun | None = None


class GenerateExportRequest(BaseModel):
    artifact_id: str | None = None
    export_format: ExportFormat = ExportFormat.PPTX


class ExportJobResponse(BaseModel):
    export_job: ExportJob
    task_run: TaskRun | None = None


class UpdateSlidePlanRequest(BaseModel):
    slide_plan_id: str | None = None
    page_count: int | None = Field(default=None, ge=0)
    slides: list[dict] | None = None
    design_direction: str | None = None
    metadata: dict | None = None


class UpdateSlidePlanResponse(BaseModel):
    slide_plan: SlidePlan


class TemplatesResponse(BaseModel):
    templates: list[TemplateMeta] = Field(default_factory=list)
