from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel, Field


class FinalizedSvgPage(BaseModel):
    source_file_name: str
    final_file_name: str
    final_svg_content: str
    applied_steps: list[str] = Field(default_factory=list)


class SvgFinalizeResult(BaseModel):
    pages: list[FinalizedSvgPage] = Field(default_factory=list)
    finalized_files: list[str] = Field(default_factory=list)
    summary: dict[str, int] = Field(default_factory=dict)


class SvgFinalizer:
    def finalize_pages(self, rendered_pages: list[tuple[str, str]]) -> SvgFinalizeResult:
        finalized_pages: list[FinalizedSvgPage] = []
        for index, (source_file_name, svg_content) in enumerate(rendered_pages, start=1):
            normalized_content, applied_steps = self._normalize_svg(svg_content)
            finalized_pages.append(
                FinalizedSvgPage(
                    source_file_name=source_file_name,
                    final_file_name=f"slide-{index:02d}.svg",
                    final_svg_content=normalized_content,
                    applied_steps=applied_steps,
                )
            )

        return SvgFinalizeResult(
            pages=finalized_pages,
            summary={
                "page_count": len(finalized_pages),
                "normalized_xml_declaration_count": len(finalized_pages),
                "resource_path_rewrite_count": sum(1 for page in finalized_pages if "normalize_resource_paths" in page.applied_steps),
                "width_height_alignment_count": sum(1 for page in finalized_pages if "ensure_canvas_dimensions" in page.applied_steps),
            },
        )

    def _normalize_svg(self, svg_content: str) -> tuple[str, list[str]]:
        normalized = svg_content.lstrip("\ufeff").strip()
        applied_steps = ["strip_bom", "trim_whitespace"]
        if not normalized.startswith("<?xml"):
            normalized = f'<?xml version="1.0" encoding="UTF-8"?>\n{normalized}'
            applied_steps.append("add_xml_declaration")
        normalized, did_rewrite_resources = self._normalize_resource_paths(normalized)
        if did_rewrite_resources:
            applied_steps.append("normalize_resource_paths")
        normalized, ensured_dimensions = self._ensure_canvas_dimensions(normalized)
        if ensured_dimensions:
            applied_steps.append("ensure_canvas_dimensions")
        if not normalized.endswith("\n"):
            normalized = f"{normalized}\n"
            applied_steps.append("append_trailing_newline")
        return normalized, applied_steps

    def _normalize_resource_paths(self, svg_content: str) -> tuple[str, bool]:
        normalized = svg_content.replace("\\", "/")
        normalized = normalized.replace("href=\"./", 'href="')
        normalized = normalized.replace("xlink:href=\"./", 'xlink:href="')
        return normalized, normalized != svg_content

    def _ensure_canvas_dimensions(self, svg_content: str) -> tuple[str, bool]:
        if "<svg" not in svg_content:
            return svg_content, False

        updated = svg_content
        changed = False
        if 'viewBox="0 0 1280 720"' in updated:
            if 'width="1280"' not in updated:
                updated = re.sub(r"<svg\b", '<svg width="1280"', updated, count=1)
                changed = True
            if 'height="720"' not in updated:
                updated = re.sub(r"<svg\b([^>]*)width=\"1280\"", '<svg\\1width="1280" height="720"', updated, count=1)
                changed = True
        return updated, changed