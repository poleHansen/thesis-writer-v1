from __future__ import annotations

from pydantic import Field

from core_types.common import IdentifiedModel, JsonDict
from core_types.enums import LayoutMode


class TemplateMeta(IdentifiedModel):
    template_id: str
    name: str
    style_tags: list[str] = Field(default_factory=list)
    scenario_tags: list[str] = Field(default_factory=list)
    supported_layout_modes: list[LayoutMode] = Field(default_factory=list)
    density_range: str = "medium"
    color_scheme: list[str] = Field(default_factory=list)
    design_spec_path: str
    preview_image_path: str | None = None
    version: str = "1.0.0"
    is_active: bool = True
    metadata: JsonDict = Field(default_factory=dict)
