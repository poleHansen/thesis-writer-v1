from __future__ import annotations

import base64

from fastapi import HTTPException, status

from core_types import ContentBlock, ExtractedAsset, Outline, OutlineSection, PresentationBrief, Project, ProjectFile, SlidePlan, SlidePlanItem, SourceBundle, SourceChunk, TaskRun, UserIntent
from core_types.task.models import TaskRun
from core_types.enums import BundleStatus, FileUploadStatus, ParseStatus, ProjectStatus, ReviewStatus, TaskStatus, TaskType
from ingestion import DocumentNormalizer, IngestionParser

from app.models.project import CreateProjectRequest, GenerateBriefRequest, GenerateOutlineRequest, GenerateSlidePlanRequest, ParseProjectFilesRequest, RegisterProjectFileRequest
from app.models.project import UploadProjectFileRequest
from app.repositories.project_repository import SqlAlchemyProjectRepository
from app.services.file_storage import FileStorageService


class ProjectService:
    def __init__(self, repository: SqlAlchemyProjectRepository, storage_service: FileStorageService | None = None) -> None:
        self._repository = repository
        self._parser = IngestionParser()
        self._normalizer = DocumentNormalizer()
        self._storage_service = storage_service or FileStorageService("storage")

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
        if not project_files:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project has no files to analyze")

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

        brief = PresentationBrief(
            project_id=project_id,
            source_bundle_id=source_bundle.id,
            presentation_goal=self._build_presentation_goal(project, payload.user_intent_override),
            target_audience=payload.user_intent_override.audience if payload.user_intent_override and payload.user_intent_override.audience else "general audience",
            core_message=self._build_core_message(project, project_files),
            storyline=self._build_storyline(project_files),
            recommended_page_count=payload.user_intent_override.desired_page_count if payload.user_intent_override and payload.user_intent_override.desired_page_count else max(8, min(20, len(project_files) * 3)),
            tone="professional",
            style_preferences=payload.user_intent_override.style_preferences if payload.user_intent_override else [],
            risks=[] if payload.force_regenerate else ["brief is generated from file metadata only"],
            assumptions=["detailed parsing will be implemented in phase 2"],
            status=ReviewStatus.DRAFT,
            metadata={"generation_mode": "skeleton"},
        )
        self._repository.create_brief(brief)

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

        chapter_titles = self._derive_outline_titles(brief)
        chapter_count = max(3, min(len(chapter_titles), brief.recommended_page_count))
        chapters = [
            OutlineSection(
                section_id=f"section-{index + 1}",
                title=title,
                objective=f"Explain {title.lower()}",
                key_message=f"{title} supports the core message: {brief.core_message}",
                supporting_points=[
                    brief.presentation_goal,
                    brief.storyline,
                    f"Audience focus: {brief.target_audience}",
                ],
                estimated_slides=max(1, brief.recommended_page_count // chapter_count),
            )
            for index, title in enumerate(chapter_titles[:chapter_count])
        ]
        outline = Outline(
            project_id=project_id,
            brief_id=brief.id,
            title=f"{project.name} outline",
            chapters=chapters,
            summary=f"Outline generated from brief {brief.id} with {len(chapters)} chapters.",
            status=ReviewStatus.DRAFT,
            metadata={"generation_mode": "skeleton", "source": "brief"},
        )
        self._repository.create_outline(outline)
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

        slides = self._build_slide_plan_items(outline, brief)
        slide_plan = SlidePlan(
            project_id=project_id,
            brief_id=brief.id,
            outline_id=outline.id,
            page_count=len(slides),
            slides=slides,
            design_direction=payload.preferred_template_id or "auto-generated skeleton",
            status=ReviewStatus.DRAFT,
            metadata={"generation_mode": "skeleton", "source": "outline"},
        )
        self._repository.create_slide_plan(slide_plan)
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
            return "file_upload"
        if has_intent:
            return "chat_input"
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

    def _build_presentation_goal(self, project: Project, user_intent: UserIntent | None) -> str:
        if user_intent and user_intent.purpose:
            return user_intent.purpose
        return project.description or f"Generate a presentation for project {project.name}"

    def _build_core_message(self, project: Project, project_files: list[ProjectFile]) -> str:
        return f"{project.name} is synthesized from {len(project_files)} registered source files."

    def _build_storyline(self, project_files: list[ProjectFile]) -> str:
        return " -> ".join(project_file.file_name for project_file in project_files)

    def _derive_outline_titles(self, brief: PresentationBrief) -> list[str]:
        return [
            "Problem Context",
            "Research Scope",
            "Methodology",
            "Key Findings",
            "Conclusion and Next Steps",
        ]

    def _build_slide_plan_items(self, outline: Outline, brief: PresentationBrief) -> list[SlidePlanItem]:
        slides: list[SlidePlanItem] = []
        for index, chapter in enumerate(outline.chapters, start=1):
            bullets = chapter.supporting_points[:3] if chapter.supporting_points else [brief.core_message]
            slides.append(
                SlidePlanItem(
                    slide_id=f"slide-{index}",
                    slide_number=index,
                    title=chapter.title,
                    conclusion=chapter.key_message,
                    layout_mode="two_column",
                    content_blocks=[
                        ContentBlock(
                            block_id=f"slide-{index}-summary",
                            block_type="summary",
                            heading=chapter.objective,
                            body=chapter.key_message,
                            bullets=bullets,
                            asset_refs=[],
                            chart_hint=None,
                            emphasis="primary",
                        )
                    ],
                    speaker_notes=f"Focus on {chapter.objective.lower()} for {brief.target_audience}.",
                    data_refs=[],
                    visual_priority="medium",
                )
            )
        return slides
