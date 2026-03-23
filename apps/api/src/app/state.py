from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_session
from app.repositories.project_repository import SqlAlchemyProjectRepository
from app.services.project_service import ProjectService


def get_project_service(session: Session = Depends(get_session)) -> ProjectService:
    repository = SqlAlchemyProjectRepository(session)
    return ProjectService(repository)
