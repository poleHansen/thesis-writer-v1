from __future__ import annotations

from html import escape

from pydantic import BaseModel, Field

from core_types import SlidePlan, SlidePlanItem, TemplateMeta
from core_types.enums import LayoutMode, RenderStatus


class RenderedSvgPage(BaseModel):
    slide_id: str
    slide_number: int
    svg_content: str


class SvgRenderResult(BaseModel):
    artifact_id: str = "pending-artifact"
    pages: list[RenderedSvgPage] = Field(default_factory=list)
    generated_files: list[str] = Field(default_factory=list)
    failed_slide_ids: list[str] = Field(default_factory=list)
    render_errors: list[dict[str, str]] = Field(default_factory=list)
    render_status: RenderStatus = RenderStatus.PENDING
    log_path: str | None = None
    validation_summary: dict[str, int] = Field(default_factory=dict)


class SvgRenderer:
    def render(self, slide_plan: SlidePlan, template: TemplateMeta) -> SvgRenderResult:
        pages: list[RenderedSvgPage] = []
        failed_slide_ids: list[str] = []
        render_errors: list[dict[str, str]] = []
        for slide in slide_plan.slides:
            try:
                pages.append(
                    RenderedSvgPage(
                        slide_id=slide.slide_id,
                        slide_number=slide.slide_number,
                        svg_content=self._render_slide(slide, template, slide_plan.page_count),
                    )
                )
            except Exception as exc:
                failed_slide_ids.append(slide.slide_id)
                render_errors.append({"slide_id": slide.slide_id, "error": str(exc)})

        render_status = RenderStatus.SUCCEEDED if not failed_slide_ids else RenderStatus.PARTIAL
        if not pages:
            render_status = RenderStatus.FAILED
        return SvgRenderResult(pages=pages, failed_slide_ids=failed_slide_ids, render_errors=render_errors, render_status=render_status)

    def _render_slide(self, slide: SlidePlanItem, template: TemplateMeta, total_pages: int) -> str:
        palette = template.color_scheme or ["#0F172A", "#F8FAFC", "#0EA5E9"]
        background = palette[1] if len(palette) > 1 else "#F8FAFC"
        foreground = palette[0]
        accent = palette[2] if len(palette) > 2 else "#0EA5E9"
        blocks = self._render_blocks(slide, foreground, accent)
        layout_mode_label = self._multiline_text(
            text=self._layout_mode_value(slide.layout_mode),
            x=80,
            y=110,
            max_width=1120,
            max_height=24,
            font_size=20,
            fill=accent,
            max_lines=1,
            line_height=1.0,
        )
        title = self._multiline_text(
            text=slide.title,
            x=80,
            y=170,
            max_width=1120,
            max_height=92,
            font_size=38,
            fill=foreground,
            font_weight="700",
            max_lines=2,
            line_height=1.18,
        )
        subtitle = self._multiline_text(
            text=slide.conclusion,
            x=80,
            y=230,
            max_width=1120,
            max_height=48,
            font_size=20,
            fill=foreground,
            fill_opacity="0.72",
            max_lines=2,
            line_height=1.2,
        )
        footer = self._multiline_text(
            text=f"{slide.slide_number}/{total_pages}  {template.name}",
            x=80,
            y=685,
            max_width=1120,
            max_height=22,
            font_size=18,
            fill=foreground,
            fill_opacity="0.65",
            max_lines=1,
            line_height=1.0,
        )

        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <rect width="1280" height="720" fill="{background}" />
  <rect x="0" y="0" width="1280" height="18" fill="{accent}" />
        {layout_mode_label}
    {title}
    {subtitle}
  {blocks}
  <line x1="80" y1="650" x2="1200" y2="650" stroke="{foreground}" stroke-opacity="0.18" />
    {footer}
