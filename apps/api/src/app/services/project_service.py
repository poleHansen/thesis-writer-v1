from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status

from core_types import ExportJob, ExtractedAsset, Outline, OutlineSection, PresentationBrief, Project, ProjectFile, SlideArtifact, SlidePlan, SlidePlanItem, SourceBundle, SourceChunk, TaskRun, TemplateMeta, UserIntent
from core_types.task.models import TaskRun
from core_types.enums import BundleStatus, ExportStatus, FileUploadStatus, ParseStatus, ProjectStatus, RenderStatus, ReviewStatus, TaskStatus, TaskType
from ingestion import DocumentNormalizer, IngestionParser
from methodology_engine import BriefGenerator, OutlineGenerator, SlidePlanner
from app.services.llm_gateway import LlmGateway, LlmGatewayError, LlmGatewaySettings

from app.models.project import CreateProjectRequest, GenerateBriefRequest, GenerateExportRequest, GenerateOutlineRequest, GenerateSlideArtifactRequest, GenerateSlidePlanRequest, ParseProjectFilesRequest, ProjectLlmSettings, ProjectLlmSettingsUpdateRequest, RegisterProjectFileRequest, UpdateBriefRequest, UpdateOutlineRequest, UpdateSlidePlanRequest
from app.models.project import UploadProjectFileRequest
from app.repositories.project_repository import SqlAlchemyProjectRepository
from app.services.design_spec_builder import DesignSpecBuilder
from app.services.export_service import PdfExportService, PptxExportService
from app.services.file_storage import FileStorageService
from app.services.svg_finalizer import SvgFinalizer
from app.services.svg_renderer import SvgRenderResult, SvgRenderer
from app.services.svg_validator import SvgValidator
from app.services.template_registry import TemplateRegistryService


