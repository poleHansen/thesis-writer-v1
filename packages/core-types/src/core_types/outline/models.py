from __future__ import annotations

from pydantic import Field

from core_types.common import CoreModel, IdentifiedModel, JsonDict
from core_types.enums import ReviewStatus


class OutlineSection(CoreModel):
    section_id: str
    title: str
    objective: str
    key_message: str
    supporting_points: list[str] = Field(default_factory=list)
    estimated_slides: int = 1
    children: list["OutlineSection"] = Field(default_factory=list)


class Outline(IdentifiedModel):
    project_id: str
    brief_id: str
    title: str
    chapters: list[OutlineSection] = Field(default_factory=list)
    summary: str | None = None
    status: ReviewStatus = ReviewStatus.DRAFT
    metadata: JsonDict = Field(default_factory=dict)


OutlineSection.model_rebuild()
