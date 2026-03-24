from __future__ import annotations

from core_types import LayoutMode, SlidePlan, TemplateMeta


class TemplateRegistryService:
    def __init__(self) -> None:
        self._templates = self._build_templates()

    def list_templates(self) -> list[TemplateMeta]:
        return list(self._templates)

    def get_template(self, template_id: str) -> TemplateMeta | None:
        return next((template for template in self._templates if template.template_id == template_id), None)

    def resolve_template(self, template_id: str | None, slide_plan: SlidePlan) -> TemplateMeta:
        if template_id:
            template = self.get_template(template_id)
            if template is None:
                raise ValueError(f"Unknown template_id: {template_id}")
            return template

        dominant_layouts = {slide.layout_mode for slide in slide_plan.slides}
        for template in self._templates:
            if dominant_layouts.issubset(set(template.supported_layout_modes)):
                return template
        return self._templates[0]

    def _build_templates(self) -> list[TemplateMeta]:
        return [
            TemplateMeta(
                template_id="consulting-clean",
                name="咨询清晰风",
                style_tags=["consulting", "clean", "structured"],
                scenario_tags=["analysis", "strategy", "report"],
                supported_layout_modes=[
                    LayoutMode.COVER,
                    LayoutMode.TOC,
                    LayoutMode.SECTION,
                    LayoutMode.HERO,
                    LayoutMode.TWO_COLUMN,
                    LayoutMode.BENTO,
                    LayoutMode.CHART_FOCUS,
                    LayoutMode.TIMELINE,
                    LayoutMode.ENDING,
                ],
                density_range="medium",
                color_scheme=["#0F172A", "#E2E8F0", "#0EA5E9"],
                design_spec_path="builtin://templates/consulting-clean/design-spec.json",
                preview_image_path="builtin://templates/consulting-clean/preview.png",
                metadata={
                    "default_for": ["analysis", "mixed"],
                    "font_family": "Source Han Sans",
                },
            ),
            TemplateMeta(
                template_id="academic-defense",
                name="学术答辩风",
                style_tags=["academic", "defense", "precise"],
                scenario_tags=["thesis", "research", "defense"],
                supported_layout_modes=[
                    LayoutMode.COVER,
                    LayoutMode.TOC,
                    LayoutMode.SECTION,
                    LayoutMode.TWO_COLUMN,
                    LayoutMode.CHART_FOCUS,
                    LayoutMode.TIMELINE,
                    LayoutMode.ENDING,
                ],
                density_range="medium-high",
                color_scheme=["#1E3A8A", "#F8FAFC", "#DC2626"],
                design_spec_path="builtin://templates/academic-defense/design-spec.json",
                preview_image_path="builtin://templates/academic-defense/preview.png",
                metadata={
                    "default_for": ["thesis", "research"],
                    "font_family": "Noto Serif SC",
                },
            ),
        ]