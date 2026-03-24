from __future__ import annotations

from core_types import Outline, OutlineSection, PresentationBrief

from methodology_engine.slide_planner import SlidePlanner


def test_slide_planner_emits_structured_design_hints_from_brief() -> None:
    planner = SlidePlanner()
    brief = PresentationBrief(
        project_id="project-1",
        source_bundle_id="source-1",
        presentation_goal="Explain an AI product strategy",
        target_audience="technology leadership team",
        core_message="A focused platform strategy improves delivery speed",
        storyline="Problem -> Architecture -> Rollout",
        tone="technology",
        style_preferences=["technology", "dark", "grid"],
    )
    outline = Outline(
        project_id="project-1",
        brief_id=brief.id,
        title="AI Product Strategy",
        chapters=[
            OutlineSection(
                section_id="section-1",
                title="Executive Summary",
                objective="Summarize the strategic case",
                key_message="Platform investment is the fastest route to scale",
                supporting_points=["Speed", "Consistency", "Governance"],
            ),
            OutlineSection(
                section_id="section-2",
                title="Architecture Roadmap",
                objective="Show the delivery sequence",
                key_message="Capability rollout should follow dependency order",
                supporting_points=["Foundation", "Shared services", "Experience layer"],
            ),
        ],
    )

    slide_plan = planner.generate(
        project_id="project-1",
        brief=brief,
        outline=outline,
        preferred_template_id=None,
    )

    assert slide_plan.design_direction == "technology dark product"
    assert slide_plan.metadata["scenario_tags"] == ["technology", "product", "architecture"]
    assert slide_plan.metadata["style_tags"] == ["technology", "dark", "grid"]
    assert slide_plan.metadata["audience_tag"] == "technology leadership team"


def test_slide_planner_uses_explicit_template_as_design_direction() -> None:
    planner = SlidePlanner()
    brief = PresentationBrief(
        project_id="project-2",
        source_bundle_id="source-2",
        presentation_goal="Prepare a formal policy report",
        target_audience="regional policy office",
        core_message="A clear operating model reduces execution risk",
        storyline="Context -> Analysis -> Recommendation",
        tone="formal",
        style_preferences=["formal", "clean"],
    )
    outline = Outline(
        project_id="project-2",
        brief_id=brief.id,
        title="Policy Report",
        chapters=[
            OutlineSection(
                section_id="section-1",
                title="Regional Context",
                objective="Set the baseline",
                key_message="Regional conditions require phased execution",
                supporting_points=["Policy context", "Economic base", "Execution constraints"],
            )
        ],
    )

    slide_plan = planner.generate(
        project_id="project-2",
        brief=brief,
        outline=outline,
        preferred_template_id="government-blue",
    )

    assert slide_plan.design_direction == "government-blue"
    assert slide_plan.metadata["preferred_template_id"] == "government-blue"
    assert "policy" in slide_plan.metadata["scenario_tags"]