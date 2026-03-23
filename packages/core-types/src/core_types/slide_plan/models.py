from __future__ import annotations

from pydantic import Field

from core_types.common import CoreModel, IdentifiedModel, JsonDict
from core_types.enums import LayoutMode, ReviewStatus


class ContentBlock(CoreModel):
    block_id: str
    block_type: str
    heading: str | None = None
    body: str | None = None
    bullets: list[str] = Field(default_factory=list)
    asset_refs: list[str] = Field(default_factory=list)
    chart_hint: str | None = None
    emphasis: str | None = None


class SlidePlanItem(CoreModel):
    slide_id: str
    slide_number: int
    title: str
    conclusion: str
    layout_mode: LayoutMode
    content_blocks: list[ContentBlock] = Field(default_factory=list)
    speaker_notes: str | None = None
    data_refs: list[str] = Field(default_factory=list)
    visual_priority: str | None = None


class SlidePlan(IdentifiedModel):
    project_id: str
    brief_id: str
    outline_id: str
    page_count: int = 0
    slides: list[SlidePlanItem] = Field(default_factory=list)
    design_direction: str | None = None
    status: ReviewStatus = ReviewStatus.DRAFT
    metadata: JsonDict = Field(default_factory=dict)
