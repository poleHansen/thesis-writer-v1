from __future__ import annotations

from core_types import ContentBlock, Outline, PresentationBrief, SlidePlan, SlidePlanItem
from core_types.enums import LayoutMode, ReviewStatus


class SlidePlanner:
    def generate(
        self,
        *,
        project_id: str,
        brief: PresentationBrief,
        outline: Outline,
        preferred_template_id: str | None,
    ) -> SlidePlan:
        slides = self._build_slide_plan_items(outline, brief)
        return SlidePlan(
            project_id=project_id,
            brief_id=brief.id,
            outline_id=outline.id,
            page_count=len(slides),
            slides=slides,
            design_direction=preferred_template_id or "methodology-engine planned",
            status=ReviewStatus.DRAFT,
            metadata={
                "generation_mode": "methodology_engine_v1",
                "source": "outline",
                "planning_principles": [
                    "single_conclusion_per_slide",
                    "controlled_information_density",
                    "limited_content_blocks",
                    "layout_matches_content_type",
                ],
                "supported_layout_modes": [mode.value for mode in LayoutMode],
            },
        )

    def _build_slide_plan_items(self, outline: Outline, brief: PresentationBrief) -> list[SlidePlanItem]:
        chapters = outline.chapters
        if not chapters:
            return []

        slides: list[SlidePlanItem] = []
        total = len(chapters)
        for index, chapter in enumerate(chapters, start=1):
            layout_mode = self._select_layout_mode(index=index, total=total, title=chapter.title)
            bullets = chapter.supporting_points[:3] if chapter.supporting_points else [brief.core_message]
            content_blocks = self._build_content_blocks(
                slide_id=f"slide-{index}",
                layout_mode=layout_mode,
                chapter_title=chapter.title,
                objective=chapter.objective,
                conclusion=chapter.key_message,
                bullets=bullets,
            )
            slides.append(
                SlidePlanItem(
                    slide_id=f"slide-{index}",
                    slide_number=index,
                    title=chapter.title,
                    conclusion=chapter.key_message,
                    layout_mode=layout_mode,
                    content_blocks=content_blocks,
                    speaker_notes=f"Keep the slide anchored on one conclusion: {chapter.key_message}",
                    data_refs=[],
                    visual_priority=self._visual_priority(layout_mode),
                )
            )
        return slides

    def _select_layout_mode(self, *, index: int, total: int, title: str) -> LayoutMode:
        normalized = title.lower()
        if index == 1:
            return LayoutMode.COVER
        if index == 2:
            return LayoutMode.TOC
        if index == total:
            return LayoutMode.ENDING
        if "timeline" in normalized or "roadmap" in normalized or "next step" in normalized:
            return LayoutMode.TIMELINE
        if "recommendation" in normalized or "choice" in normalized:
            return LayoutMode.HERO
        if "evidence" in normalized or "analysis" in normalized:
            return LayoutMode.CHART_FOCUS
        if "context" in normalized or "scenario" in normalized:
            return LayoutMode.SECTION
        if index % 3 == 0:
            return LayoutMode.BENTO
        return LayoutMode.TWO_COLUMN

    def _build_content_blocks(
        self,
        *,
        slide_id: str,
        layout_mode: LayoutMode,
        chapter_title: str,
        objective: str,
        conclusion: str,
        bullets: list[str],
    ) -> list[ContentBlock]:
        limited_bullets = bullets[:3]
        if layout_mode == LayoutMode.COVER:
            return [
                ContentBlock(
                    block_id=f"{slide_id}-hero",
                    block_type="hero",
                    heading=chapter_title,
                    body=conclusion,
                    bullets=limited_bullets[:2],
                    asset_refs=[],
                    chart_hint=None,
                    emphasis="primary",
                )
            ]
        if layout_mode == LayoutMode.TOC:
            return [
                ContentBlock(
                    block_id=f"{slide_id}-toc",
                    block_type="agenda",
                    heading="Presentation Flow",
                    body=objective,
                    bullets=limited_bullets,
                    asset_refs=[],
                    chart_hint=None,
                    emphasis="primary",
                )
            ]
        if layout_mode == LayoutMode.CHART_FOCUS:
            return [
                ContentBlock(
                    block_id=f"{slide_id}-insight",
                    block_type="insight",
                    heading=chapter_title,
                    body=conclusion,
                    bullets=[],
                    asset_refs=[],
                    chart_hint="compare key evidence",
                    emphasis="primary",
                ),
                ContentBlock(
                    block_id=f"{slide_id}-evidence",
                    block_type="evidence",
                    heading="Key Evidence",
                    body=None,
                    bullets=limited_bullets,
                    asset_refs=[],
                    chart_hint="bar_or_line",
                    emphasis="secondary",
                ),
            ]
        if layout_mode == LayoutMode.TIMELINE:
            return [
                ContentBlock(
                    block_id=f"{slide_id}-timeline",
                    block_type="timeline",
                    heading=chapter_title,
                    body=objective,
                    bullets=limited_bullets,
                    asset_refs=[],
                    chart_hint="timeline",
                    emphasis="primary",
                )
            ]
        if layout_mode == LayoutMode.BENTO:
            return [
                ContentBlock(
                    block_id=f"{slide_id}-summary",
                    block_type="summary",
                    heading=chapter_title,
                    body=conclusion,
                    bullets=limited_bullets[:1],
                    asset_refs=[],
                    chart_hint=None,
                    emphasis="primary",
                ),
                ContentBlock(
                    block_id=f"{slide_id}-details",
                    block_type="detail",
                    heading="Supporting Points",
                    body=None,
                    bullets=limited_bullets[1:3],
                    asset_refs=[],
                    chart_hint=None,
                    emphasis="secondary",
                ),
            ]
        if layout_mode == LayoutMode.SECTION:
            return [
                ContentBlock(
                    block_id=f"{slide_id}-section",
                    block_type="section",
                    heading=chapter_title,
                    body=objective,
                    bullets=limited_bullets,
                    asset_refs=[],
                    chart_hint=None,
                    emphasis="primary",
                )
            ]
        if layout_mode == LayoutMode.HERO:
            return [
                ContentBlock(
                    block_id=f"{slide_id}-recommendation",
                    block_type="recommendation",
                    heading=chapter_title,
                    body=conclusion,
                    bullets=limited_bullets,
                    asset_refs=[],
                    chart_hint=None,
                    emphasis="primary",
                )
            ]
        if layout_mode == LayoutMode.ENDING:
            return [
                ContentBlock(
                    block_id=f"{slide_id}-ending",
                    block_type="ending",
                    heading="Next Step",
                    body=conclusion,
                    bullets=limited_bullets[:2],
                    asset_refs=[],
                    chart_hint=None,
                    emphasis="primary",
                )
            ]
        return [
            ContentBlock(
                block_id=f"{slide_id}-summary",
                block_type="summary",
                heading=objective,
                body=conclusion,
                bullets=limited_bullets,
                asset_refs=[],
                chart_hint=None,
                emphasis="primary",
            )
        ]

    def _visual_priority(self, layout_mode: LayoutMode) -> str:
        if layout_mode in {LayoutMode.COVER, LayoutMode.HERO, LayoutMode.ENDING}:
            return "high"
        if layout_mode in {LayoutMode.CHART_FOCUS, LayoutMode.BENTO, LayoutMode.TIMELINE}:
            return "medium"
        return "balanced"