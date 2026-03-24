from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.models.project import CreateProjectRequest
from app.models.project import BriefResponse
from app.models.project import GenerateBriefRequest
from app.models.project import GenerateOutlineRequest
from app.models.project import GenerateSlideArtifactRequest
from app.models.project import GenerateSlidePlanRequest
from app.models.project import OutlineResponse
from app.models.project import ParseProjectFilesRequest
from app.models.project import ParseProjectFilesResponse
from app.models.project import ProjectFileResponse
from app.models.project import ProjectDetailResponse
from app.models.project import ProjectFilesResponse
from app.models.project import ProjectResponse
from app.models.project import ProjectStatusResponse
from app.models.project import RegisterProjectFileRequest
from app.models.project import SlidePlanResponse
from app.models.project import SlideArtifactResponse
from app.models.project import SourceBundleResponse
from app.models.project import TemplatesResponse
from app.models.project import UpdateBriefRequest
from app.models.project import UpdateBriefResponse
from app.models.project import UpdateOutlineRequest
from app.models.project import UpdateOutlineResponse
from app.models.project import UpdateSlidePlanRequest
from app.models.project import UpdateSlidePlanResponse
from app.models.project import UploadProjectFileRequest
from app.services.project_service import ProjectService
from app.state import get_project_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/templates", response_model=TemplatesResponse)
def list_templates(
    service: ProjectService = Depends(get_project_service),
) -> TemplatesResponse:
    return TemplatesResponse(templates=service.list_templates())


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: CreateProjectRequest,
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    project = service.create_project(payload)
    return ProjectResponse(project=project)


@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
) -> ProjectDetailResponse:
    detail = service.get_project_detail(project_id)
    return ProjectDetailResponse(**detail)


@router.get("/{project_id}/status", response_model=ProjectStatusResponse)
def get_project_status(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
) -> ProjectStatusResponse:
    project, tasks = service.get_project_status(project_id)
    current_task = tasks[-1] if tasks else None
    return ProjectStatusResponse(
        project_id=project.id,
        project_status=project.status,
        current_task=current_task,
        recent_tasks=tasks,
    )


@router.post("/{project_id}/files", response_model=ProjectFileResponse, status_code=status.HTTP_201_CREATED)
def register_project_file(
    project_id: str,
    payload: RegisterProjectFileRequest,
    service: ProjectService = Depends(get_project_service),
) -> ProjectFileResponse:
    project_file = service.register_project_file(project_id, payload)
    return ProjectFileResponse(file=project_file)


@router.post("/{project_id}/files:upload", response_model=ProjectFileResponse, status_code=status.HTTP_201_CREATED)
def upload_project_file(
    project_id: str,
    payload: UploadProjectFileRequest,
    service: ProjectService = Depends(get_project_service),
) -> ProjectFileResponse:
    project_file = service.upload_project_file(project_id, payload)
    return ProjectFileResponse(file=project_file)


@router.get("/{project_id}/files", response_model=ProjectFilesResponse)
def list_project_files(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
) -> ProjectFilesResponse:
    files = service.list_project_files(project_id)
    return ProjectFilesResponse(files=files)


@router.post("/{project_id}/files:parse", response_model=ParseProjectFilesResponse)
def parse_project_files(
    project_id: str,
    payload: ParseProjectFilesRequest,
    service: ProjectService = Depends(get_project_service),
) -> ParseProjectFilesResponse:
    files, source_bundle, task_run = service.parse_project_files(project_id, payload)
    return ParseProjectFilesResponse(files=files, source_bundle=source_bundle, task_run=task_run)


@router.post("/{project_id}/brief:generate", response_model=BriefResponse)
def generate_brief(
    project_id: str,
    payload: GenerateBriefRequest,
    service: ProjectService = Depends(get_project_service),
) -> BriefResponse:
    _, brief, task_run = service.generate_brief(project_id, payload)
    return BriefResponse(brief=brief, task_run=task_run)


@router.patch("/{project_id}/brief", response_model=UpdateBriefResponse)
def update_brief(
    project_id: str,
    payload: UpdateBriefRequest,
    service: ProjectService = Depends(get_project_service),
) -> UpdateBriefResponse:
    brief = service.update_brief(project_id, payload)
    return UpdateBriefResponse(brief=brief)


@router.post("/{project_id}/outline:generate", response_model=OutlineResponse)
def generate_outline(
    project_id: str,
    payload: GenerateOutlineRequest,
    service: ProjectService = Depends(get_project_service),
) -> OutlineResponse:
    outline, task_run = service.generate_outline(project_id, payload)
    return OutlineResponse(outline=outline, task_run=task_run)


@router.patch("/{project_id}/outline", response_model=UpdateOutlineResponse)
def update_outline(
    project_id: str,
    payload: UpdateOutlineRequest,
    service: ProjectService = Depends(get_project_service),
) -> UpdateOutlineResponse:
    outline = service.update_outline(project_id, payload)
    return UpdateOutlineResponse(outline=outline)


@router.post("/{project_id}/slide-plan:generate", response_model=SlidePlanResponse)
def generate_slide_plan(
    project_id: str,
    payload: GenerateSlidePlanRequest,
    service: ProjectService = Depends(get_project_service),
) -> SlidePlanResponse:
    slide_plan, task_run = service.generate_slide_plan(project_id, payload)
    return SlidePlanResponse(slide_plan=slide_plan, task_run=task_run)


@router.post("/{project_id}/artifact:generate", response_model=SlideArtifactResponse)
def generate_slide_artifact(
    project_id: str,
    payload: GenerateSlideArtifactRequest,
    service: ProjectService = Depends(get_project_service),
) -> SlideArtifactResponse:
    artifact, task_run = service.generate_slide_artifact(project_id, payload)
    return SlideArtifactResponse(artifact=artifact, task_run=task_run)


@router.patch("/{project_id}/slide-plan", response_model=UpdateSlidePlanResponse)
def update_slide_plan(
    project_id: str,
    payload: UpdateSlidePlanRequest,
    service: ProjectService = Depends(get_project_service),
) -> UpdateSlidePlanResponse:
    slide_plan = service.update_slide_plan(project_id, payload)
    return UpdateSlidePlanResponse(slide_plan=slide_plan)
