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
    render_status: RenderStatus = RenderStatus.PENDING
    log_path: str | None = None


class SvgRenderer:
    def render(self, slide_plan: SlidePlan, template: TemplateMeta) -> SvgRenderResult:
        pages: list[RenderedSvgPage] = []
        failed_slide_ids: list[str] = []
        for slide in slide_plan.slides:
            try:
                pages.append(
                    RenderedSvgPage(
                        slide_id=slide.slide_id,
                        slide_number=slide.slide_number,
                        svg_content=self._render_slide(slide, template, slide_plan.page_count),
                    )
                )
            except Exception:
                failed_slide_ids.append(slide.slide_id)

        render_status = RenderStatus.SUCCEEDED if not failed_slide_ids else RenderStatus.PARTIAL
        if not pages:
            render_status = RenderStatus.FAILED
        return SvgRenderResult(pages=pages, failed_slide_ids=failed_slide_ids, render_status=render_status)

    def _render_slide(self, slide: SlidePlanItem, template: TemplateMeta, total_pages: int) -> str:
        palette = template.color_scheme or ["#0F172A", "#F8FAFC", "#0EA5E9"]
        background = palette[1] if len(palette) > 1 else "#F8FAFC"
        foreground = palette[0]
        accent = palette[2] if len(palette) > 2 else "#0EA5E9"
        blocks = self._render_blocks(slide, foreground, accent)
        footer = escape(f"{slide.slide_number}/{total_pages}  {template.name}")
        subtitle = escape(slide.conclusion)
        title = escape(slide.title)

        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <rect width="1280" height="720" fill="{background}" />
  <rect x="0" y="0" width="1280" height="18" fill="{accent}" />
  <text x="80" y="110" font-size="20" font-family="Arial" fill="{accent}">{escape(slide.layout_mode.value)}</text>
  <text x="80" y="170" font-size="38" font-family="Arial" font-weight="700" fill="{foreground}">{title}</text>
  <text x="80" y="215" font-size="20" font-family="Arial" fill="{foreground}" fill-opacity="0.72">{subtitle}</text>
  {blocks}
  <line x1="80" y1="650" x2="1200" y2="650" stroke="{foreground}" stroke-opacity="0.18" />
  <text x="80" y="685" font-size="18" font-family="Arial" fill="{foreground}" fill-opacity="0.65">{footer}</text>
</svg>'''

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
        body = escape(slide.content_blocks[0].body) if slide.content_blocks and slide.content_blocks[0].body else ""
        return f'''<circle cx="1030" cy="180" r="120" fill="{accent}" fill-opacity="0.12" />
  <circle cx="1120" cy="260" r="70" fill="{accent}" fill-opacity="0.22" />
  <text x="80" y="330" font-size="22" font-family="Arial" fill="{foreground}" fill-opacity="0.78">{body}</text>'''

    def _toc_blocks(self, slide: SlidePlanItem, foreground: str, accent: str) -> str:
        items: list[str] = []
        for index, block in enumerate(slide.content_blocks[:6], start=1):
            label = escape(block.heading or block.body or f"目录 {index}")
            y = 290 + (index - 1) * 48
            items.append(f'<text x="120" y="{y}" font-size="24" font-family="Arial" fill="{foreground}">{index:02d}. {label}</text>')
        return f'<rect x="80" y="250" width="1120" height="320" rx="24" fill="{accent}" fill-opacity="0.08" />' + "".join(items)

    def _section_blocks(self, slide: SlidePlanItem, foreground: str, accent: str) -> str:
        return f'''<rect x="80" y="280" width="520" height="220" rx="32" fill="{accent}" fill-opacity="0.12" />
  <text x="120" y="380" font-size="56" font-family="Arial" font-weight="700" fill="{foreground}">{slide.slide_number:02d}</text>'''

    def _hero_blocks(self, slide: SlidePlanItem, foreground: str, accent: str) -> str:
        summary = escape(slide.content_blocks[0].body) if slide.content_blocks and slide.content_blocks[0].body else ""
        bullets = self._bullet_group(slide, 80, 320, foreground, accent, max_items=4)
        return f'''<rect x="760" y="260" width="420" height="220" rx="28" fill="{accent}" fill-opacity="0.1" />
  <text x="800" y="330" font-size="24" font-family="Arial" fill="{foreground}">{summary}</text>{bullets}'''

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
        caption = escape(slide.content_blocks[0].heading) if slide.content_blocks else "关键指标"
        return f'''<rect x="80" y="280" width="720" height="280" rx="24" fill="{accent}" fill-opacity="0.08" />
  <polyline points="130,500 240,430 360,450 500,360 650,390 760,320" fill="none" stroke="{accent}" stroke-width="8" />
  <text x="110" y="330" font-size="24" font-family="Arial" fill="{foreground}">{caption}</text>{self._bullet_group(slide, 860, 320, foreground, accent, max_items=4)}'''

    def _timeline_blocks(self, slide: SlidePlanItem, foreground: str, accent: str) -> str:
        items = slide.content_blocks[:4]
        timeline: list[str] = [f'<line x1="140" y1="430" x2="1140" y2="430" stroke="{accent}" stroke-width="6" stroke-opacity="0.4" />']
        for index, block in enumerate(items):
            cx = 180 + index * 300
            label = escape(block.heading or block.body or f"节点 {index + 1}")
            timeline.append(f'<circle cx="{cx}" cy="430" r="18" fill="{accent}" />')
            timeline.append(f'<text x="{cx - 40}" y="390" font-size="18" font-family="Arial" fill="{foreground}">{label}</text>')
        return "".join(timeline)

    def _ending_blocks(self, slide: SlidePlanItem, foreground: str, accent: str) -> str:
        body = escape(slide.content_blocks[0].body) if slide.content_blocks and slide.content_blocks[0].body else "感谢观看"
        return f'''<rect x="80" y="280" width="1120" height="220" rx="36" fill="{accent}" fill-opacity="0.1" />
  <text x="640" y="400" text-anchor="middle" font-size="44" font-family="Arial" font-weight="700" fill="{foreground}">{body}</text>'''

    def _block_card(self, block, x: int, y: int, width: int, height: int, foreground: str, accent: str) -> str:
        if block is None:
            heading = "待补充"
            body = ""
        else:
            heading = escape(block.heading or "内容块")
            body = escape(block.body or "")
        return f'''<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="24" fill="{accent}" fill-opacity="0.08" />
  <text x="{x + 24}" y="{y + 42}" font-size="24" font-family="Arial" font-weight="700" fill="{foreground}">{heading}</text>
  <text x="{x + 24}" y="{y + 86}" font-size="18" font-family="Arial" fill="{foreground}" fill-opacity="0.76">{body}</text>'''

    def _bullet_group(self, slide: SlidePlanItem, x: int, y: int, foreground: str, accent: str, max_items: int) -> str:
        bullets: list[str] = []
        cursor = y
        collected: list[str] = []
        for block in slide.content_blocks:
            collected.extend(block.bullets)
        for item in collected[:max_items]:
            label = escape(item)
            bullets.append(f'<circle cx="{x + 8}" cy="{cursor - 6}" r="5" fill="{accent}" /><text x="{x + 24}" y="{cursor}" font-size="18" font-family="Arial" fill="{foreground}">{label}</text>')
            cursor += 34
        return "".join(bullets)