from __future__ import annotations

from app.services.svg_renderer import SvgRenderer
from core_types import ContentBlock, SlidePlan, SlidePlanItem, TemplateMeta
from core_types.enums import LayoutMode


def _template() -> TemplateMeta:
    return TemplateMeta(
        id="template-1",
        template_id="technology-grid",
        name="Technology Grid",
        style_tags=["technology"],
        scenario_tags=["product_demo"],
        supported_layout_modes=[
            LayoutMode.HERO,
            LayoutMode.TOC,
            LayoutMode.TIMELINE,
        ],
        color_scheme=["#0F172A", "#F8FAFC", "#0EA5E9"],
        design_spec_path="templates/builtin/technology-grid.design.json",
        metadata={"title_font": "Arial"},
    )


def test_renderer_wraps_bullets_into_tspans() -> None:
    slide = SlidePlanItem(
        slide_id="slide-hero",
        slide_number=1,
        title="Hero",
        conclusion="Summary",
        layout_mode=LayoutMode.HERO,
        content_blocks=[
            ContentBlock(
                block_id="block-hero-1",
                block_type="summary",
                heading="Overview",
                body="A short summary.",
                bullets=[
                    "This bullet is intentionally long so the renderer needs to wrap it into a second line instead of truncating it immediately."
                ],
            )
        ],
    )
    slide_plan = SlidePlan(
        id="plan-1",
        project_id="project-1",
        brief_id="brief-1",
        outline_id="outline-1",
        page_count=1,
        slides=[slide],
    )

    page = SvgRenderer().render(slide_plan=slide_plan, template=_template()).pages[0]

    assert "<tspan" in page.svg_content
    assert 'data-max-width="280"' in page.svg_content


def test_renderer_clamps_bullet_group_to_available_height() -> None:
    slide = SlidePlanItem(
        slide_id="slide-hero-bullets",
        slide_number=1,
        title="Hero",
        conclusion="Summary",
        layout_mode=LayoutMode.HERO,
        content_blocks=[
            ContentBlock(
                block_id="block-hero-bullets",
                block_type="summary",
                heading="Overview",
                body="A short summary.",
                bullets=[
                    "Bullet one is long enough to consume two wrapped lines inside the narrow right sidebar area.",
                    "Bullet two is also deliberately long so it takes another tall slot in the same grouped bullet region.",
                    "Bullet three should still fit within the declared group budget when the prior two have already used significant height.",
                    "Bullet four is expected to be dropped because the group height budget should stop rendering before this item.",
                ],
            )
        ],
    )
    slide_plan = SlidePlan(
        id="plan-bullets-1",
        project_id="project-1",
        brief_id="brief-1",
        outline_id="outline-1",
        page_count=1,
        slides=[slide],
    )

    page = SvgRenderer().render(slide_plan=slide_plan, template=_template()).pages[0]

    assert "Bullet one is long enough" in page.svg_content
    assert "Bullet two is also deliberately long" not in page.svg_content
    assert "Bullet three should still fit" not in page.svg_content
    assert "Bullet four is expected to be dropped" not in page.svg_content


def test_renderer_wraps_toc_and_timeline_labels() -> None:
    toc_slide = SlidePlanItem(
        slide_id="slide-toc",
        slide_number=1,
        title="Agenda",
        conclusion="Navigation",
        layout_mode=LayoutMode.TOC,
        content_blocks=[
            ContentBlock(
                block_id="block-toc-1",
                block_type="agenda_item",
                heading="A deliberately long agenda label that should wrap into two lines for readability in the table of contents",
                body="",
                bullets=[],
            )
        ],
    )
    timeline_slide = SlidePlanItem(
        slide_id="slide-timeline",
        slide_number=2,
        title="Timeline",
        conclusion="Phases",
        layout_mode=LayoutMode.TIMELINE,
        content_blocks=[
            ContentBlock(
                block_id="block-timeline-1",
                block_type="milestone",
                heading="A long milestone label that should wrap above the timeline marker",
                body="",
                bullets=[],
            )
        ],
    )
    slide_plan = SlidePlan(
        id="plan-2",
        project_id="project-1",
        brief_id="brief-1",
        outline_id="outline-1",
        page_count=2,
        slides=[toc_slide, timeline_slide],
    )

    result = SvgRenderer().render(slide_plan=slide_plan, template=_template())

    toc_svg = result.pages[0].svg_content
    timeline_svg = result.pages[1].svg_content

    assert 'data-max-width="1040"' in toc_svg
    assert 'data-max-height="58"' in toc_svg
    assert "01. A deliberately long agenda label" in toc_svg
    assert '<text x="180" y="382"' in timeline_svg
    assert 'text-anchor="middle"' in timeline_svg
    assert 'data-max-height="44"' in timeline_svg
    assert '<tspan x="180"' in timeline_svg


