from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi.testclient import TestClient


def test_generation_writes_artifact_snapshots(tmp_path: Path) -> None:
    database_path = tmp_path / "artifact-test.db"
    storage_root = Path("storage")

    os.environ["DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"
    os.environ["AUTO_CREATE_TABLES"] = "true"

    from app.main import create_app

    app = create_app()

    project_payload = {
        "name": "Artifact Persistence Demo",
        "description": "Verify generated artifacts are written to disk.",
        "source_mode": "file",
        "tags": ["test"],
    }

    file_payload = {
        "file_name": "demo.md",
        "file_type": "markdown",
        "storage_path": "storage/uploads/demo.md",
        "mime_type": "text/markdown",
        "size_bytes": 128,
        "checksum": "demo-checksum",
        "extracted_summary": "A compact source summary for artifact tests.",
        "metadata": {},
    }

    with TestClient(app) as client:
        create_response = client.post("/projects", json=project_payload)
        assert create_response.status_code == 201
        project_id = create_response.json()["project"]["id"]

        register_response = client.post(f"/projects/{project_id}/files", json=file_payload)
        assert register_response.status_code == 201

        brief_response = client.post(
            f"/projects/{project_id}/brief:generate",
            json={"force_regenerate": True},
        )
        assert brief_response.status_code == 200
        brief_id = brief_response.json()["brief"]["id"]

        outline_response = client.post(
            f"/projects/{project_id}/outline:generate",
            json={"brief_id": brief_id},
        )
        assert outline_response.status_code == 200
        outline_id = outline_response.json()["outline"]["id"]

        slide_plan_response = client.post(
            f"/projects/{project_id}/slide-plan:generate",
            json={"outline_id": outline_id},
        )
        assert slide_plan_response.status_code == 200
        slide_plan_id = slide_plan_response.json()["slide_plan"]["id"]

        render_response = client.post(
            f"/projects/{project_id}/artifact:generate",
            json={"slide_plan_id": slide_plan_id},
        )
        assert render_response.status_code == 200
        artifact_id = render_response.json()["artifact"]["id"]

    artifact_dir = storage_root / "projects" / project_id / "artifacts"
    brief_path = artifact_dir / "brief.json"
    outline_path = artifact_dir / "outline.json"
    slide_plan_path = artifact_dir / "slide-plan.json"
    slide_artifact_path = artifact_dir / "slide-artifact.json"
    render_root = storage_root / "projects" / project_id / "render" / artifact_id
    design_spec_path = render_root / "design-spec.json"

    assert brief_path.exists()
    assert outline_path.exists()
    assert slide_plan_path.exists()
    assert slide_artifact_path.exists()
    assert (render_root / "svg_output").exists()
    assert (render_root / "svg_final").exists()
    assert design_spec_path.exists()
    assert (render_root / "render-log.json").exists()
    assert any((render_root / "svg_final").glob("slide-*.svg"))

    brief_payload = json.loads(brief_path.read_text(encoding="utf-8"))
    outline_payload = json.loads(outline_path.read_text(encoding="utf-8"))
    slide_plan_payload = json.loads(slide_plan_path.read_text(encoding="utf-8"))
    slide_artifact_payload = json.loads(slide_artifact_path.read_text(encoding="utf-8"))
    design_spec_payload = json.loads(design_spec_path.read_text(encoding="utf-8"))
    render_log_payload = json.loads((render_root / "render-log.json").read_text(encoding="utf-8"))
    first_svg = next((render_root / "svg_final").glob("slide-*.svg"))
    first_svg_content = first_svg.read_text(encoding="utf-8")

    assert brief_payload["project_id"] == project_id
    assert outline_payload["project_id"] == project_id
    assert slide_plan_payload["project_id"] == project_id
    assert slide_artifact_payload["project_id"] == project_id
    assert slide_artifact_payload["slide_plan_id"] == slide_plan_id
    assert slide_artifact_payload["metadata"]["design_spec_path"].endswith("design-spec.json")
    assert slide_artifact_payload["render_status"] in {"succeeded", "partial"}
    assert slide_artifact_payload["metadata"]["generated_svg_files"]
    assert slide_artifact_payload["metadata"]["validation_summary"]["checked_file_count"] >= 1
    assert slide_artifact_payload["metadata"]["validation_summary"]["invalid_file_count"] == 0
    assert slide_artifact_payload["metadata"]["finalization_summary"]["page_count"] >= 1
    assert slide_artifact_payload["metadata"]["finalization_summary"]["width_height_alignment_count"] >= 0
    assert design_spec_payload["project_id"] == project_id
    assert design_spec_payload["page_count"] >= 1
    assert design_spec_payload["template"]["template_id"]
    assert slide_plan_payload["page_count"] >= 1
    assert render_log_payload["validation_results"]
    assert all(item["is_valid"] for item in render_log_payload["validation_results"])
    assert render_log_payload["finalization_summary"]["page_count"] >= 1
    assert render_log_payload["finalization_summary"]["width_height_alignment_count"] >= 0
    assert all(item["finalizer_steps"] for item in render_log_payload["validation_results"])
    assert all(
        "ensure_canvas_dimensions" in item["finalizer_steps"] or 'width="1280"' in first_svg_content
        for item in render_log_payload["validation_results"]
    )
    assert first_svg_content.startswith("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
    assert 'width="1280"' in first_svg_content
    assert 'height="720"' in first_svg_content