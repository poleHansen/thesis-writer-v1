from __future__ import annotations

from dataclasses import dataclass, field

from core_types import SourceBundle, UserIntent


@dataclass(slots=True)
class ClarificationAssessment:
    is_sufficient: bool
    missing_fields: list[str] = field(default_factory=list)
    suggested_questions: list[str] = field(default_factory=list)


class RequirementClarifier:
    QUESTION_TEMPLATES = {
        "audience": "这份 PPT 的目标受众是谁？",
        "scenario": "这份 PPT 会在什么场景下使用？",
        "purpose": "这次演示最核心的目标是什么？",
        "desired_page_count": "希望控制在多少页以内？",
        "style_preferences": "有没有明确的风格偏好？",
        "emphasize_points": "是否需要重点强调某些数据、图表、案例或观点？",
    }

    def build_question_set(self) -> list[str]:
        return list(self.QUESTION_TEMPLATES.values())

    def assess(self, source_bundle: SourceBundle | None, user_intent: UserIntent | None) -> ClarificationAssessment:
        intent = user_intent or (source_bundle.user_intent if source_bundle else None)
        missing_fields: list[str] = []

        if intent is None:
            missing_fields = list(self.QUESTION_TEMPLATES.keys())
        else:
            if not intent.audience:
                missing_fields.append("audience")
            if not intent.scenario:
                missing_fields.append("scenario")
            if not intent.purpose:
                missing_fields.append("purpose")
            if not intent.desired_page_count:
                missing_fields.append("desired_page_count")
            if not intent.style_preferences:
                missing_fields.append("style_preferences")
            if not intent.emphasize_points:
                missing_fields.append("emphasize_points")

        suggested_questions = [self.QUESTION_TEMPLATES[field_name] for field_name in missing_fields]
        return ClarificationAssessment(
            is_sufficient=len(missing_fields) <= 2,
            missing_fields=missing_fields,
            suggested_questions=suggested_questions,
        )