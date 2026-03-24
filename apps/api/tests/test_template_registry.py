from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient

from core_types import ContentBlock, LayoutMode, SlidePlan, SlidePlanItem
from app.services.template_registry import TemplateRegistryService


def test_list_templates_returns_externalized_builtin_assets(tmp_path: Path) -> None:
    database_path = tmp_path / "template-test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"
    os.environ["AUTO_CREATE_TABLES"] = "true"

    from app.main import create_app

    app = create_app()

    with TestClient(app) as client:
        response = client.get("/projects/templates")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["templates"]) >= 6
    template_ids = {item["template_id"] for item in payload["templates"]}
    assert {
        "consulting-clean",
        "consulting-premium",
        "academic-defense",
        "research-paper",
        "technology-grid",
        "government-blue",
    }.issubset(template_ids)
    consulting = next(item for item in payload["templates"] if item["template_id"] == "consulting-clean")
    premium = next(item for item in payload["templates"] if item["template_id"] == "consulting-premium")
    research = next(item for item in payload["templates"] if item["template_id"] == "research-paper")
    technology = next(item for item in payload["templates"] if item["template_id"] == "technology-grid")
    government = next(item for item in payload["templates"] if item["template_id"] == "government-blue")
    assert consulting["design_spec_path"] == "builtin://templates/consulting-clean/design-spec.json"
    assert "cover" in consulting["supported_layout_modes"]
    assert premium["metadata"]["visual_direction"] == "executive_light_panels"
    assert premium["density_range"] == "medium-high"
    assert research["metadata"]["font_family"] == "Noto Serif SC"
    assert research["design_spec_path"] == "builtin://templates/research-paper/design-spec.json"
    assert technology["metadata"]["visual_direction"] == "dark_grid_hud"
    assert "bento" in technology["supported_layout_modes"]
    assert government["density_range"] == "medium-high"
    assert government["design_spec_path"] == "builtin://templates/government-blue/design-spec.json"


def test_resolve_template_prefers_scenario_hints_when_layouts_overlap() -> None:
    registry = TemplateRegistryService()
    slide_plan = SlidePlan(
        project_id="project-1",
        brief_id="brief-1",
        outline_id="outline-1",
        page_count=2,
        design_direction="technology architecture",
        slides=[
            SlidePlanItem(
                slide_id="slide-1",
                slide_number=1,
                title="系统架构",
                conclusion="技术架构需要清晰呈现",
                layout_mode=LayoutMode.HERO,
                content_blocks=[ContentBlock(block_id="block-1", block_type="text", body="架构总览")],
            ),
            SlidePlanItem(
                slide_id="slide-2",
                slide_number=2,
                title="能力分层",
                conclusion="分层能力便于模块化演进",
                layout_mode=LayoutMode.TWO_COLUMN,
                content_blocks=[ContentBlock(block_id="block-2", block_type="bullets", bullets=["应用层", "能力层"])],
            ),
        ],
        metadata={"scenario_tags": ["ai", "product"]},
    )

    resolved = registry.resolve_template(None, slide_plan)

    assert resolved.template_id == "technology-grid"


def test_resolve_template_prefers_academic_research_hints() -> None:
    registry = TemplateRegistryService()
    slide_plan = SlidePlan(
        project_id="project-3",
        brief_id="brief-3",
        outline_id="outline-3",
        page_count=2,
        design_direction="academic research methodology",
        slides=[
            SlidePlanItem(
                slide_id="slide-1",
                slide_number=1,
                title="研究方法",
                conclusion="方法设计需要清楚解释",
                layout_mode=LayoutMode.CHART_FOCUS,
                content_blocks=[ContentBlock(block_id="block-1", block_type="text", body="实验设计与变量控制")],
            ),
            SlidePlanItem(
                slide_id="slide-2",
                slide_number=2,
                title="研究结论",
                conclusion="结论需要和方法形成闭环",
                layout_mode=LayoutMode.TWO_COLUMN,
                content_blocks=[ContentBlock(block_id="block-2", block_type="bullets", bullets=["方法有效", "可进一步扩展"])],
            ),
        ],
        metadata={"scenario_tags": ["thesis", "research"], "style_tags": ["academic"]},
    )

    resolved = registry.resolve_template(None, slide_plan)

    assert resolved.template_id in {"research-paper", "academic-defense"}


def test_resolve_template_prefers_consulting_strategy_hints() -> None:
    registry = TemplateRegistryService()
    slide_plan = SlidePlan(
        project_id="project-4",
        brief_id="brief-4",
        outline_id="outline-4",
        page_count=2,
        design_direction="strategy business analysis",
        slides=[
            SlidePlanItem(
                slide_id="slide-1",
                slide_number=1,
                title="战略判断",
                conclusion="需要突出执行层的关键判断",
                layout_mode=LayoutMode.HERO,
                content_blocks=[ContentBlock(block_id="block-1", block_type="text", body="增长与效率双目标")],
            ),
            SlidePlanItem(
                slide_id="slide-2",
                slide_number=2,
                title="行动方案",
                conclusion="拆成可执行路径",
                layout_mode=LayoutMode.BENTO,
                content_blocks=[ContentBlock(block_id="block-2", block_type="bullets", bullets=["聚焦市场", "优化产品", "改善交付"])],
            ),
        ],
        metadata={"scenario_tags": ["strategy", "management"]},
    )

    resolved = registry.resolve_template(None, slide_plan)

    assert resolved.template_id == "consulting-premium"


def test_resolve_template_falls_back_to_layout_coverage_without_hints() -> None:
    registry = TemplateRegistryService()
    slide_plan = SlidePlan(
        project_id="project-2",
        brief_id="brief-2",
        outline_id="outline-2",
        page_count=1,
        slides=[
            SlidePlanItem(
                slide_id="slide-1",
                slide_number=1,
                title="目录",
                conclusion="展示内容结构",
                layout_mode=LayoutMode.TOC,
                content_blocks=[ContentBlock(block_id="block-1", block_type="text", body="章节列表")],
            )
        ],
    )

    resolved = registry.resolve_template(None, slide_plan)

    assert resolved.template_id in {
        "academic-defense",
        "consulting-clean",
        "government-blue",
        "technology-grid",
    }
    assert LayoutMode.TOC in resolved.supported_layout_modes