def test_renderer_keeps_second_timeline_label_line_reachable() -> None:
    timeline_slide = SlidePlanItem(
        slide_id="slide-timeline-wrap",
        slide_number=1,
        title="Timeline",
        conclusion="Phases",
        layout_mode=LayoutMode.TIMELINE,
        content_blocks=[
            ContentBlock(
                block_id="block-timeline-wrap-1",
                block_type="milestone",
                heading="A long milestone label that should wrap into a second line above the timeline marker without being height-clamped away.",
                body="",
                bullets=[],
            )
        ],
    )
    slide_plan = SlidePlan(
        id="plan-timeline-wrap",
        project_id="project-1",
        brief_id="brief-1",
        outline_id="outline-1",
        page_count=1,
        slides=[timeline_slide],
    )

    page = SvgRenderer().render(slide_plan=slide_plan, template=_template()).pages[0]

    assert '<text x="180" y="382"' in page.svg_content
    assert 'data-max-height="44"' in page.svg_content
    assert '<tspan x="180" dy="20.7">' in page.svg_content


def test_renderer_offsets_following_toc_items_after_wrapped_entry() -> None:
    toc_slide = SlidePlanItem(
        slide_id="slide-toc-spacing",
        slide_number=1,
        title="Agenda",
        conclusion="Navigation",
        layout_mode=LayoutMode.TOC,
        content_blocks=[
            ContentBlock(
                block_id="block-toc-spacing-1",
                block_type="agenda_item",
                heading="A deliberately long agenda label that should wrap into two lines because it repeats the same visual idea several times and keeps extending well beyond the available width for a single TOC row in this template.",
                body="",
                bullets=[],
            ),
            ContentBlock(
                block_id="block-toc-spacing-2",
                block_type="agenda_item",
                heading="Short follow-up item",
                body="",
                bullets=[],
            ),
        ],
    )
    slide_plan = SlidePlan(
        id="plan-toc-spacing",
        project_id="project-1",
        brief_id="brief-1",
        outline_id="outline-1",
        page_count=1,
        slides=[toc_slide],
    )

    page = SvgRenderer().render(slide_plan=slide_plan, template=_template()).pages[0]

    assert '<text x="120" y="290"' in page.svg_content
    assert '<tspan x="120" dy="28.8">' in page.svg_content
    assert '<text x="120" y="371"' in page.svg_content
    assert "02. Short follow-up item" in page.svg_content


def test_renderer_clamps_lines_by_declared_height() -> None:
    renderer = SvgRenderer()

    text = renderer._multiline_text(
        text="This content is intentionally long enough to require several wrapped lines, but the available height should clamp it to a single visible line.",
        x=104,
        y=320,
        max_width=220,
        max_height=20,
        font_size=18,
        fill="#0F172A",
        max_lines=4,
        line_height=1.2,
    )

    assert 'data-max-height="20"' in text
    assert 'data-line-height="1.2"' in text
    assert text.count("<tspan") == 0
    assert "…" in text


