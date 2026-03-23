from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProjectRecord(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    owner_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    current_template_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    latest_source_bundle_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("source_bundles.id"), nullable=True)
    latest_brief_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("presentation_briefs.id"), nullable=True)
    latest_outline_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("outlines.id"), nullable=True)
    latest_slide_plan_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("slide_plans.id"), nullable=True)
    latest_artifact_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("slide_artifacts.id"), nullable=True)
    last_error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class TaskRunRecord(Base):
    __tablename__ = "task_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False, index=True)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    task_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    trigger_source: Mapped[str] = mapped_column(String(32), nullable=False, default="api")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class ProjectFileRecord(Base):
    __tablename__ = "project_files"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    size_bytes: Mapped[int] = mapped_column(nullable=False, default=0)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    upload_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    parse_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    parse_error: Mapped[str | None] = mapped_column(Text(), nullable=True)
    extracted_summary: Mapped[str | None] = mapped_column(Text(), nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class SourceBundleRecord(Base):
    __tablename__ = "source_bundles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False, index=True)
    source_file_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    user_intent: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    raw_markdown: Mapped[str | None] = mapped_column(Text(), nullable=True)
    normalized_markdown: Mapped[str | None] = mapped_column(Text(), nullable=True)
    page_chunks: Mapped[list[dict]] = mapped_column(JSON, default=list)
    tables: Mapped[list[dict]] = mapped_column(JSON, default=list)
    images: Mapped[list[dict]] = mapped_column(JSON, default=list)
    citations: Mapped[list[str]] = mapped_column(JSON, default=list)
    language: Mapped[str] = mapped_column(String(32), nullable=False, default="zh-CN")
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class PresentationBriefRecord(Base):
    __tablename__ = "presentation_briefs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False, index=True)
    source_bundle_id: Mapped[str] = mapped_column(String(64), ForeignKey("source_bundles.id"), nullable=False, index=True)
    presentation_goal: Mapped[str] = mapped_column(Text(), nullable=False)
    target_audience: Mapped[str] = mapped_column(String(255), nullable=False)
    core_message: Mapped[str] = mapped_column(Text(), nullable=False)
    storyline: Mapped[str] = mapped_column(Text(), nullable=False)
    recommended_page_count: Mapped[int] = mapped_column(nullable=False, default=12)
    tone: Mapped[str] = mapped_column(String(64), nullable=False, default="professional")
    style_preferences: Mapped[list[str]] = mapped_column(JSON, default=list)
    risks: Mapped[list[str]] = mapped_column(JSON, default=list)
    assumptions: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class OutlineRecord(Base):
    __tablename__ = "outlines"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False, index=True)
    brief_id: Mapped[str] = mapped_column(String(64), ForeignKey("presentation_briefs.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    chapters: Mapped[list[dict]] = mapped_column(JSON, default=list)
    summary: Mapped[str | None] = mapped_column(Text(), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class SlidePlanRecord(Base):
    __tablename__ = "slide_plans"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False, index=True)
    brief_id: Mapped[str] = mapped_column(String(64), ForeignKey("presentation_briefs.id"), nullable=False, index=True)
    outline_id: Mapped[str] = mapped_column(String(64), ForeignKey("outlines.id"), nullable=False, index=True)
    page_count: Mapped[int] = mapped_column(nullable=False, default=0)
    slides: Mapped[list[dict]] = mapped_column(JSON, default=list)
    design_direction: Mapped[str | None] = mapped_column(Text(), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class SlideArtifactRecord(Base):
    __tablename__ = "slide_artifacts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False, index=True)
    slide_plan_id: Mapped[str] = mapped_column(String(64), ForeignKey("slide_plans.id"), nullable=False, index=True)
    template_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("templates.id"), nullable=True, index=True)
    svg_output_dir: Mapped[str | None] = mapped_column(String(512), nullable=True)
    svg_final_dir: Mapped[str | None] = mapped_column(String(512), nullable=True)
    preview_image_paths: Mapped[list[str]] = mapped_column(JSON, default=list)
    render_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    failed_slide_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    log_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class TemplateRecord(Base):
    __tablename__ = "templates"
    __table_args__ = (UniqueConstraint("template_id", name="uq_templates_template_id"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    template_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    style_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    scenario_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    supported_layout_modes: Mapped[list[str]] = mapped_column(JSON, default=list)
    density_range: Mapped[str] = mapped_column(String(32), nullable=False, default="medium")
    color_scheme: Mapped[list[str]] = mapped_column(JSON, default=list)
    design_spec_path: Mapped[str] = mapped_column(String(512), nullable=False)
    preview_image_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class ExportRecord(Base):
    __tablename__ = "exports"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id"), nullable=False, index=True)
    artifact_id: Mapped[str] = mapped_column(String(64), ForeignKey("slide_artifacts.id"), nullable=False, index=True)
    export_format: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    export_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    preview_pdf_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)