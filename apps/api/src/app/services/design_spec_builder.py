from __future__ import annotations

from core_types import Project, SlidePlan, TemplateMeta


class DesignSpecBuilder:
    def build(self, project: Project, slide_plan: SlidePlan, template: TemplateMeta) -> dict[str, object]:
        return {
            "project_id": project.id,
            "project_name": project.name,
            "template": {
                "template_id": template.template_id,
                "name": template.name,
                "style_tags": template.style_tags,
                "scenario_tags": template.scenario_tags,
                "color_scheme": template.color_scheme,
                "density_range": template.density_range,
                "design_spec_path": template.design_spec_path,
                "preview_image_path": template.preview_image_path,
                "metadata": template.metadata,
            },
            "design_direction": slide_plan.design_direction,
            "page_count": slide_plan.page_count,
            "render_mode": "placeholder",
            "slides": [
                {
                    "slide_id": slide.slide_id,
                    "slide_number": slide.slide_number,
                    "title": slide.title,
                    "conclusion": slide.conclusion,
                    "layout_mode": slide.layout_mode,
                    "content_block_count": len(slide.content_blocks),
                    "visual_priority": slide.visual_priority,
                }
                for slide in slide_plan.slides
            ],
        }