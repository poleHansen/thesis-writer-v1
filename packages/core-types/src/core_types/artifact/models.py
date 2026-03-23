from __future__ import annotations

from pydantic import Field

from core_types.common import IdentifiedModel, JsonDict
from core_types.enums import RenderStatus


class SlideArtifact(IdentifiedModel):
    project_id: str
    slide_plan_id: str
    template_id: str | None = None
    svg_output_dir: str | None = None
    svg_final_dir: str | None = None
    preview_image_paths: list[str] = Field(default_factory=list)
    render_status: RenderStatus = RenderStatus.PENDING
    failed_slide_ids: list[str] = Field(default_factory=list)
    log_path: str | None = None
    metadata: JsonDict = Field(default_factory=dict)
