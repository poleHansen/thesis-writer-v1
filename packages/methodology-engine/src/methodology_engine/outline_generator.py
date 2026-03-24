from __future__ import annotations

from core_types import Outline, OutlineSection, PresentationBrief, Project, SourceBundle
from core_types.enums import ReviewStatus


class OutlineGenerator:
    def generate(
        self,
        *,
        project: Project,
        brief: PresentationBrief,
        source_bundle: SourceBundle | None,
    ) -> Outline:
        chapter_titles = self._derive_outline_titles(brief, source_bundle)
        chapter_count = max(3, min(len(chapter_titles), brief.recommended_page_count))
        estimated_slides = max(1, brief.recommended_page_count // chapter_count)
        chapters = [
            OutlineSection(
                section_id=f"section-{index + 1}",
                title=title,
                objective=self._build_objective(title, index),
                key_message=self._build_key_message(title, brief, index),
                supporting_points=self._build_supporting_points(brief, source_bundle, index),
                estimated_slides=estimated_slides,
            )
            for index, title in enumerate(chapter_titles[:chapter_count])
        ]
        return Outline(
            project_id=project.id,
            brief_id=brief.id,
            title=f"{project.name} outline",
            chapters=chapters,
            summary=f"Outline generated from brief {brief.id} with {len(chapters)} chapters.",
            status=ReviewStatus.DRAFT,
            metadata={
                "generation_mode": "methodology_engine_v1",
                "source": "brief",
                "source_mode": source_bundle.source_mode if source_bundle else None,
                "generation_principles": [
                    "mainline_before_chapters",
                    "explicit_chapter_role",
                    "explicit_key_message",
                    "avoid_raw_toc_copy",
                ],
            },
        )

    def _derive_outline_titles(self, brief: PresentationBrief, source_bundle: SourceBundle | None) -> list[str]:
        titles = [
            "Context and Problem",
            "What Matters Most",
            "Evidence and Analysis",
            "Implications and Choices",
            "Recommendation and Next Steps",
        ]
        if source_bundle and source_bundle.user_intent and source_bundle.user_intent.scenario:
            titles[0] = "Scenario and Core Challenge"
        if brief.target_audience.lower() not in {"general audience", "general"}:
            titles[1] = "Audience Priorities"
        return titles

    def _build_objective(self, title: str, index: int) -> str:
        objectives = [
            "Establish the presentation mainline and stakes",
            "Clarify the decision focus and evaluation lens",
            "Present the strongest supporting evidence",
            "Explain tradeoffs, impacts, and implications",
            "Drive toward a concrete takeaway and action",
        ]
        return objectives[min(index, len(objectives) - 1)] if title else objectives[min(index, len(objectives) - 1)]

    def _build_key_message(self, title: str, brief: PresentationBrief, index: int) -> str:
        if index == 0:
            return f"The presentation should anchor on: {brief.core_message}"
        if index == 1:
            return f"{title} defines what the audience must understand before details."
        if index == 2:
            return f"{title} substantiates the storyline with the most relevant evidence."
        if index == 3:
            return f"{title} turns findings into interpretable decisions and tradeoffs."
        return f"{title} converts the storyline into a final recommendation."

    def _build_supporting_points(self, brief: PresentationBrief, source_bundle: SourceBundle | None, index: int) -> list[str]:
        points: list[str] = [brief.presentation_goal, brief.storyline, f"Audience focus: {brief.target_audience}"]
        if source_bundle and source_bundle.citations:
            points.append(f"Evidence source: {source_bundle.citations[min(index, len(source_bundle.citations) - 1)]}")
        if brief.risks:
            points.append(f"Risk note: {brief.risks[0]}")
        return points[:4]