def test_renderer_wraps_slide_title_and_card_heading_with_height_limits() -> None:
    slide = SlidePlanItem(
        slide_id="slide-two-column",
        slide_number=1,
        title="A presentation title that is long enough to require wrapping across two lines in the slide header area",
        conclusion="A subtitle that also needs wrapping instead of silently overflowing beyond the reserved header band",
        layout_mode=LayoutMode.TWO_COLUMN,
        content_blocks=[
            ContentBlock(
                block_id="block-card-1",
                block_type="insight",
                heading="An intentionally long card heading that should wrap inside the card instead of truncating to a brittle single line",
                body="Supporting copy.",
                bullets=[],
            )
        ],
    )
    slide_plan = SlidePlan(
        id="plan-3",
        project_id="project-1",
        brief_id="brief-1",
        outline_id="outline-1",
        page_count=1,
        slides=[slide],
    )

    page = SvgRenderer().render(slide_plan=slide_plan, template=_template()).pages[0]

    assert 'font-size="38"' in page.svg_content
    assert 'data-max-height="92"' in page.svg_content
    assert 'data-max-height="48"' in page.svg_content
    assert 'data-max-height="54"' in page.svg_content
    assert page.svg_content.count("<tspan") >= 2


def test_renderer_keeps_second_subtitle_line_reachable() -> None:
    slide = SlidePlanItem(
        slide_id="slide-subtitle-wrap",
        slide_number=1,
        title="Short title",
        conclusion="A subtitle that also needs wrapping instead of silently overflowing beyond the reserved header band and should prove whether the second line is reachable.",
        layout_mode=LayoutMode.HERO,
        content_blocks=[
            ContentBlock(
                block_id="block-subtitle-wrap-1",
                block_type="summary",
                heading="Overview",
                body="Short body.",
                bullets=[],
            )
        ],
    )
    slide_plan = SlidePlan(
        id="plan-subtitle-wrap",
        project_id="project-1",
        brief_id="brief-1",
        outline_id="outline-1",
        page_count=1,
        slides=[slide],
    )

    page = SvgRenderer().render(slide_plan=slide_plan, template=_template()).pages[0]

    assert '<text x="80" y="230"' in page.svg_content
    assert 'data-max-height="48"' in page.svg_content
    assert '<tspan x="80" dy="24.0">' in page.svg_content


def test_renderer_keeps_second_card_heading_line_reachable() -> None:
    slide = SlidePlanItem(
        slide_id="slide-card-heading-wrap",
        slide_number=1,
        title="Two Column",
        conclusion="Subtitle",
        layout_mode=LayoutMode.TWO_COLUMN,
        content_blocks=[
            ContentBlock(
                block_id="block-card-heading-wrap-1",
                block_type="insight",
                heading="A card heading that is deliberately long enough to need a second line inside the compact card title area for this renderer test.",
                body="Supporting copy.",
                bullets=[],
            )
        ],
    )
    slide_plan = SlidePlan(
        id="plan-card-heading-wrap",
        project_id="project-1",
        brief_id="brief-1",
        outline_id="outline-1",
        page_count=1,
        slides=[slide],
    )

    page = SvgRenderer().render(slide_plan=slide_plan, template=_template()).pages[0]

    assert '<text x="104" y="322"' in page.svg_content
    assert 'data-max-height="54"' in page.svg_content
    assert '<tspan x="104" dy="27.6">' in page.svg_content


def test_renderer_applies_height_limits_to_layout_label_and_footer() -> None:
    slide = SlidePlanItem(
        slide_id="slide-footer",
        slide_number=7,
        title="Summary",
        conclusion="Closing remarks",
        layout_mode=LayoutMode.CHART_FOCUS,
        content_blocks=[
            ContentBlock(
                block_id="block-footer-1",
                block_type="metric",
                heading="Metric heading",
                body="Body",
                bullets=[],
            )
        ],
    )
    slide_plan = SlidePlan(
        id="plan-4",
        project_id="project-1",
        brief_id="brief-1",
        outline_id="outline-1",
        page_count=12,
        slides=[slide],
    )

    page = SvgRenderer().render(slide_plan=slide_plan, template=_template()).pages[0]

    assert '<text x="80" y="110"' in page.svg_content
    assert 'data-max-height="24"' in page.svg_content
    assert '<text x="80" y="685"' in page.svg_content
    assert 'data-max-height="22"' in page.svg_content
    assert "7/12 Technology Grid" in page.svg_content