class ProjectService:
    def __init__(self, repository: SqlAlchemyProjectRepository, storage_service: FileStorageService | None = None) -> None:
        self._repository = repository
        self._parser = IngestionParser()
        self._normalizer = DocumentNormalizer()
        self._brief_generator = BriefGenerator()
        self._outline_generator = OutlineGenerator()
        self._slide_planner = SlidePlanner()
        self._template_registry = TemplateRegistryService()
        self._design_spec_builder = DesignSpecBuilder()
        self._svg_renderer = SvgRenderer()
        self._svg_finalizer = SvgFinalizer()
        self._svg_validator = SvgValidator()
        self._storage_service = storage_service or FileStorageService("storage")
        self._export_service = PptxExportService()
        self._pdf_export_service = PdfExportService()

    def get_project_llm_settings(self, project_id: str) -> ProjectLlmSettings:
        project = self.get_project(project_id)
        settings_payload = project.metadata.get("llm_settings") or {}
        if not settings_payload:
            return ProjectLlmSettings()
        masked_payload = {
            **settings_payload,
            "api_key": self._mask_secret(settings_payload.get("api_key", "")),
        }
        return ProjectLlmSettings.model_validate(masked_payload)

    def update_project_llm_settings(self, project_id: str, payload: ProjectLlmSettingsUpdateRequest) -> ProjectLlmSettings:
        project = self.get_project(project_id)
        stored_payload = payload.model_dump()
        updated_project = project.model_copy(
            update={
                "metadata": {
                    **project.metadata,
                    "llm_settings": stored_payload,
                }
            }
        )
        self._repository.update_project(updated_project)
        return self.get_project_llm_settings(project_id)

    def test_project_llm_settings(self, project_id: str) -> dict[str, object]:
        project = self.get_project(project_id)
        settings = self._load_project_llm_settings(project)
        gateway = LlmGateway(settings)
        try:
            result = gateway.test_connection()
        except LlmGatewayError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        return {
            "ok": bool(result.get("ok", True)),
            "provider": str(result.get("provider", settings.provider)),
            "model": str(result.get("model", settings.model)),
            "message": "LLM connection succeeded",
        }

    def create_project(self, payload: CreateProjectRequest) -> Project:
        project = Project(
            name=payload.name,
            description=payload.description,
            source_mode=payload.source_mode,
            tags=payload.tags,
            status=ProjectStatus.CREATED,
        )
        return self._repository.create_project(project)

    def get_project(self, project_id: str) -> Project:
        project = self._repository.get_project(project_id)
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return project

    def get_project_detail(self, project_id: str) -> dict[str, object]:
        detail = self._repository.get_project_detail(project_id)
        if detail is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return detail

    def get_project_status(self, project_id: str) -> tuple[Project, list[TaskRun]]:
        project = self.get_project(project_id)
        tasks = self._repository.list_project_tasks(project_id)
        return project, tasks

    def list_projects_dashboard(self) -> list[dict[str, object]]:
        return self._repository.list_project_dashboard()

    def list_project_exports(self, project_id: str, limit: int = 5) -> list[ExportJob]:
        self.get_project(project_id)
        return self._repository.list_project_exports(project_id, limit)

    def get_project_export(self, project_id: str, export_id: str) -> ExportJob:
        self.get_project(project_id)
        export_job = self._repository.get_project_export(project_id, export_id)
        if export_job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export job not found")
        return export_job

    def list_templates(self) -> list[TemplateMeta]:
        return self._template_registry.list_templates()

    def register_project_file(self, project_id: str, payload: RegisterProjectFileRequest) -> ProjectFile:
        self.get_project(project_id)
        project_file = ProjectFile(
            project_id=project_id,
            file_name=payload.file_name,
            file_type=payload.file_type,
            storage_path=payload.storage_path,
            mime_type=payload.mime_type,
            size_bytes=payload.size_bytes,
            checksum=payload.checksum,
            upload_status=FileUploadStatus.UPLOADED,
            parse_status=ParseStatus.PENDING,
            extracted_summary=payload.extracted_summary,
            metadata=payload.metadata,
        )
        return self._repository.create_project_file(project_file)

    def upload_project_file(self, project_id: str, payload: UploadProjectFileRequest) -> ProjectFile:
        self.get_project(project_id)
        try:
            content = base64.b64decode(payload.content_base64)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid base64 payload: {exc}") from exc

        storage_path, checksum, size_bytes = self._storage_service.save_project_file(project_id, payload.file_name, content)
        project_file = ProjectFile(
            project_id=project_id,
            file_name=payload.file_name,
            file_type=payload.file_type,
            storage_path=storage_path,
            mime_type=payload.mime_type,
            size_bytes=size_bytes,
            checksum=checksum,
            upload_status=FileUploadStatus.UPLOADED,
            parse_status=ParseStatus.PENDING,
            metadata={**payload.metadata, "storage_mode": "managed_upload"},
        )
        return self._repository.create_project_file(project_file)

    def list_project_files(self, project_id: str) -> list[ProjectFile]:
        self.get_project(project_id)
        return self._repository.list_project_files(project_id)

    def parse_project_files(self, project_id: str, payload: ParseProjectFilesRequest) -> tuple[list[ProjectFile], SourceBundle | None, TaskRun]:
        project = self.get_project(project_id)
        project_files = self._repository.list_project_files(project_id)
        if payload.file_ids:
            selected_ids = set(payload.file_ids)
            project_files = [project_file for project_file in project_files if project_file.id in selected_ids]
        if not project_files:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project has no files to parse")

        parsed_files: list[ProjectFile] = []
        raw_sections: list[str] = []
        page_chunks: list[SourceChunk] = []
        images: list[ExtractedAsset] = []
        tables: list[ExtractedAsset] = []
        warnings_by_file: dict[str, list[str]] = {}
        parsed_documents = []

        for project_file in project_files:
            try:
                parsed = self._parser.parse_file(project_file.storage_path, project_file.file_type)
                updated_file = project_file.model_copy(
                    update={
                        "parse_status": ParseStatus.SUCCEEDED,
                        "parse_error": None,
                        "extracted_summary": parsed.page_chunks[0][:240] if parsed.page_chunks else (parsed.raw_text[:240] if parsed.raw_text else None),
                        "metadata": {
                            **project_file.metadata,
                            "parse_warnings": parsed.warnings,
                            "page_chunk_count": len(parsed.page_chunks),
                        },
                    }
                )
                self._repository.update_project_file(updated_file)
                parsed_files.append(updated_file)
                parsed_documents.append(parsed)
                raw_sections.append(f"# {project_file.file_name}\n\n{parsed.markdown}")
                page_chunks.extend(
                    SourceChunk(
                        chunk_id=f"{project_file.id}-chunk-{index + 1}",
                        page_number=index + 1,
                        heading_path=[project_file.file_name],
                        content=chunk,
                        token_count=len(chunk.split()),
                        chunk_type="paragraph",
                    )
                    for index, chunk in enumerate(parsed.page_chunks)
                )
                images.extend(
                    ExtractedAsset(
                        asset_id=image.asset_id,
                        asset_type="image",
                        source_file_id=project_file.id,
                        title=image.title,
                        description=image.description,
                        storage_path=image.source_path,
                    )
                    for image in parsed.images
                )
                tables.extend(
                    ExtractedAsset(
                        asset_id=table.asset_id,
                        asset_type="table",
                        source_file_id=project_file.id,
                        title=table.title,
                        description=table.markdown,
                    )
                    for table in parsed.tables
                )
                if parsed.warnings:
                    warnings_by_file[project_file.id] = parsed.warnings
            except Exception as exc:
                failed_file = project_file.model_copy(
                    update={
                        "parse_status": ParseStatus.FAILED,
                        "parse_error": str(exc),
                        "metadata": {**project_file.metadata},
                    }
                )
                self._repository.update_project_file(failed_file)
                parsed_files.append(failed_file)

        source_bundle: SourceBundle | None = None
        if payload.rebuild_bundle:
            successful_files = [project_file for project_file in parsed_files if project_file.parse_status == ParseStatus.SUCCEEDED]
            if successful_files or payload.user_intent:
                source_bundle = self._build_source_bundle_from_inputs(
                    project=project,
                    project_files=successful_files,
                    raw_sections=raw_sections,
                    page_chunks=page_chunks,
                    images=images,
                    tables=tables,
                    parsed_documents=parsed_documents,
                    user_intent=payload.user_intent,
                    warnings_by_file=warnings_by_file,
                    generated_from="parser",
                )
                self._repository.create_source_bundle(source_bundle)
                self._repository.update_project_links(
                    project_id,
                    latest_source_bundle_id=source_bundle.id,
                    status=ProjectStatus.PARSED if source_bundle.status == BundleStatus.READY else ProjectStatus.ANALYZED,
                )

        succeeded_count = len([project_file for project_file in parsed_files if project_file.parse_status == ParseStatus.SUCCEEDED])
        failed_count = len([project_file for project_file in parsed_files if project_file.parse_status == ParseStatus.FAILED])
        if failed_count > 0 and succeeded_count == 0:
            self._repository.update_project_links(
                project_id,
                status=ProjectStatus.PARSE_FAILED,
            )
        task_run = TaskRun(
            project_id=project_id,
            task_type=TaskType.PARSE,
            task_status=TaskStatus.SUCCEEDED if failed_count == 0 else TaskStatus.FAILED,
            result={
                "parsed_file_count": succeeded_count,
                "failed_file_count": failed_count,
                "source_bundle_id": source_bundle.id if source_bundle else None,
            },
            error_message=None if failed_count == 0 else "Some files failed during parsing",
        )
        self._repository.create_task_run(task_run)
        return parsed_files, source_bundle, task_run

    def generate_brief(self, project_id: str, payload: GenerateBriefRequest) -> tuple[SourceBundle, PresentationBrief, TaskRun]:
        project = self.get_project(project_id)
        project_files = self._repository.list_project_files(project_id)
        latest_source_bundle = self._repository.get_latest_source_bundle(project_id)
        effective_user_intent = payload.user_intent_override
        if latest_source_bundle is not None and not payload.force_regenerate:
            source_bundle = latest_source_bundle
        else:
            if not project_files and not payload.user_intent_override:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project has no files or user intent to analyze")
            source_bundle = self._build_source_bundle_from_inputs(
            project=project,
            project_files=project_files,
            raw_sections=[self._build_raw_markdown(project_files)] if project_files else [],
            page_chunks=[],
            images=[],
            tables=[],
            parsed_documents=[],
            user_intent=payload.user_intent_override,
            warnings_by_file={},
            generated_from="project_files",
        )
            self._repository.create_source_bundle(source_bundle)
        if effective_user_intent is None:
            effective_user_intent = source_bundle.user_intent

        brief = self._generate_brief(project, source_bundle, project_files, effective_user_intent, payload.force_regenerate)
        self._repository.create_brief(brief)
        self._persist_project_artifact(project_id, "brief.json", brief)

        updated_project = self._repository.update_project_links(
            project_id,
            latest_source_bundle_id=source_bundle.id,
            latest_brief_id=brief.id,
            status=ProjectStatus.BRIEFING,
        )

        task_run = TaskRun(
            project_id=project_id,
            task_type=TaskType.GENERATE_BRIEF,
            task_status=TaskStatus.SUCCEEDED,
            result={
                "source_bundle_id": source_bundle.id,
                "brief_id": brief.id,
                "project_status": (updated_project.status if updated_project else ProjectStatus.BRIEFING),
            },
        )
        self._repository.create_task_run(task_run)
        return source_bundle, brief, task_run

    def generate_outline(self, project_id: str, payload: GenerateOutlineRequest) -> tuple[Outline, TaskRun]:
        project = self.get_project(project_id)
        brief = self._repository.get_brief(payload.brief_id) if payload.brief_id else self._repository.get_latest_brief(project_id)
        if brief is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project has no brief to outline")

        source_bundle = self._repository.get_source_bundle(brief.source_bundle_id)
        outline = self._generate_outline(project, brief, source_bundle)
        self._repository.create_outline(outline)
        self._persist_project_artifact(project_id, "outline.json", outline)
        updated_project = self._repository.update_project_links(
            project_id,
            latest_outline_id=outline.id,
            status=ProjectStatus.OUTLINED,
        )

        task_run = TaskRun(
            project_id=project_id,
            task_type=TaskType.GENERATE_OUTLINE,
            task_status=TaskStatus.SUCCEEDED,
            result={
                "outline_id": outline.id,
                "brief_id": brief.id,
                "project_status": (updated_project.status if updated_project else ProjectStatus.OUTLINED),
            },
        )
        self._repository.create_task_run(task_run)
        return outline, task_run

    def generate_slide_plan(self, project_id: str, payload: GenerateSlidePlanRequest) -> tuple[SlidePlan, TaskRun]:
        project = self.get_project(project_id)
        outline = self._repository.get_outline(payload.outline_id) if payload.outline_id else self._repository.get_latest_outline(project_id)
        if outline is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project has no outline to plan")

        brief = self._repository.get_brief(outline.brief_id)
        if brief is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Outline has no linked brief")

        slide_plan = self._generate_slide_plan(project, brief, outline, payload.preferred_template_id)
        self._repository.create_slide_plan(slide_plan)
        self._persist_project_artifact(project_id, "slide-plan.json", slide_plan)
        updated_project = self._repository.update_project_links(
            project_id,
            latest_slide_plan_id=slide_plan.id,
            status=ProjectStatus.PLANNED,
        )

        task_run = TaskRun(
            project_id=project_id,
            task_type=TaskType.GENERATE_SLIDE_PLAN,
            task_status=TaskStatus.SUCCEEDED,
            result={
                "slide_plan_id": slide_plan.id,
                "outline_id": outline.id,
                "brief_id": brief.id,
                "project_status": (updated_project.status if updated_project else ProjectStatus.PLANNED),
            },
        )
        self._repository.create_task_run(task_run)
        return slide_plan, task_run

    def generate_slide_artifact(self, project_id: str, payload: GenerateSlideArtifactRequest) -> tuple[SlideArtifact, TaskRun]:
        project = self.get_project(project_id)
        slide_plan = self._repository.get_slide_plan(payload.slide_plan_id) if payload.slide_plan_id else self._repository.get_latest_slide_plan(project_id)
        if slide_plan is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project has no slide plan to render")

        try:
            template = self._template_registry.resolve_template(payload.template_id, slide_plan)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        artifact = SlideArtifact(
            project_id=project_id,
            slide_plan_id=slide_plan.id,
            template_id=template.id,
            svg_output_dir="",
            svg_final_dir="",
            render_status=RenderStatus.PENDING,
            metadata={
                "generated_from": "slide_plan",
                "page_count": slide_plan.page_count,
                "design_direction": slide_plan.design_direction,
                "slide_titles": [slide.title for slide in slide_plan.slides],
                "render_mode": "placeholder",
                "template_id": template.template_id,
                "template_name": template.name,
            },
        )
        svg_output_dir, svg_final_dir = self._storage_service.ensure_render_directories(project_id, artifact.id)
        design_spec = self._design_spec_builder.build(project=project, slide_plan=slide_plan, template=template)
        design_spec_path = self._storage_service.save_render_context(project_id, artifact.id, "design-spec.json", design_spec)
        render_result = self._render_svg_pages(project_id=project_id, artifact_id=artifact.id, slide_plan=slide_plan, template=template, svg_output_dir=svg_output_dir, svg_final_dir=svg_final_dir)
        artifact.svg_output_dir = svg_output_dir
        artifact.svg_final_dir = svg_final_dir
        artifact.preview_image_paths = render_result.generated_files
        artifact.render_status = render_result.render_status
        artifact.failed_slide_ids = render_result.failed_slide_ids
        artifact.log_path = render_result.log_path
        artifact.metadata["design_spec_path"] = design_spec_path
        artifact.metadata["render_mode"] = "builtin_svg_v1"
        artifact.metadata["generated_svg_files"] = render_result.generated_files
        artifact.metadata["validation_summary"] = render_result.validation_summary
        artifact.metadata["finalization_summary"] = render_result.validation_summary.get("finalization_summary", {})
        self._repository.create_slide_artifact(artifact)
        self._persist_project_artifact(project_id, "slide-artifact.json", artifact)
        updated_project = self._repository.update_project_links(
            project_id,
            latest_slide_plan_id=slide_plan.id,
            latest_artifact_id=artifact.id,
            status=ProjectStatus.FINALIZED if render_result.render_status == RenderStatus.SUCCEEDED else ProjectStatus.RENDERING,
        )

        task_run = TaskRun(
            project_id=project_id,
            task_type=TaskType.RENDER,
            task_status=TaskStatus.SUCCEEDED,
            result={
                "artifact_id": artifact.id,
                "slide_plan_id": slide_plan.id,
                "project_status": (updated_project.status if updated_project else ProjectStatus.RENDERING),
                "svg_output_dir": svg_output_dir,
                "svg_final_dir": svg_final_dir,
                "design_spec_path": design_spec_path,
                "template_id": template.template_id,
                "generated_svg_files": render_result.generated_files,
                "failed_slide_ids": render_result.failed_slide_ids,
                "validation_summary": render_result.validation_summary,
            },
        )
        self._repository.create_task_run(task_run)
        return artifact, task_run

    def generate_export(self, project_id: str, payload: GenerateExportRequest) -> tuple[ExportJob, TaskRun]:
        self.get_project(project_id)
        export_format = payload.export_format.value if hasattr(payload.export_format, "value") else str(payload.export_format)
        artifact = self._repository.get_slide_artifact(payload.artifact_id) if payload.artifact_id else None
        if artifact is None:
            detail = self._repository.get_project_detail(project_id)
            artifact = None if detail is None else detail.get("latest_artifact")
        export_job = ExportJob(
            project_id=project_id,
            artifact_id=artifact.id if artifact is not None else (payload.artifact_id or "unknown-artifact"),
            run_id=f"run-{uuid4().hex}",
            export_format=export_format,
            status=ExportStatus.PENDING,
            metadata={},
        )
        if artifact is None:
            return self._fail_export(export_job, "Project has no rendered artifact to export")
        export_job.artifact_id = artifact.id
        export_job.metadata = {"source_svg_final_dir": artifact.svg_final_dir}
        if not artifact.svg_final_dir:
            return self._fail_export(export_job, "Artifact is missing svg_final output")
        if artifact.render_status not in {RenderStatus.SUCCEEDED, RenderStatus.PARTIAL}:
            return self._fail_export(export_job, "Artifact finalize is incomplete; export is unavailable")

        final_svg_files = sorted(Path(artifact.svg_final_dir).glob("slide-*.svg"))
        if not final_svg_files:
            return self._fail_export(export_job, "Artifact has no finalized SVG pages to export")

        export_file_name = f"{artifact.id}-{export_job.run_id}.{export_format}"
        export_path = self._storage_service.build_export_path(project_id, artifact.id, export_job.run_id, export_file_name)
        if export_format == "pdf":
            export_metadata = self._pdf_export_service.export_svg_pages_to_pdf(
                svg_paths=final_svg_files,
                target_path=export_path,
            )
            export_job.preview_pdf_path = export_path
            export_job.metadata = {
                "source_svg_final_dir": artifact.svg_final_dir,
                "export_kind": "pdf_preview_from_svg_pages",
                **export_metadata,
            }
        else:
            export_metadata = self._export_service.export_svg_pages_to_pptx(
                svg_paths=final_svg_files,
                target_path=export_path,
            )
            export_job.export_path = export_path
            export_job.metadata = {
                "source_svg_final_dir": artifact.svg_final_dir,
                "export_kind": "pptx_from_svg_pages",
                **export_metadata,
            }

        if export_format != "pdf":
            export_job.export_path = export_path
        else:
            export_job.export_path = export_path
        archive_manifest_path = self._storage_service.save_export_context(
            project_id,
            artifact.id,
            export_job.run_id,
            "archive-manifest.json",
            {
                "project_id": project_id,
                "artifact_id": artifact.id,
                "export_id": export_job.id,
                "run_id": export_job.run_id,
                "export_format": export_format,
                "export_path": export_path,
                "preview_pdf_path": export_job.preview_pdf_path,
                "source_svg_final_dir": artifact.svg_final_dir,
                "source_files": [str(path) for path in final_svg_files],
                "artifacts": {
                    "slide_artifact": self._storage_service.save_project_artifact(
                        project_id,
                        "slide-artifact.json",
                        artifact.model_dump(mode="json"),
                    ),
                    "export_output": export_path,
                },
                "metadata": export_job.metadata,
            },
        )
        export_log_path = self._storage_service.save_export_context(
            project_id,
            artifact.id,
            export_job.run_id,
            "export-log.json",
            {
                "project_id": project_id,
                "artifact_id": artifact.id,
                "export_id": export_job.id,
                "run_id": export_job.run_id,
                "status": "succeeded",
                "export_format": export_format,
                "archive_manifest_path": archive_manifest_path,
                "export_path": export_path,
                "preview_pdf_path": export_job.preview_pdf_path,
            },
        )
        export_job.metadata = {
            **export_job.metadata,
            "run_id": export_job.run_id,
            "archive_manifest_path": archive_manifest_path,
            "export_log_path": export_log_path,
        }
        export_job.status = ExportStatus.SUCCEEDED
        self._repository.create_export_job(export_job)
        updated_project = self._repository.update_project_links(
            project_id,
            latest_artifact_id=artifact.id,
            status=ProjectStatus.EXPORTED,
        )
        task_run = TaskRun(
            project_id=project_id,
            task_type=TaskType.EXPORT,
            task_status=TaskStatus.SUCCEEDED,
            result={
                "artifact_id": artifact.id,
                "export_id": export_job.id,
                "run_id": export_job.run_id,
                "export_format": export_format,
                "export_path": export_path,
                "preview_pdf_path": export_job.preview_pdf_path,
                "archive_manifest_path": archive_manifest_path,
                "export_log_path": export_log_path,
                "project_status": (updated_project.status if updated_project else ProjectStatus.EXPORTED),
            },
        )
        self._repository.create_task_run(task_run)
        return export_job, task_run

    def _fail_export(self, export_job: ExportJob, error_message: str) -> tuple[ExportJob, TaskRun]:
        export_job.status = ExportStatus.FAILED
        export_job.error_message = error_message
        self._repository.create_export_job(export_job)
        updated_project = self._repository.update_project_links(
            export_job.project_id,
            status=ProjectStatus.EXPORT_FAILED,
        )
        task_run = TaskRun(
            project_id=export_job.project_id,
            task_type=TaskType.EXPORT,
            task_status=TaskStatus.FAILED,
            result={
                "artifact_id": export_job.artifact_id,
                "export_id": export_job.id,
                "run_id": export_job.run_id,
                "export_format": export_job.export_format,
                "project_status": (updated_project.status if updated_project else ProjectStatus.EXPORT_FAILED),
            },
            error_message=error_message,
        )
        self._repository.create_task_run(task_run)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)

    def _render_svg_pages(self, project_id: str, artifact_id: str, slide_plan: SlidePlan, template: TemplateMeta, svg_output_dir: str, svg_final_dir: str) -> SvgRenderResult:
        render_result = self._svg_renderer.render(slide_plan=slide_plan, template=template)
        generated_output_files: list[str] = []
        generated_final_files: list[str] = []
        validation_results: list[dict[str, object]] = []
        rendered_pages: list[tuple[str, str]] = []
        for page in render_result.pages:
            file_name = f"slide-{page.slide_number:02d}.svg"
            generated_output_files.append(self._storage_service.save_svg_page(svg_output_dir, file_name, page.svg_content))
            rendered_pages.append((file_name, page.svg_content))

        finalize_result = self._svg_finalizer.finalize_pages(rendered_pages)
        for finalized_page in finalize_result.pages:
            final_path = self._storage_service.save_svg_page(svg_final_dir, finalized_page.final_file_name, finalized_page.final_svg_content)
            generated_final_files.append(final_path)
            validation = self._svg_validator.validate_file(final_path, finalized_page.final_svg_content)
            validation_results.append(
                {
                    "file_path": validation.file_path,
                    "is_valid": validation.is_valid,
                    "issues": validation.issues,
                    "finalizer_steps": finalized_page.applied_steps,
                }
            )
        log_payload = {
            "render_status": render_result.render_status,
            "generated_output_files": generated_output_files,
            "generated_files": generated_final_files,
            "failed_slide_ids": render_result.failed_slide_ids,
            "render_errors": render_result.render_errors,
            "finalization_summary": finalize_result.summary,
            "validation_results": validation_results,
        }
        log_path = self._storage_service.save_render_context(
            project_id,
            artifact_id,
            "render-log.json",
            log_payload,
        )
        validation_summary = {
            "checked_file_count": len(validation_results),
            "valid_file_count": sum(1 for item in validation_results if item["is_valid"]),
            "invalid_file_count": sum(1 for item in validation_results if not item["is_valid"]),
            "finalization_summary": finalize_result.summary,
        }
        return render_result.model_copy(update={"generated_files": generated_final_files, "log_path": log_path, "validation_summary": validation_summary})

    def update_brief(self, project_id: str, payload: UpdateBriefRequest) -> PresentationBrief:
        self.get_project(project_id)
        brief = self._repository.get_brief(payload.brief_id) if payload.brief_id else self._repository.get_latest_brief(project_id)
        if brief is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project has no brief to edit")
        updated_brief = brief.model_copy(
            update={
                "presentation_goal": payload.presentation_goal if payload.presentation_goal is not None else brief.presentation_goal,
                "target_audience": payload.target_audience if payload.target_audience is not None else brief.target_audience,
                "core_message": payload.core_message if payload.core_message is not None else brief.core_message,
                "storyline": payload.storyline if payload.storyline is not None else brief.storyline,
                "recommended_page_count": payload.recommended_page_count if payload.recommended_page_count is not None else brief.recommended_page_count,
                "tone": payload.tone if payload.tone is not None else brief.tone,
                "style_preferences": payload.style_preferences if payload.style_preferences is not None else brief.style_preferences,
                "risks": payload.risks if payload.risks is not None else brief.risks,
                "assumptions": payload.assumptions if payload.assumptions is not None else brief.assumptions,
                "metadata": {**brief.metadata, **(payload.metadata or {}), "last_edited_by": "manual_review"},
            }
        )
        persisted_brief = self._repository.update_brief(updated_brief)
        self._persist_project_artifact(project_id, "brief.json", persisted_brief)
        return persisted_brief

    def update_outline(self, project_id: str, payload: UpdateOutlineRequest) -> Outline:
        self.get_project(project_id)
        outline = self._repository.get_outline(payload.outline_id) if payload.outline_id else self._repository.get_latest_outline(project_id)
        if outline is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project has no outline to edit")
        chapters = [OutlineSection.model_validate(chapter) for chapter in payload.chapters] if payload.chapters is not None else outline.chapters
        updated_outline = outline.model_copy(
            update={
                "title": payload.title if payload.title is not None else outline.title,
                "chapters": chapters,
                "summary": payload.summary if payload.summary is not None else outline.summary,
                "metadata": {**outline.metadata, **(payload.metadata or {}), "last_edited_by": "manual_review"},
            }
        )
        persisted_outline = self._repository.update_outline(updated_outline)
        self._persist_project_artifact(project_id, "outline.json", persisted_outline)
        return persisted_outline

    def update_slide_plan(self, project_id: str, payload: UpdateSlidePlanRequest) -> SlidePlan:
        self.get_project(project_id)
        slide_plan = self._repository.get_slide_plan(payload.slide_plan_id) if payload.slide_plan_id else self._repository.get_latest_slide_plan(project_id)
        if slide_plan is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project has no slide plan to edit")
        slides = [SlidePlanItem.model_validate(slide) for slide in payload.slides] if payload.slides is not None else slide_plan.slides
        updated_slide_plan = slide_plan.model_copy(
            update={
                "page_count": payload.page_count if payload.page_count is not None else len(slides),
                "slides": slides,
                "design_direction": payload.design_direction if payload.design_direction is not None else slide_plan.design_direction,
                "metadata": {**slide_plan.metadata, **(payload.metadata or {}), "last_edited_by": "manual_review"},
            }
        )
        persisted_slide_plan = self._repository.update_slide_plan(updated_slide_plan)
        self._persist_project_artifact(project_id, "slide-plan.json", persisted_slide_plan)
        return persisted_slide_plan

    def _persist_project_artifact(self, project_id: str, artifact_name: str, model: Any) -> str:
        if hasattr(model, "model_dump"):
            payload = model.model_dump(mode="json")
        else:
            payload = model
        return self._storage_service.save_project_artifact(project_id, artifact_name, payload)

    def _build_raw_markdown(self, project_files: list[ProjectFile]) -> str:
        return "\n\n".join(f"# {project_file.file_name}\n\n{project_file.extracted_summary or 'Pending source parsing.'}" for project_file in project_files)

    def _build_normalized_markdown(self, project_files: list[ProjectFile], user_intent: UserIntent | None) -> str:
        lines = [f"- {project_file.file_name}: {project_file.extracted_summary or 'Pending source parsing.'}" for project_file in project_files]
        if user_intent and user_intent.purpose:
            lines.insert(0, f"Purpose: {user_intent.purpose}")
        return "\n".join(lines)

    def _build_source_bundle_from_inputs(
        self,
        *,
        project: Project,
        project_files: list[ProjectFile],
        raw_sections: list[str],
        page_chunks: list[SourceChunk],
        images: list[ExtractedAsset],
        tables: list[ExtractedAsset],
        parsed_documents: list[object],
        user_intent: UserIntent | None,
        warnings_by_file: dict[str, list[str]],
        generated_from: str,
    ) -> SourceBundle:
        has_files = bool(project_files)
        has_intent = user_intent is not None
        effective_mode = self._resolve_source_mode(has_files=has_files, has_intent=has_intent, fallback_mode=project.source_mode)

        raw_markdown: str | None = None
        normalized_markdown: str | None = None
        deduplicated_sections: list[str] = []
        removed_sections: list[str] = []

        if has_files:
            raw_markdown = "\n\n".join(section for section in raw_sections if section.strip())
            if parsed_documents:
                normalized = self._normalizer.normalize_documents(parsed_documents)
                normalized_markdown = normalized.normalized_markdown
                deduplicated_sections = normalized.deduplicated_sections
                removed_sections = normalized.removed_sections
            else:
                normalized_markdown = self._build_normalized_markdown(
                    project_files,
                    user_intent if effective_mode == "mixed" else None,
                )
        elif has_intent:
            normalized_markdown = self._build_intent_markdown(user_intent)

        return SourceBundle(
            project_id=project.id,
            source_file_ids=[project_file.id for project_file in project_files] if has_files else [],
            source_mode=effective_mode,
            user_intent=user_intent if has_intent else None,
            raw_markdown=raw_markdown if has_files else None,
            normalized_markdown=normalized_markdown,
            page_chunks=page_chunks if has_files else [],
            tables=tables if has_files else [],
            images=images if has_files else [],
            citations=[project_file.file_name for project_file in project_files] if has_files else [],
            status=BundleStatus.NEEDS_REVIEW if warnings_by_file else BundleStatus.READY,
            metadata={
                "generated_from": generated_from,
                "effective_source_mode": effective_mode,
                "input_summary": {
                    "has_files": has_files,
                    "has_user_intent": has_intent,
                    "file_count": len(project_files),
                },
                "warnings_by_file": warnings_by_file,
                "deduplicated_sections": deduplicated_sections,
                "removed_sections": removed_sections,
            },
        )

    def _resolve_source_mode(self, *, has_files: bool, has_intent: bool, fallback_mode: str) -> str:
        if has_files and has_intent:
            return "mixed"
        if has_files:
            return "file"
        if has_intent:
            return "chat"
        return fallback_mode

    def _build_intent_markdown(self, user_intent: UserIntent) -> str:
        lines: list[str] = []
        if user_intent.purpose:
            lines.append(f"# Purpose\n\n{user_intent.purpose}")
        if user_intent.audience:
            lines.append(f"# Audience\n\n{user_intent.audience}")
        if user_intent.scenario:
            lines.append(f"# Scenario\n\n{user_intent.scenario}")
        if user_intent.style_preferences:
            lines.append("# Style Preferences\n\n" + "\n".join(f"- {item}" for item in user_intent.style_preferences))
        if user_intent.emphasize_points:
            lines.append("# Emphasize Points\n\n" + "\n".join(f"- {item}" for item in user_intent.emphasize_points))
        if user_intent.constraints:
            lines.append("# Constraints\n\n" + "\n".join(f"- {item}" for item in user_intent.constraints))
        if user_intent.desired_page_count:
            lines.append(f"# Desired Page Count\n\n{user_intent.desired_page_count}")
        return "\n\n".join(lines)

    def _load_project_llm_settings(self, project: Project) -> LlmGatewaySettings:
        settings_payload = project.metadata.get("llm_settings") or {}
        if not settings_payload or not settings_payload.get("enabled"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project LLM settings are not configured")
        return LlmGatewaySettings.model_validate(settings_payload)

    def _mask_secret(self, value: str) -> str:
        if not value:
            return ""
        if len(value) <= 8:
            return "*" * len(value)
        return f"{value[:4]}{'*' * max(4, len(value) - 8)}{value[-4:]}"

    def _generate_brief(
        self,
        project: Project,
        source_bundle: SourceBundle,
        project_files: list[ProjectFile],
        user_intent: UserIntent | None,
        force_regenerate: bool,
    ) -> PresentationBrief:
        try:
            settings = self._load_project_llm_settings(project)
        except HTTPException:
            return self._brief_generator.generate(
                project=project,
                source_bundle=source_bundle,
                project_files=project_files,
                user_intent=user_intent,
                force_regenerate=force_regenerate,
            )

        gateway = LlmGateway(settings)
        prompt = self._build_brief_prompt(project, source_bundle, user_intent)
        try:
            payload = gateway.generate_json(
                system_prompt="You create concise, production-ready presentation briefs in Chinese. Return JSON only.",
                user_prompt=prompt,
                response_schema={
                    "type": "object",
                    "properties": {
                        "presentation_goal": {"type": "string"},
                        "target_audience": {"type": "string"},
                        "core_message": {"type": "string"},
                        "storyline": {"type": "string"},
                        "recommended_page_count": {"type": "integer"},
                        "tone": {"type": "string"},
                        "style_preferences": {"type": "array", "items": {"type": "string"}},
                        "risks": {"type": "array", "items": {"type": "string"}},
                        "assumptions": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["presentation_goal", "target_audience", "core_message", "storyline", "recommended_page_count", "tone", "style_preferences", "risks", "assumptions"],
                },
            )
        except LlmGatewayError:
            return self._brief_generator.generate(
                project=project,
                source_bundle=source_bundle,
                project_files=project_files,
                user_intent=user_intent,
                force_regenerate=force_regenerate,
            )

        return PresentationBrief(
            project_id=project.id,
            source_bundle_id=source_bundle.id,
            presentation_goal=str(payload["presentation_goal"]),
            target_audience=str(payload["target_audience"]),
            core_message=str(payload["core_message"]),
            storyline=str(payload["storyline"]),
            recommended_page_count=int(payload["recommended_page_count"]),
            tone=str(payload["tone"]),
            style_preferences=[str(item) for item in payload.get("style_preferences", [])],
            risks=[str(item) for item in payload.get("risks", [])],
            assumptions=[str(item) for item in payload.get("assumptions", [])],
            metadata={"generation_mode": "llm", "provider": settings.provider, "model": settings.model},
        )

    def _generate_outline(self, project: Project, brief: PresentationBrief, source_bundle: SourceBundle | None) -> Outline:
        try:
            settings = self._load_project_llm_settings(project)
        except HTTPException:
            return self._outline_generator.generate(project=project, brief=brief, source_bundle=source_bundle)

        gateway = LlmGateway(settings)
        prompt = self._build_outline_prompt(project, brief, source_bundle)
        try:
            payload = gateway.generate_json(
                system_prompt="You create structured presentation outlines in Chinese. Return JSON only.",
                user_prompt=prompt,
                response_schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "summary": {"type": "string"},
                        "chapters": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "section_id": {"type": "string"},
                                    "title": {"type": "string"},
                                    "objective": {"type": "string"},
                                    "key_message": {"type": "string"},
                                    "supporting_points": {"type": "array", "items": {"type": "string"}},
                                    "estimated_slides": {"type": "integer"},
                                },
                                "required": ["section_id", "title", "objective", "key_message", "supporting_points", "estimated_slides"],
                            },
                        },
                    },
                    "required": ["title", "summary", "chapters"],
                },
            )
        except LlmGatewayError:
            return self._outline_generator.generate(project=project, brief=brief, source_bundle=source_bundle)

        return Outline(
            project_id=project.id,
            brief_id=brief.id,
            title=str(payload["title"]),
            summary=str(payload.get("summary") or ""),
            chapters=[OutlineSection.model_validate(chapter) for chapter in payload.get("chapters", [])],
            metadata={"generation_mode": "llm", "provider": settings.provider, "model": settings.model},
        )

    def _generate_slide_plan(self, project: Project, brief: PresentationBrief, outline: Outline, preferred_template_id: str | None) -> SlidePlan:
        try:
            settings = self._load_project_llm_settings(project)
        except HTTPException:
            return self._slide_planner.generate(
                project_id=project.id,
                brief=brief,
                outline=outline,
                preferred_template_id=preferred_template_id,
            )

        gateway = LlmGateway(settings)
        prompt = self._build_slide_plan_prompt(project, brief, outline, preferred_template_id)
        try:
            payload = gateway.generate_json(
                system_prompt="You create slide-by-slide presentation plans in Chinese. Return JSON only.",
                user_prompt=prompt,
                response_schema={
                    "type": "object",
                    "properties": {
                        "page_count": {"type": "integer"},
                        "design_direction": {"type": "string"},
                        "slides": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "slide_id": {"type": "string"},
                                    "slide_number": {"type": "integer"},
                                    "title": {"type": "string"},
                                    "conclusion": {"type": "string"},
                                    "layout_mode": {"type": "string"},
                                    "content_blocks": {"type": "array", "items": {"type": "object"}},
                                    "speaker_notes": {"type": ["string", "null"]},
                                    "data_refs": {"type": "array", "items": {"type": "string"}},
                                    "visual_priority": {"type": ["string", "null"]},
                                },
                                "required": ["slide_id", "slide_number", "title", "conclusion", "layout_mode", "content_blocks", "data_refs"],
                            },
                        },
                    },
                    "required": ["page_count", "design_direction", "slides"],
                },
            )
        except LlmGatewayError:
            return self._slide_planner.generate(
                project_id=project.id,
                brief=brief,
                outline=outline,
                preferred_template_id=preferred_template_id,
            )

        return SlidePlan(
            project_id=project.id,
            brief_id=brief.id,
            outline_id=outline.id,
            page_count=int(payload["page_count"]),
            design_direction=str(payload.get("design_direction") or ""),
            slides=[SlidePlanItem.model_validate(slide) for slide in payload.get("slides", [])],
            metadata={"generation_mode": "llm", "provider": settings.provider, "model": settings.model, "preferred_template_id": preferred_template_id},
        )

    def _build_brief_prompt(self, project: Project, source_bundle: SourceBundle, user_intent: UserIntent | None) -> str:
        return json.dumps(
            {
                "project": project.model_dump(mode="json"),
                "source_bundle": source_bundle.model_dump(mode="json"),
                "user_intent": user_intent.model_dump(mode="json") if user_intent else None,
                "task": "Generate a concise presentation brief for an AI PPT workflow.",
            },
            ensure_ascii=False,
        )

    def _build_outline_prompt(self, project: Project, brief: PresentationBrief, source_bundle: SourceBundle | None) -> str:
        return json.dumps(
            {
                "project": project.model_dump(mode="json"),
                "brief": brief.model_dump(mode="json"),
                "source_bundle": source_bundle.model_dump(mode="json") if source_bundle else None,
                "task": "Generate a presentation outline with chapters, objectives, and key messages.",
            },
            ensure_ascii=False,
        )

    def _build_slide_plan_prompt(self, project: Project, brief: PresentationBrief, outline: Outline, preferred_template_id: str | None) -> str:
        return json.dumps(
            {
                "project": project.model_dump(mode="json"),
                "brief": brief.model_dump(mode="json"),
                "outline": outline.model_dump(mode="json"),
                "preferred_template_id": preferred_template_id,
                "task": "Generate a page-by-page slide plan with layout mode and content blocks.",
            },
            ensure_ascii=False,
        )