</svg>'''

    def _layout_mode_value(self, layout_mode: LayoutMode | str) -> str:
        return layout_mode.value if isinstance(layout_mode, LayoutMode) else str(layout_mode)

    def _render_blocks(self, slide: SlidePlanItem, foreground: str, accent: str) -> str:
        if slide.layout_mode == LayoutMode.COVER:
            return self._cover_blocks(slide, foreground, accent)
        if slide.layout_mode == LayoutMode.TOC:
            return self._toc_blocks(slide, foreground, accent)
        if slide.layout_mode == LayoutMode.SECTION:
            return self._section_blocks(slide, foreground, accent)
        if slide.layout_mode == LayoutMode.TIMELINE:
            return self._timeline_blocks(slide, foreground, accent)
        if slide.layout_mode == LayoutMode.BENTO:
            return self._bento_blocks(slide, foreground, accent)
        if slide.layout_mode == LayoutMode.CHART_FOCUS:
            return self._chart_focus_blocks(slide, foreground, accent)
        if slide.layout_mode == LayoutMode.TWO_COLUMN:
            return self._two_column_blocks(slide, foreground, accent)
        if slide.layout_mode == LayoutMode.ENDING:
            return self._ending_blocks(slide, foreground, accent)
        return self._hero_blocks(slide, foreground, accent)

    def _cover_blocks(self, slide: SlidePlanItem, foreground: str, accent: str) -> str:
        body = self._multiline_text(
            text=slide.content_blocks[0].body if slide.content_blocks and slide.content_blocks[0].body else "",
            x=80,
            y=330,
            max_width=720,
            max_height=130,
            font_size=22,
            fill=foreground,
            fill_opacity="0.78",
            max_lines=4,
        )
        return f'''<circle cx="1030" cy="180" r="120" fill="{accent}" fill-opacity="0.12" />
  <circle cx="1120" cy="260" r="70" fill="{accent}" fill-opacity="0.22" />
    {body}'''

    def _toc_blocks(self, slide: SlidePlanItem, foreground: str, accent: str) -> str:
        items: list[str] = []
        cursor = 290
        bottom_limit = 570
        for index, block in enumerate(slide.content_blocks[:6], start=1):
            item_text = f"{index:02d}. {block.heading or block.body or f'目录 {index}'}"
            line_count = max(len(self._wrap_text(item_text, max_width=1040, font_size=24, max_lines=2, max_height=58, line_height=1.2)), 1)
            item_height = max(24 + int(line_count * 24 * 1.2), 34)
            if cursor + item_height > bottom_limit:
                break
            items.append(
                self._multiline_text(
                    text=item_text,
                    x=120,
                    y=cursor,
                    max_width=1040,
                    max_height=58,
                    font_size=24,
                    fill=foreground,
                    max_lines=2,
                    line_height=1.2,
                )
            )
            cursor += item_height
        return f'<rect x="80" y="250" width="1120" height="320" rx="24" fill="{accent}" fill-opacity="0.08" />' + "".join(items)

    def _section_blocks(self, slide: SlidePlanItem, foreground: str, accent: str) -> str:
        section_number = self._multiline_text(
            text=f"{slide.slide_number:02d}",
            x=120,
            y=380,
            max_width=120,
            max_height=64,
            font_size=56,
            fill=foreground,
            font_weight="700",
            max_lines=1,
            line_height=1.0,
        )
        section_title = self._multiline_text(
            text=slide.content_blocks[0].heading if slide.content_blocks and slide.content_blocks[0].heading else slide.title,
            x=650,
            y=350,
            max_width=520,
            max_height=108,
            font_size=34,
            fill=foreground,
            font_weight="700",
            max_lines=3,
            line_height=1.15,
        )
        return f'''<rect x="80" y="280" width="520" height="220" rx="32" fill="{accent}" fill-opacity="0.12" />
    {section_number}
  {section_title}'''

    def _hero_blocks(self, slide: SlidePlanItem, foreground: str, accent: str) -> str:
        summary = self._multiline_text(
            text=slide.content_blocks[0].body if slide.content_blocks and slide.content_blocks[0].body else "",
            x=800,
            y=330,
            max_width=340,
            max_height=120,
            font_size=24,
            fill=foreground,
            max_lines=4,
        )
        bullets = self._bullet_group(slide, 80, 320, foreground, accent, max_items=4, max_group_height=188)
        return f'''<rect x="760" y="260" width="420" height="220" rx="28" fill="{accent}" fill-opacity="0.1" />
    {summary}{bullets}'''

    def _two_column_blocks(self, slide: SlidePlanItem, foreground: str, accent: str) -> str:
        left = self._block_card(slide.content_blocks[0] if slide.content_blocks else None, 80, 280, 500, 260, foreground, accent)
        right = self._block_card(slide.content_blocks[1] if len(slide.content_blocks) > 1 else None, 640, 280, 560, 260, foreground, accent)
        return left + right

    def _bento_blocks(self, slide: SlidePlanItem, foreground: str, accent: str) -> str:
        cards: list[str] = []
        positions = [(80, 280, 360, 150), (470, 280, 340, 150), (840, 280, 360, 150), (80, 450, 560, 150), (670, 450, 530, 150)]
        for block, (x, y, width, height) in zip(slide.content_blocks[:5], positions):
            cards.append(self._block_card(block, x, y, width, height, foreground, accent))
        return "".join(cards)

    def _chart_focus_blocks(self, slide: SlidePlanItem, foreground: str, accent: str) -> str:
        caption = self._multiline_text(
            text=slide.content_blocks[0].heading if slide.content_blocks else "关键指标",
            x=110,
            y=330,
            max_width=660,
            max_height=88,
            font_size=24,
            fill=foreground,
            max_lines=3,
        )
        return f'''<rect x="80" y="280" width="720" height="280" rx="24" fill="{accent}" fill-opacity="0.08" />
    <polyline points="130,500 240,430 360,450 500,360 650,390 760,320" fill="none" stroke="{accent}" stroke-width="8" />
        {caption}{self._bullet_group(slide, 860, 320, foreground, accent, max_items=4, max_group_height=188)}'''

    def _timeline_blocks(self, slide: SlidePlanItem, foreground: str, accent: str) -> str:
        items = slide.content_blocks[:4]
        timeline: list[str] = [f'<line x1="140" y1="430" x2="1140" y2="430" stroke="{accent}" stroke-width="6" stroke-opacity="0.4" />']
        for index, block in enumerate(items):
            cx = 180 + index * 300
            timeline.append(f'<circle cx="{cx}" cy="430" r="18" fill="{accent}" />')
            timeline.append(
                self._multiline_text(
                    text=block.heading or block.body or f"节点 {index + 1}",
                    x=cx,
                    y=382,
                    max_width=150,
                    max_height=44,
                    font_size=18,
                    fill=foreground,
                    text_anchor="middle",
                    max_lines=2,
                    line_height=1.15,
                )
            )
        return "".join(timeline)

    def _ending_blocks(self, slide: SlidePlanItem, foreground: str, accent: str) -> str:
        body = self._multiline_text(
            text=slide.content_blocks[0].body if slide.content_blocks and slide.content_blocks[0].body else "感谢观看",
            x=640,
            y=380,
            max_width=920,
            max_height=150,
            font_size=44,
            fill=foreground,
            font_weight="700",
            text_anchor="middle",
            max_lines=3,
        )
        return f'''<rect x="80" y="280" width="1120" height="220" rx="36" fill="{accent}" fill-opacity="0.1" />
    {body}'''

    def _block_card(self, block, x: int, y: int, width: int, height: int, foreground: str, accent: str) -> str:
        if block is None:
            heading = "待补充"
            body = ""
        else:
            heading = self._multiline_text(
                text=block.heading or "内容块",
                x=x + 24,
                y=y + 42,
                max_width=width - 48,
                max_height=54,
                font_size=24,
                fill=foreground,
                font_weight="700",
                max_lines=2,
                line_height=1.15,
            )
            body = self._multiline_text(
                text=block.body or "",
                x=x + 24,
                y=y + 86,
                max_width=width - 48,
                max_height=height - 110,
                font_size=18,
                fill=foreground,
                fill_opacity="0.76",
                max_lines=4,
            )
        return f'''<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="24" fill="{accent}" fill-opacity="0.08" />
    {heading}
    {body}'''

    def _bullet_group(
        self,
        slide: SlidePlanItem,
        x: int,
        y: int,
        foreground: str,
        accent: str,
        max_items: int,
        max_group_height: int,
    ) -> str:
        bullets: list[str] = []
        cursor = y
        bottom_limit = y + max_group_height
        collected: list[str] = []
        for block in slide.content_blocks:
            collected.extend(block.bullets)
        for item in collected[:max_items]:
            line_count = max(len(self._wrap_text(item, max_width=280, font_size=18, max_lines=2)), 1)
            item_height = max(16 + int(line_count * 18 * 1.2), 22)
            if cursor + item_height > bottom_limit:
                break
            label = self._multiline_text(
                text=item,
                x=x + 24,
                y=cursor,
                max_width=280,
                max_height=44,
                font_size=18,
                fill=foreground,
                max_lines=2,
                line_height=1.2,
            )
            bullets.append(f'<circle cx="{x + 8}" cy="{cursor - 6}" r="5" fill="{accent}" />{label}')
            cursor += item_height
        return "".join(bullets)

    def _multiline_text(
        self,
        text: str,
        x: int,
        y: int,
        max_width: int,
        max_height: int | None,
        font_size: int,
        fill: str,
        *,
        fill_opacity: str | None = None,
        font_weight: str | None = None,
        text_anchor: str | None = None,
        max_lines: int = 3,
        line_height: float = 1.35,
    ) -> str:
        lines = self._wrap_text(
            text,
            max_width=max_width,
            font_size=font_size,
            max_lines=max_lines,
            max_height=max_height,
            line_height=line_height,
        )
        if not lines:
            return ""

        attributes = [
            f'x="{x}"',
            f'y="{y}"',
            f'font-size="{font_size}"',
            'font-family="Arial"',
            f'fill="{fill}"',
            f'data-max-width="{max_width}"',
            f'data-line-height="{line_height}"',
        ]
        if max_height is not None:
            attributes.append(f'data-max-height="{max_height}"')
        if fill_opacity is not None:
            attributes.append(f'fill-opacity="{fill_opacity}"')
        if font_weight is not None:
            attributes.append(f'font-weight="{font_weight}"')
        if text_anchor is not None:
            attributes.append(f'text-anchor="{text_anchor}"')

        dy = round(font_size * line_height, 1)
        tspans = [escape(lines[0])]
        for line in lines[1:]:
            tspans.append(f'<tspan x="{x}" dy="{dy}">{escape(line)}</tspan>')
        joined_attributes = " ".join(attributes)
        joined_tspans = "".join(tspans)
        return f'<text {joined_attributes}>{joined_tspans}</text>'

    def _wrap_text(
        self,
        text: str,
        max_width: int,
        font_size: int,
        max_lines: int,
        max_height: int | None = None,
        line_height: float = 1.35,
    ) -> list[str]:
        raw = " ".join((text or "").strip().split())
        if not raw:
            return []

        estimated_capacity = max(int(max_width / (font_size * 0.56)), 1)
        height_limited_lines = None
        if max_height is not None:
            per_line_height = max(font_size * line_height, 1)
            height_limited_lines = max(int((max_height + (per_line_height - font_size)) / per_line_height), 1)
        effective_max_lines = min(max_lines, height_limited_lines) if height_limited_lines is not None else max_lines
        words = raw.split(" ")
        lines: list[str] = []
        current = ""

        for word in words:
            candidate = word if not current else f"{current} {word}"
            if len(candidate) <= estimated_capacity:
                current = candidate
                continue
            if current:
                lines.append(current)
                current = word
            else:
                lines.append(word[:estimated_capacity])
                current = word[estimated_capacity:]
            if len(lines) >= effective_max_lines:
                break

        if len(lines) < effective_max_lines and current:
            lines.append(current)

        truncated = len(lines) > effective_max_lines
        lines = lines[:effective_max_lines]

        consumed = " ".join(lines)
        if truncated or len(consumed) < len(raw):
            last = lines[-1]
            if len(last) >= estimated_capacity:
                last = last[: max(estimated_capacity - 1, 1)].rstrip()
            lines[-1] = last.rstrip(" .,") + "…"
        return lines