def test_renderer_applies_height_limits_to_section_number() -> None:
    slide = SlidePlanItem(
        slide_id="slide-section",
        slide_number=3,
        title="Section Title",
        conclusion="Divider",
        layout_mode=LayoutMode.SECTION,
        content_blocks=[
            ContentBlock(
                block_id="block-section-1",
                block_type="section_intro",
                heading="A section title that still needs bounded layout behavior on the right side",
                body="",
                bullets=[],
            )
        ],
    )
    slide_plan = SlidePlan(
        id="plan-5",
        project_id="project-1",
        brief_id="brief-1",
        outline_id="outline-1",
        page_count=6,
        slides=[slide],
    )

    page = SvgRenderer().render(slide_plan=slide_plan, template=_template()).pages[0]

    assert '<text x="120" y="380"' in page.svg_content
    assert 'font-size="56"' in page.svg_content
    assert 'data-max-width="120"' in page.svg_content
    assert 'data-max-height="64"' in page.svg_content
    assert 'data-line-height="1.0"' in page.svg_content
    assert '>03</text>' in page.svg_content


def test_renderer_keeps_second_section_title_line_reachable() -> None:
    slide = SlidePlanItem(
        slide_id="slide-section-wrap",
        slide_number=3,
        title="Section Title",
        conclusion="Divider",
        layout_mode=LayoutMode.SECTION,
        content_blocks=[
            ContentBlock(
                block_id="block-section-wrap-1",
                block_type="section_intro",
                heading="A section title that is deliberately long enough to need a second line inside the right-side title area for this renderer test.",
                body="",
                bullets=[],
            )
        ],
    )
    slide_plan = SlidePlan(
        id="plan-section-wrap",
        project_id="project-1",
        brief_id="brief-1",
        outline_id="outline-1",
        page_count=6,
        slides=[slide],
    )

    page = SvgRenderer().render(slide_plan=slide_plan, template=_template()).pages[0]

    assert '<text x="650" y="350"' in page.svg_content
    assert 'data-max-height="108"' in page.svg_content
    assert '<tspan x="650" dy="39.1">' in page.svg_content


def test_renderer_keeps_second_chart_caption_line_reachable() -> None:
    slide = SlidePlanItem(
        slide_id="slide-chart-caption-wrap",
        slide_number=4,
        title="Chart Focus",
        conclusion="Key metric",
        layout_mode=LayoutMode.CHART_FOCUS,
        content_blocks=[
            ContentBlock(
                block_id="block-chart-caption-wrap-1",
                block_type="metric",
                heading="A chart caption that is intentionally long enough to require a second line inside the chart focus annotation area for this renderer test.",
                body="Body",
                bullets=[],
            )
        ],
    )
    slide_plan = SlidePlan(
        id="plan-chart-caption-wrap",
        project_id="project-1",
        brief_id="brief-1",
        outline_id="outline-1",
        page_count=6,
        slides=[slide],
    )

    page = SvgRenderer().render(slide_plan=slide_plan, template=_template()).pages[0]

    assert '<text x="110" y="330"' in page.svg_content
    assert 'data-max-height="88"' in page.svg_content
    assert '<tspan x="110" dy="32.4">' in page.svg_content


