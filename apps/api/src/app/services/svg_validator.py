from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class SvgValidationResult:
    file_path: str
    is_valid: bool
    issues: list[str] = field(default_factory=list)


class SvgValidator:
    _banned_tokens = [
        "<script",
        "<style",
        "clipPath",
        "<mask",
        "<foreignObject",
        "textPath",
        "marker-end",
        "<iframe",
        "<animate",
    ]
    _banned_attribute_tokens = [
        "rgba(",
    ]

    def validate_file(self, file_path: str, svg_content: str) -> SvgValidationResult:
        issues: list[str] = []
        svg_path = Path(file_path)
        if 'viewBox="0 0 1280 720"' not in svg_content:
            issues.append("missing_required_viewBox")
        if "<svg" not in svg_content:
            issues.append("missing_svg_root")
        if 'width="1280"' not in svg_content:
            issues.append("missing_required_width")
        if 'height="720"' not in svg_content:
            issues.append("missing_required_height")
        for token in self._banned_tokens:
            if token in svg_content:
                issues.append(f"banned_token:{token}")
        for token in self._banned_attribute_tokens:
            if token in svg_content:
                issues.append(f"banned_attribute_token:{token}")
        if self._contains_group_opacity(svg_content):
            issues.append("banned_attribute_token:group_opacity")
        if self._contains_external_resource(svg_content):
            issues.append("external_resource_reference")
        if self._contains_missing_local_resource(svg_path, svg_content):
            issues.append("missing_local_resource_reference")
        if self._contains_text_overflow(svg_content):
            issues.append("potential_text_overflow")
        return SvgValidationResult(file_path=file_path, is_valid=not issues, issues=issues)

    def _contains_group_opacity(self, svg_content: str) -> bool:
        return bool(re.search(r'<g\b[^>]*\sopacity="[^"]+"', svg_content))

    def _contains_external_resource(self, svg_content: str) -> bool:
        hrefs = self._extract_resource_hrefs(svg_content)
        for href in hrefs:
            normalized = href.strip()
            if normalized.startswith(("http://", "https://", "file://", "../")):
                return True
        return False

    def _contains_missing_local_resource(self, svg_path: Path, svg_content: str) -> bool:
        hrefs = self._extract_resource_hrefs(svg_content)
        for href in hrefs:
            normalized = href.strip()
            if not normalized or normalized.startswith(("http://", "https://", "file://", "data:", "#", "../")):
                continue
            candidate_path = (svg_path.parent / normalized).resolve()
            if not candidate_path.exists():
                return True
        return False

    def _extract_resource_hrefs(self, svg_content: str) -> list[str]:
        return re.findall(r"(?:xlink:href|href)=\"([^\"]+)\"", svg_content)

    def _contains_text_overflow(self, svg_content: str) -> bool:
        text_nodes = re.finditer(r"<text\b([^>]*)>(.*?)</text>", svg_content, flags=re.DOTALL)
        for match in text_nodes:
            attributes = match.group(1)
            raw_text = match.group(2)
            lines = self._extract_text_lines(raw_text)
            if not lines:
                continue
            if any(len(line) > 120 for line in lines):
                return True
            if any(self._text_exceeds_canvas(attributes, line) for line in lines):
                return True
            if self._text_exceeds_height(attributes, len(lines)):
                return True
        return False

    def _extract_text_lines(self, raw_text: str) -> list[str]:
        normalized = raw_text.strip()
        if not normalized:
            return []

        tspan_matches = list(re.finditer(r"<tspan\b[^>]*>(.*?)</tspan>", normalized, flags=re.DOTALL))
        if not tspan_matches:
            text = re.sub(r"<[^>]+>", "", normalized).strip()
            return [text] if text else []

        lines: list[str] = []
        prefix = re.sub(r"<tspan\b[^>]*>.*?</tspan>", "", normalized, flags=re.DOTALL)
        prefix_text = re.sub(r"<[^>]+>", "", prefix).strip()
        if prefix_text:
            lines.append(prefix_text)
        for match in tspan_matches:
            line = re.sub(r"<[^>]+>", "", match.group(1)).strip()
            if line:
                lines.append(line)
        return lines

    def _text_exceeds_canvas(self, attributes: str, text: str) -> bool:
        font_size = self._extract_numeric_attribute(attributes, "font-size") or 16.0
        x = self._extract_numeric_attribute(attributes, "x") or 0.0
        max_width = self._extract_numeric_attribute(attributes, "data-max-width")
        estimated_width = len(text) * font_size * 0.56

        if max_width is not None and estimated_width > max_width:
            return True

        anchor = self._extract_string_attribute(attributes, "text-anchor") or "start"
        if anchor == "middle":
            left = x - estimated_width / 2
            right = x + estimated_width / 2
        elif anchor == "end":
            left = x - estimated_width
            right = x
        else:
            left = x
            right = x + estimated_width

        return left < 0 or right > 1280

    def _text_exceeds_height(self, attributes: str, line_count: int) -> bool:
        max_height = self._extract_numeric_attribute(attributes, "data-max-height")
        if max_height is None:
            return False

        font_size = self._extract_numeric_attribute(attributes, "font-size") or 16.0
        line_height_factor = self._extract_numeric_attribute(attributes, "data-line-height")
        if line_height_factor is None:
            dy = self._extract_first_tspan_dy(attributes)
            if dy is not None and font_size > 0:
                line_height_factor = dy / font_size
        if line_height_factor is None:
            line_height_factor = 1.35
        line_height = font_size * line_height_factor
        estimated_height = font_size + (line_count - 1) * line_height
        return estimated_height > max_height

    def _extract_first_tspan_dy(self, attributes: str) -> float | None:
        match = re.search(r'data-first-tspan-dy="([0-9]+(?:\.[0-9]+)?)"', attributes)
        if match is None:
            return None
        return float(match.group(1))

    def _extract_numeric_attribute(self, attributes: str, name: str) -> float | None:
        match = re.search(rf'{re.escape(name)}="([0-9]+(?:\.[0-9]+)?)"', attributes)
        if match is None:
            return None
        return float(match.group(1))

    def _extract_string_attribute(self, attributes: str, name: str) -> str | None:
        match = re.search(rf'{re.escape(name)}="([^\"]+)"', attributes)
        if match is None:
            return None
        return match.group(1)