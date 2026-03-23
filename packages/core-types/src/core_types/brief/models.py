from __future__ import annotations

from pydantic import Field

from core_types.common import IdentifiedModel, JsonDict
from core_types.enums import ReviewStatus


class PresentationBrief(IdentifiedModel):
    project_id: str
    source_bundle_id: str
    presentation_goal: str
    target_audience: str
    core_message: str
    storyline: str
    recommended_page_count: int = 12
    tone: str = "professional"
    style_preferences: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    status: ReviewStatus = ReviewStatus.DRAFT
    metadata: JsonDict = Field(default_factory=dict)
