from __future__ import annotations

import json
from pathlib import Path

from core_types import LayoutMode, SlidePlan, TemplateMeta


class TemplateRegistryService:
    def __init__(self, template_root: str | Path | None = None) -> None:
        self._template_root = Path(template_root) if template_root is not None else Path("templates") / "builtin"
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
        scenario_hints = self._collect_scenario_hints(slide_plan)
        ranked_templates = sorted(
            self._templates,
            key=lambda template: (
                self._scenario_match_score(template, scenario_hints),
                self._layout_match_score(template, dominant_layouts),
            ),
            reverse=True,
        )
        best_template = ranked_templates[0]
        if self._layout_match_score(best_template, dominant_layouts) > 0:
            return best_template
        return self._templates[0]

    def _collect_scenario_hints(self, slide_plan: SlidePlan) -> set[str]:
        hints: set[str] = set()
        for raw_value in [slide_plan.design_direction, slide_plan.metadata.get("preferred_template_id")]:
            hints.update(self._normalize_hint_tokens(raw_value))

        for key in ("scenario", "scenario_tags", "style_tags", "domain", "content_type"):
            hints.update(self._normalize_hint_tokens(slide_plan.metadata.get(key)))
        return hints

    def _normalize_hint_tokens(self, raw_value: object) -> set[str]:
        if raw_value is None:
            return set()
        if isinstance(raw_value, str):
            normalized = raw_value.replace("/", " ").replace("-", " ").replace("_", " ").lower()
            return {token for token in normalized.split() if token}
        if isinstance(raw_value, list):
            tokens: set[str] = set()
            for item in raw_value:
                tokens.update(self._normalize_hint_tokens(item))
            return tokens
        return set()

    def _scenario_match_score(self, template: TemplateMeta, scenario_hints: set[str]) -> int:
        if not scenario_hints:
            return 0
        template_tokens = {
            token
            for value in [template.template_id, template.name, *template.style_tags, *template.scenario_tags]
            for token in self._normalize_hint_tokens(value)
        }
        return len(template_tokens.intersection(scenario_hints))

    def _layout_match_score(self, template: TemplateMeta, dominant_layouts: set[LayoutMode]) -> int:
        supported_layouts = set(template.supported_layout_modes)
        if not dominant_layouts:
            return 1
        if dominant_layouts.issubset(supported_layouts):
            return len(dominant_layouts)
        return len(dominant_layouts.intersection(supported_layouts))

    def _build_templates(self) -> list[TemplateMeta]:
        template_files = sorted(self._template_root.glob("*.json"))
        templates: list[TemplateMeta] = []
        for template_file in template_files:
            payload = json.loads(template_file.read_text(encoding="utf-8"))
            payload["supported_layout_modes"] = [LayoutMode(mode) for mode in payload.get("supported_layout_modes", [])]
            templates.append(TemplateMeta(**payload))
        if not templates:
            raise ValueError(f"No builtin templates found under: {self._template_root}")
        return templates