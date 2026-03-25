from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from core_types import ExportJob, Outline, OutlineSection, PresentationBrief, Project, ProjectFile, SlideArtifact, SlidePlan, SlidePlanItem, ContentBlock, SourceBundle, TaskRun, TemplateMeta
from core_types.enums import ParseStatus, ProjectStatus, TaskStatus, TaskType

from app.db.models import ExportRecord, OutlineRecord, PresentationBriefRecord, ProjectFileRecord, ProjectRecord, SlideArtifactRecord, SlidePlanRecord, SourceBundleRecord, TaskRunRecord, TemplateRecord


class InMemoryProjectRepository:
    def __init__(self) -> None:
        self._projects: dict[str, Project] = {}
        self._tasks_by_project: dict[str, list[TaskRun]] = defaultdict(list)

    def create_project(self, project: Project) -> Project:
        self._projects[project.id] = project
        self._tasks_by_project[project.id].append(
            TaskRun(
                project_id=project.id,
                task_type=TaskType.INGEST,
                task_status=TaskStatus.SUCCEEDED,
                result={"project_status": ProjectStatus.CREATED.value},
            )
        )
        return project

    def get_project(self, project_id: str) -> Project | None:
        return self._projects.get(project_id)

    def list_project_tasks(self, project_id: str) -> list[TaskRun]:
        return list(self._tasks_by_project.get(project_id, []))

    def list_projects(self) -> list[Project]:
        return sorted(self._projects.values(), key=lambda project: project.created_at, reverse=True)

    def list_project_dashboard(self) -> list[dict[str, object]]:
        return [
            {
                "project": project,
                "file_count": 0,
                "parsed_file_count": 0,
                "failed_file_count": 0,
                "latest_brief": None,
                "latest_outline": None,
                "latest_slide_plan": None,
                "latest_artifact": None,
                "latest_export": None,
                "current_task": (self._tasks_by_project.get(project.id) or [None])[-1],
            }
            for project in self.list_projects()
        ]

    def create_project_file(self, project_file: ProjectFile) -> ProjectFile:
        self._tasks_by_project[project_file.project_id]
        return project_file

    def list_project_files(self, project_id: str) -> list[ProjectFile]:
        return []

    def get_project_file(self, project_id: str, file_id: str) -> ProjectFile | None:
        return None

    def create_source_bundle(self, source_bundle: SourceBundle) -> SourceBundle:
        return source_bundle

    def create_brief(self, brief: PresentationBrief) -> PresentationBrief:
        return brief

    def update_brief(self, brief: PresentationBrief) -> PresentationBrief:
        return brief

    def get_brief(self, brief_id: str) -> PresentationBrief | None:
        return None

    def get_latest_brief(self, project_id: str) -> PresentationBrief | None:
        return None

    def create_outline(self, outline: Outline) -> Outline:
        return outline

    def update_outline(self, outline: Outline) -> Outline:
        return outline

    def get_outline(self, outline_id: str) -> Outline | None:
        return None

    def get_latest_outline(self, project_id: str) -> Outline | None:
        return None

    def create_slide_plan(self, slide_plan: SlidePlan) -> SlidePlan:
        return slide_plan

    def update_slide_plan(self, slide_plan: SlidePlan) -> SlidePlan:
        return slide_plan

    def create_slide_artifact(self, artifact: SlideArtifact) -> SlideArtifact:
        return artifact

    def create_export_job(self, export_job: ExportJob) -> ExportJob:
        return export_job

    def get_slide_plan(self, slide_plan_id: str) -> SlidePlan | None:
        return None

    def get_latest_slide_plan(self, project_id: str) -> SlidePlan | None:
        return None

    def get_latest_source_bundle(self, project_id: str) -> SourceBundle | None:
        return None

    def create_task_run(self, task_run: TaskRun) -> TaskRun:
        self._tasks_by_project[task_run.project_id].append(task_run)
        return task_run

    def get_project_detail(self, project_id: str) -> dict[str, object] | None:
        project = self.get_project(project_id)
        if project is None:
            return None
        return {
            "project": project,
            "latest_source_bundle": None,
            "latest_brief": None,
            "latest_outline": None,
            "latest_slide_plan": None,
            "latest_artifact": None,
            "latest_export": None,
        }

    def list_project_exports(self, project_id: str, limit: int = 5) -> list[ExportJob]:
        return []

    def update_project(self, project: Project) -> Project:
        self._projects[project.id] = project
        return project

    def update_project_links(
        self,
        project_id: str,
        *,
        latest_source_bundle_id: str | None = None,
        latest_brief_id: str | None = None,
        latest_outline_id: str | None = None,
        latest_slide_plan_id: str | None = None,
        latest_artifact_id: str | None = None,
        status: str | None = None,
    ) -> Project | None:
        project = self.get_project(project_id)
        if project is None:
            return None
        updates = {
            "latest_source_bundle_id": latest_source_bundle_id,
            "latest_brief_id": latest_brief_id,
            "latest_outline_id": latest_outline_id,
            "latest_slide_plan_id": latest_slide_plan_id,
            "latest_artifact_id": latest_artifact_id,
            "status": status,
        }
        updated_project = project.model_copy(update={k: v for k, v in updates.items() if v is not None})
        self._projects[project_id] = updated_project
        return updated_project


class SqlAlchemyProjectRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_project(self, project: Project) -> Project:
        record = ProjectRecord(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status,
            source_mode=project.source_mode,
            owner_id=project.owner_id,
            tags=project.tags,
            current_template_id=project.current_template_id,
            latest_source_bundle_id=project.latest_source_bundle_id,
            latest_brief_id=project.latest_brief_id,
            latest_outline_id=project.latest_outline_id,
            latest_slide_plan_id=project.latest_slide_plan_id,
            latest_artifact_id=project.latest_artifact_id,
            last_error_code=project.last_error_code,
            metadata_json=project.metadata,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
        task = TaskRun(
            project_id=project.id,
            task_type=TaskType.INGEST,
            task_status=TaskStatus.SUCCEEDED,
            result={"project_status": ProjectStatus.CREATED.value},
        )
        task_record = TaskRunRecord(
            id=task.id,
            project_id=task.project_id,
            task_type=task.task_type,
            task_status=task.task_status,
            trigger_source=task.trigger_source,
            payload=task.payload,
            result=task.result,
            error_code=task.error_code,
            error_message=task.error_message,
            started_at=task.started_at,
            finished_at=task.finished_at,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
        self._session.add(record)
        self._session.add(task_record)
        self._session.commit()
        return self.get_project(project.id) or project

    def get_project(self, project_id: str) -> Project | None:
        record = self._session.get(ProjectRecord, project_id)
        if record is None:
            return None
        return Project(
            id=record.id,
            name=record.name,
            description=record.description,
            status=record.status,
            source_mode=record.source_mode,
            owner_id=record.owner_id,
            tags=record.tags or [],
            current_template_id=record.current_template_id,
            latest_source_bundle_id=record.latest_source_bundle_id,
            latest_brief_id=record.latest_brief_id,
            latest_outline_id=record.latest_outline_id,
            latest_slide_plan_id=record.latest_slide_plan_id,
            latest_artifact_id=record.latest_artifact_id,
            last_error_code=record.last_error_code,
            metadata=record.metadata_json or {},
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def list_projects(self) -> list[Project]:
        stmt = select(ProjectRecord).order_by(ProjectRecord.created_at.desc())
        records = self._session.execute(stmt).scalars().all()
        return [self.get_project(record.id) for record in records if self.get_project(record.id) is not None]

    def update_project(self, project: Project) -> Project:
        record = self._session.get(ProjectRecord, project.id)
        if record is None:
            raise ValueError(f"Project not found: {project.id}")
        record.name = project.name
        record.description = project.description
        record.status = project.status
        record.source_mode = project.source_mode
        record.owner_id = project.owner_id
        record.tags = project.tags
        record.current_template_id = project.current_template_id
        record.latest_source_bundle_id = project.latest_source_bundle_id
        record.latest_brief_id = project.latest_brief_id
        record.latest_outline_id = project.latest_outline_id
        record.latest_slide_plan_id = project.latest_slide_plan_id
        record.latest_artifact_id = project.latest_artifact_id
        record.last_error_code = project.last_error_code
        record.metadata_json = project.metadata
        record.updated_at = project.updated_at
        self._session.add(record)
        self._session.commit()
        return self.get_project(project.id) or project

    def list_project_tasks(self, project_id: str) -> list[TaskRun]:
        stmt = (
            select(TaskRunRecord)
            .where(TaskRunRecord.project_id == project_id)
            .order_by(TaskRunRecord.created_at.asc())
        )
        records = self._session.execute(stmt).scalars().all()
        return [
            TaskRun(
                id=record.id,
                project_id=record.project_id,
                task_type=record.task_type,
                task_status=record.task_status,
                trigger_source=record.trigger_source,
                payload=record.payload or {},
                result=record.result or {},
                error_code=record.error_code,
                error_message=record.error_message,
                started_at=record.started_at,
                finished_at=record.finished_at,
                created_at=record.created_at,
                updated_at=record.updated_at,
            )
            for record in records
        ]

    def create_project_file(self, project_file: ProjectFile) -> ProjectFile:
        record = ProjectFileRecord(
            id=project_file.id,
            project_id=project_file.project_id,
            file_name=project_file.file_name,
            file_type=project_file.file_type,
            storage_path=project_file.storage_path,
            mime_type=project_file.mime_type,
            size_bytes=project_file.size_bytes,
            checksum=project_file.checksum,
            upload_status=project_file.upload_status,
            parse_status=project_file.parse_status,
            parse_error=project_file.parse_error,
            extracted_summary=project_file.extracted_summary,
            metadata_json=project_file.metadata,
            created_at=project_file.created_at,
            updated_at=project_file.updated_at,
        )
        self._session.add(record)
        self._session.commit()
        return project_file

    def get_project_file(self, project_id: str, file_id: str) -> ProjectFile | None:
        record = self._session.get(ProjectFileRecord, file_id)
        if record is None or record.project_id != project_id:
            return None
        return ProjectFile(
            id=record.id,
            project_id=record.project_id,
            file_name=record.file_name,
            file_type=record.file_type,
            storage_path=record.storage_path,
            mime_type=record.mime_type,
            size_bytes=record.size_bytes,
            checksum=record.checksum,
            upload_status=record.upload_status,
            parse_status=record.parse_status,
            parse_error=record.parse_error,
            extracted_summary=record.extracted_summary,
            metadata=record.metadata_json or {},
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def list_project_files(self, project_id: str) -> list[ProjectFile]:
        stmt = (
            select(ProjectFileRecord)
            .where(ProjectFileRecord.project_id == project_id)
            .order_by(ProjectFileRecord.created_at.asc())
        )
        records = self._session.execute(stmt).scalars().all()
        return [
            ProjectFile(
                id=record.id,
                project_id=record.project_id,
                file_name=record.file_name,
                file_type=record.file_type,
                storage_path=record.storage_path,
                mime_type=record.mime_type,
                size_bytes=record.size_bytes,
                checksum=record.checksum,
                upload_status=record.upload_status,
                parse_status=record.parse_status,
                parse_error=record.parse_error,
                extracted_summary=record.extracted_summary,
                metadata=record.metadata_json or {},
                created_at=record.created_at,
                updated_at=record.updated_at,
            )
            for record in records
        ]

    def list_project_dashboard(self) -> list[dict[str, object]]:
        dashboard: list[dict[str, object]] = []
        for project in self.list_projects():
            files = self.list_project_files(project.id)
            tasks = self.list_project_tasks(project.id)
            detail = self.get_project_detail(project.id)
            if detail is None:
                continue
            dashboard.append(
                {
                    "project": project,
                    "file_count": len(files),
                    "parsed_file_count": len([project_file for project_file in files if project_file.parse_status == ParseStatus.SUCCEEDED]),
                    "failed_file_count": len([project_file for project_file in files if project_file.parse_status == ParseStatus.FAILED]),
                    "latest_brief": detail.get("latest_brief"),
                    "latest_outline": detail.get("latest_outline"),
                    "latest_slide_plan": detail.get("latest_slide_plan"),
                    "latest_artifact": detail.get("latest_artifact"),
                    "latest_export": detail.get("latest_export"),
                    "current_task": tasks[-1] if tasks else None,
                }
            )
        return dashboard

    def create_source_bundle(self, source_bundle: SourceBundle) -> SourceBundle:
        record = SourceBundleRecord(
            id=source_bundle.id,
            project_id=source_bundle.project_id,
            source_file_ids=source_bundle.source_file_ids,
            source_mode=source_bundle.source_mode,
            user_intent=source_bundle.user_intent.model_dump() if source_bundle.user_intent else None,
            raw_markdown=source_bundle.raw_markdown,
            normalized_markdown=source_bundle.normalized_markdown,
            page_chunks=[chunk.model_dump() for chunk in source_bundle.page_chunks],
            tables=[table.model_dump() for table in source_bundle.tables],
            images=[image.model_dump() for image in source_bundle.images],
            citations=source_bundle.citations,
            language=source_bundle.language,
            status=source_bundle.status,
            metadata_json=source_bundle.metadata,
            created_at=source_bundle.created_at,
            updated_at=source_bundle.updated_at,
        )
        self._session.add(record)
        self._session.commit()
        return source_bundle

    def get_source_bundle(self, source_bundle_id: str) -> SourceBundle | None:
        record = self._session.get(SourceBundleRecord, source_bundle_id)
        if record is None:
            return None
        return SourceBundle(
            id=record.id,
            project_id=record.project_id,
            source_file_ids=record.source_file_ids or [],
            source_mode=record.source_mode,
            user_intent=record.user_intent,
            raw_markdown=record.raw_markdown,
            normalized_markdown=record.normalized_markdown,
            page_chunks=record.page_chunks or [],
            tables=record.tables or [],
            images=record.images or [],
            citations=record.citations or [],
            language=record.language,
            status=record.status,
            metadata=record.metadata_json or {},
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def get_latest_source_bundle(self, project_id: str) -> SourceBundle | None:
        stmt = (
            select(SourceBundleRecord)
            .where(SourceBundleRecord.project_id == project_id)
            .order_by(SourceBundleRecord.created_at.desc())
        )
        record = self._session.execute(stmt).scalars().first()
        if record is None:
            return None
        return self.get_source_bundle(record.id)

    def create_brief(self, brief: PresentationBrief) -> PresentationBrief:
        record = PresentationBriefRecord(
            id=brief.id,
            project_id=brief.project_id,
            source_bundle_id=brief.source_bundle_id,
            presentation_goal=brief.presentation_goal,
            target_audience=brief.target_audience,
            core_message=brief.core_message,
            storyline=brief.storyline,
            recommended_page_count=brief.recommended_page_count,
            tone=brief.tone,
            style_preferences=brief.style_preferences,
            risks=brief.risks,
            assumptions=brief.assumptions,
            status=brief.status,
            metadata_json=brief.metadata,
            created_at=brief.created_at,
            updated_at=brief.updated_at,
        )
        self._session.add(record)
        self._session.commit()
        return brief

    def update_brief(self, brief: PresentationBrief) -> PresentationBrief:
        record = self._session.get(PresentationBriefRecord, brief.id)
        if record is None:
            raise ValueError(f"Brief {brief.id} not found")
        record.presentation_goal = brief.presentation_goal
        record.target_audience = brief.target_audience
        record.core_message = brief.core_message
        record.storyline = brief.storyline
        record.recommended_page_count = brief.recommended_page_count
        record.tone = brief.tone
        record.style_preferences = brief.style_preferences
        record.risks = brief.risks
        record.assumptions = brief.assumptions
        record.status = brief.status
        record.metadata_json = brief.metadata
        record.updated_at = brief.updated_at
        self._session.commit()
        return brief

    def get_brief(self, brief_id: str) -> PresentationBrief | None:
        record = self._session.get(PresentationBriefRecord, brief_id)
        if record is None:
            return None
        return PresentationBrief(
            id=record.id,
            project_id=record.project_id,
            source_bundle_id=record.source_bundle_id,
            presentation_goal=record.presentation_goal,
            target_audience=record.target_audience,
            core_message=record.core_message,
            storyline=record.storyline,
            recommended_page_count=record.recommended_page_count,
            tone=record.tone,
            style_preferences=record.style_preferences or [],
            risks=record.risks or [],
            assumptions=record.assumptions or [],
            status=record.status,
            metadata=record.metadata_json or {},
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def get_latest_brief(self, project_id: str) -> PresentationBrief | None:
        stmt = (
            select(PresentationBriefRecord)
            .where(PresentationBriefRecord.project_id == project_id)
            .order_by(PresentationBriefRecord.created_at.desc())
        )
        record = self._session.execute(stmt).scalars().first()
        if record is None:
            return None
        return self.get_brief(record.id)

    def create_outline(self, outline: Outline) -> Outline:
        record = OutlineRecord(
            id=outline.id,
            project_id=outline.project_id,
            brief_id=outline.brief_id,
            title=outline.title,
            chapters=[chapter.model_dump() for chapter in outline.chapters],
            summary=outline.summary,
            status=outline.status,
            metadata_json=outline.metadata,
            created_at=outline.created_at,
            updated_at=outline.updated_at,
        )
        self._session.add(record)
        self._session.commit()
        return outline

    def update_outline(self, outline: Outline) -> Outline:
        record = self._session.get(OutlineRecord, outline.id)
        if record is None:
            raise ValueError(f"Outline {outline.id} not found")
        record.title = outline.title
        record.chapters = [chapter.model_dump() for chapter in outline.chapters]
        record.summary = outline.summary
        record.status = outline.status
        record.metadata_json = outline.metadata
        record.updated_at = outline.updated_at
        self._session.commit()
        return outline

    def get_outline(self, outline_id: str) -> Outline | None:
        record = self._session.get(OutlineRecord, outline_id)
        if record is None:
            return None
        return Outline(
            id=record.id,
            project_id=record.project_id,
            brief_id=record.brief_id,
            title=record.title,
            chapters=[OutlineSection.model_validate(chapter) for chapter in (record.chapters or [])],
            summary=record.summary,
            status=record.status,
            metadata=record.metadata_json or {},
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def get_latest_outline(self, project_id: str) -> Outline | None:
        stmt = (
            select(OutlineRecord)
            .where(OutlineRecord.project_id == project_id)
            .order_by(OutlineRecord.created_at.desc())
        )
        record = self._session.execute(stmt).scalars().first()
        if record is None:
            return None
        return self.get_outline(record.id)

    def create_slide_plan(self, slide_plan: SlidePlan) -> SlidePlan:
        record = SlidePlanRecord(
            id=slide_plan.id,
            project_id=slide_plan.project_id,
            brief_id=slide_plan.brief_id,
            outline_id=slide_plan.outline_id,
            page_count=slide_plan.page_count,
            slides=[slide.model_dump() for slide in slide_plan.slides],
            design_direction=slide_plan.design_direction,
            status=slide_plan.status,
            metadata_json=slide_plan.metadata,
            created_at=slide_plan.created_at,
            updated_at=slide_plan.updated_at,
        )
        self._session.add(record)
        self._session.commit()
        return slide_plan

    def update_slide_plan(self, slide_plan: SlidePlan) -> SlidePlan:
        record = self._session.get(SlidePlanRecord, slide_plan.id)
        if record is None:
            raise ValueError(f"Slide plan {slide_plan.id} not found")
        record.page_count = slide_plan.page_count
        record.slides = [slide.model_dump() for slide in slide_plan.slides]
        record.design_direction = slide_plan.design_direction
        record.status = slide_plan.status
        record.metadata_json = slide_plan.metadata
        record.updated_at = slide_plan.updated_at
        self._session.commit()
        return slide_plan

    def get_slide_plan(self, slide_plan_id: str) -> SlidePlan | None:
        record = self._session.get(SlidePlanRecord, slide_plan_id)
        if record is None:
            return None
        return SlidePlan(
            id=record.id,
            project_id=record.project_id,
            brief_id=record.brief_id,
            outline_id=record.outline_id,
            page_count=record.page_count,
            slides=[SlidePlanItem.model_validate(slide) for slide in (record.slides or [])],
            design_direction=record.design_direction,
            status=record.status,
            metadata=record.metadata_json or {},
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def get_latest_slide_plan(self, project_id: str) -> SlidePlan | None:
        stmt = (
            select(SlidePlanRecord)
            .where(SlidePlanRecord.project_id == project_id)
            .order_by(SlidePlanRecord.created_at.desc())
        )
        record = self._session.execute(stmt).scalars().first()
        if record is None:
            return None
        return self.get_slide_plan(record.id)

    def create_task_run(self, task_run: TaskRun) -> TaskRun:
        record = TaskRunRecord(
            id=task_run.id,
            project_id=task_run.project_id,
            task_type=task_run.task_type,
            task_status=task_run.task_status,
            trigger_source=task_run.trigger_source,
            payload=task_run.payload,
            result=task_run.result,
            error_code=task_run.error_code,
            error_message=task_run.error_message,
            started_at=task_run.started_at,
            finished_at=task_run.finished_at,
            created_at=task_run.created_at,
            updated_at=task_run.updated_at,
        )
        self._session.add(record)
        self._session.commit()
        return task_run

    def create_slide_artifact(self, artifact: SlideArtifact) -> SlideArtifact:
        record = SlideArtifactRecord(
            id=artifact.id,
            project_id=artifact.project_id,
            slide_plan_id=artifact.slide_plan_id,
            template_id=artifact.template_id,
            svg_output_dir=artifact.svg_output_dir,
            svg_final_dir=artifact.svg_final_dir,
            preview_image_paths=artifact.preview_image_paths,
            render_status=artifact.render_status,
            failed_slide_ids=artifact.failed_slide_ids,
            log_path=artifact.log_path,
            metadata_json=artifact.metadata,
            created_at=artifact.created_at,
            updated_at=artifact.updated_at,
        )
        self._session.add(record)
        self._session.commit()
        return artifact

    def create_export_job(self, export_job: ExportJob) -> ExportJob:
        record = ExportRecord(
            id=export_job.id,
            project_id=export_job.project_id,
            artifact_id=export_job.artifact_id,
            run_id=export_job.run_id,
            export_format=export_job.export_format,
            export_path=export_job.export_path,
            preview_pdf_path=export_job.preview_pdf_path,
            status=export_job.status,
            error_message=export_job.error_message,
            metadata_json=export_job.metadata,
            created_at=export_job.created_at,
            updated_at=export_job.updated_at,
        )
        self._session.add(record)
        self._session.commit()
        return export_job

    def get_slide_artifact(self, artifact_id: str) -> SlideArtifact | None:
        record = self._session.get(SlideArtifactRecord, artifact_id)
        if record is None:
            return None
        return SlideArtifact(
            id=record.id,
            project_id=record.project_id,
            slide_plan_id=record.slide_plan_id,
            template_id=record.template_id,
            svg_output_dir=record.svg_output_dir,
            svg_final_dir=record.svg_final_dir,
            preview_image_paths=record.preview_image_paths or [],
            render_status=record.render_status,
            failed_slide_ids=record.failed_slide_ids or [],
            log_path=record.log_path,
            metadata=record.metadata_json or {},
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def get_export_job(self, export_id: str) -> ExportJob | None:
        record = self._session.get(ExportRecord, export_id)
        if record is None:
            return None
        return ExportJob(
            id=record.id,
            project_id=record.project_id,
            artifact_id=record.artifact_id,
            run_id=record.run_id,
            export_format=record.export_format,
            export_path=record.export_path,
            preview_pdf_path=record.preview_pdf_path,
            status=record.status,
            error_message=record.error_message,
            metadata=record.metadata_json or {},
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def list_project_exports(self, project_id: str, limit: int = 5) -> list[ExportJob]:
        stmt = (
            select(ExportRecord)
            .where(ExportRecord.project_id == project_id)
            .order_by(ExportRecord.created_at.desc())
            .limit(limit)
        )
        records = self._session.execute(stmt).scalars().all()
        exports: list[ExportJob] = []
        for record in records:
            export_job = self.get_export_job(record.id)
            if export_job is not None:
                exports.append(export_job)
        return exports

    def get_project_export(self, project_id: str, export_id: str) -> ExportJob | None:
        export_job = self.get_export_job(export_id)
        if export_job is None:
            return None
        if export_job.project_id != project_id:
            return None
        return export_job

    def get_project_detail(self, project_id: str) -> dict[str, object] | None:
        project = self.get_project(project_id)
        if project is None:
            return None
        latest_source_bundle = self.get_source_bundle(project.latest_source_bundle_id) if project.latest_source_bundle_id else self.get_latest_source_bundle(project_id)
        latest_brief = self.get_brief(project.latest_brief_id) if project.latest_brief_id else self.get_latest_brief(project_id)
        latest_outline = self.get_outline(project.latest_outline_id) if project.latest_outline_id else self.get_latest_outline(project_id)
        latest_slide_plan = self.get_slide_plan(project.latest_slide_plan_id) if project.latest_slide_plan_id else self.get_latest_slide_plan(project_id)
        latest_artifact = self.get_slide_artifact(project.latest_artifact_id) if project.latest_artifact_id else None
        latest_export = None
        if latest_artifact is not None:
            stmt = (
                select(ExportRecord)
                .where(ExportRecord.artifact_id == latest_artifact.id)
                .order_by(ExportRecord.created_at.desc())
            )
            export_record = self._session.execute(stmt).scalars().first()
            if export_record is not None:
                latest_export = self.get_export_job(export_record.id)
        return {
            "project": project,
            "latest_source_bundle": latest_source_bundle,
            "latest_brief": latest_brief,
            "latest_outline": latest_outline,
            "latest_slide_plan": latest_slide_plan,
            "latest_artifact": latest_artifact,
            "latest_export": latest_export,
        }

    def update_project_file(self, project_file: ProjectFile) -> ProjectFile:
        record = self._session.get(ProjectFileRecord, project_file.id)
        if record is None:
            raise ValueError(f"Project file not found: {project_file.id}")
        record.file_name = project_file.file_name
        record.file_type = project_file.file_type
        record.storage_path = project_file.storage_path
        record.mime_type = project_file.mime_type
        record.size_bytes = project_file.size_bytes
        record.checksum = project_file.checksum
        record.upload_status = project_file.upload_status
        record.parse_status = project_file.parse_status
        record.parse_error = project_file.parse_error
        record.extracted_summary = project_file.extracted_summary
        record.metadata_json = project_file.metadata
        self._session.add(record)
        self._session.commit()
        return self.get_project_file(project_file.project_id, project_file.id) or project_file

    def update_project_links(
        self,
        project_id: str,
        *,
        latest_source_bundle_id: str | None = None,
        latest_brief_id: str | None = None,
        latest_outline_id: str | None = None,
        latest_slide_plan_id: str | None = None,
        latest_artifact_id: str | None = None,
        status: str | None = None,
    ) -> Project | None:
        record = self._session.get(ProjectRecord, project_id)
        if record is None:
            return None
        if latest_source_bundle_id is not None:
            record.latest_source_bundle_id = latest_source_bundle_id
        if latest_brief_id is not None:
            record.latest_brief_id = latest_brief_id
        if latest_outline_id is not None:
            record.latest_outline_id = latest_outline_id
        if latest_slide_plan_id is not None:
            record.latest_slide_plan_id = latest_slide_plan_id
        if latest_artifact_id is not None:
            record.latest_artifact_id = latest_artifact_id
        if status is not None:
            record.status = status
        self._session.add(record)
        self._session.commit()
        return self.get_project(project_id)