def test_renderer_keeps_third_hero_summary_line_reachable() -> None:
    slide = SlidePlanItem(
        slide_id="slide-hero-summary-wrap",
        slide_number=1,
        title="Hero",
        conclusion="Summary",
        layout_mode=LayoutMode.HERO,
        content_blocks=[
            ContentBlock(
                block_id="block-hero-summary-wrap-1",
                block_type="summary",
                heading="Overview",
                body="A hero summary paragraph that is deliberately long enough to need a second and likely third line inside the right-side summary card so we can verify whether the declared text height remains genuinely reachable under the current wrapping formula.",
                bullets=[],
            )
        ],
    )
    slide_plan = SlidePlan(
        id="plan-hero-summary-wrap",
        project_id="project-1",
        brief_id="brief-1",
        outline_id="outline-1",
        page_count=2,
        slides=[slide],
    )

    page = SvgRenderer().render(slide_plan=slide_plan, template=_template()).pages[0]

    assert '<text x="800" y="330"' in page.svg_content
    assert 'data-max-height="120"' in page.svg_content
    assert page.svg_content.count('<tspan x="800" dy="32.4">') >= 2


def test_renderer_keeps_fourth_card_body_line_reachable() -> None:
    slide = SlidePlanItem(
        slide_id="slide-card-body-wrap",
        slide_number=2,
        title="Two Column",
        conclusion="Summary",
        layout_mode=LayoutMode.TWO_COLUMN,
        content_blocks=[
            ContentBlock(
                block_id="block-card-body-wrap-1",
                block_type="insight",
                heading="Short heading",
                body="Supporting copy inside the insight card is intentionally long enough to require multiple wrapped lines so this probe can confirm whether the declared card body height truly permits the extra lines instead of silently clamping to one.",
                bullets=[],
            )
        ],
    )
    slide_plan = SlidePlan(
        id="plan-card-body-wrap",
        project_id="project-1",
        brief_id="brief-1",
        outline_id="outline-1",
        page_count=2,
        slides=[slide],
    )

    page = SvgRenderer().render(slide_plan=slide_plan, template=_template()).pages[0]

    assert '<text x="104" y="366"' in page.svg_content
    assert 'data-max-height="150"' in page.svg_content
    assert page.svg_content.count('<tspan x="104" dy="24.3">') >= 3


def test_renderer_keeps_fourth_cover_body_line_reachable() -> None:
    slide = SlidePlanItem(
        slide_id="slide-cover-body-wrap",
        slide_number=1,
        title="Cover",
        conclusion="Intro",
        layout_mode=LayoutMode.COVER,
        content_blocks=[
            ContentBlock(
                block_id="block-cover-body-wrap-1",
                block_type="intro",
                heading="Overview",
                body="A cover body paragraph that is intentionally long enough to require multiple wrapped lines so we can verify whether the cover introduction area really preserves the declared height budget under the current renderer rules.",
                bullets=[],
            )
        ],
    )
    slide_plan = SlidePlan(
        id="plan-cover-body-wrap",
        project_id="project-1",
        brief_id="brief-1",
        outline_id="outline-1",
        page_count=2,
        slides=[slide],
    )

    page = SvgRenderer().render(slide_plan=slide_plan, template=_template()).pages[0]

    assert '<text x="80" y="330"' in page.svg_content
    assert 'data-max-height="130"' in page.svg_content
    assert page.svg_content.count('<tspan x="80" dy="29.7">') >= 3


def test_renderer_keeps_second_ending_body_line_reachable() -> None:
    slide = SlidePlanItem(
        slide_id="slide-ending-body-wrap",
        slide_number=2,
        title="Ending",
        conclusion="Thanks",
        layout_mode=LayoutMode.ENDING,
        content_blocks=[
            ContentBlock(
                block_id="block-ending-body-wrap-1",
                block_type="closing",
                heading="Closing",
                body="A closing statement that is intentionally long enough to require a second line inside the ending slide panel so we can verify whether the large centered body budget remains truly reachable.",
                bullets=[],
            )
        ],
    )
    slide_plan = SlidePlan(
        id="plan-ending-body-wrap",
        project_id="project-1",
        brief_id="brief-1",
        outline_id="outline-1",
        page_count=2,
        slides=[slide],
    )

    page = SvgRenderer().render(slide_plan=slide_plan, template=_template()).pages[0]

    assert '<text x="640" y="380"' in page.svg_content
    assert 'data-max-height="150"' in page.svg_content
    assert '<tspan x="640" dy="59.4">' in page.svg_content
