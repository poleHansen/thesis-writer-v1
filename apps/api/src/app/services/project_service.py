from __future__ import annotations

from fastapi import HTTPException, status

from core_types import ContentBlock, Outline, OutlineSection, PresentationBrief, Project, ProjectFile, SlidePlan, SlidePlanItem, SourceBundle, TaskRun, UserIntent
from core_types.task.models import TaskRun
from core_types.enums import BundleStatus, FileUploadStatus, ParseStatus, ProjectStatus, ReviewStatus, TaskStatus, TaskType

from app.models.project import CreateProjectRequest, GenerateBriefRequest, GenerateOutlineRequest, GenerateSlidePlanRequest, RegisterProjectFileRequest
from app.repositories.project_repository import SqlAlchemyProjectRepository


class ProjectService:
    def __init__(self, repository: SqlAlchemyProjectRepository) -> None:
        self._repository = repository

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

    def list_project_files(self, project_id: str) -> list[ProjectFile]:
        self.get_project(project_id)
        return self._repository.list_project_files(project_id)

    def generate_brief(self, project_id: str, payload: GenerateBriefRequest) -> tuple[SourceBundle, PresentationBrief, TaskRun]:
        project = self.get_project(project_id)
        project_files = self._repository.list_project_files(project_id)
        if not project_files:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project has no files to analyze")

        source_bundle = SourceBundle(
            project_id=project_id,
            source_file_ids=[project_file.id for project_file in project_files],
            source_mode=project.source_mode,
            user_intent=payload.user_intent_override,
            raw_markdown=self._build_raw_markdown(project_files),
            normalized_markdown=self._build_normalized_markdown(project_files, payload.user_intent_override),
            citations=[project_file.file_name for project_file in project_files],
            status=BundleStatus.READY,
            metadata={"generated_from": "project_files"},
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
