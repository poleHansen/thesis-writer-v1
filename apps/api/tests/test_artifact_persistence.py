from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi.testclient import TestClient
from pptx import Presentation
from pypdf import PdfReader


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


def test_export_writes_project_export_artifact(tmp_path: Path) -> None:
    database_path = tmp_path / "export-test.db"
    storage_root = Path("storage")

    os.environ["DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"
    os.environ["AUTO_CREATE_TABLES"] = "true"

    from app.main import create_app

    app = create_app()

    project_payload = {
        "name": "Export Demo",
        "description": "Verify export jobs persist and write output.",
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
        "extracted_summary": "A compact source summary for export tests.",
        "metadata": {},
    }

    with TestClient(app) as client:
        create_response = client.post("/projects", json=project_payload)
        assert create_response.status_code == 201
        project_id = create_response.json()["project"]["id"]

        register_response = client.post(f"/projects/{project_id}/files", json=file_payload)
        assert register_response.status_code == 201

        brief_response = client.post(f"/projects/{project_id}/brief:generate", json={"force_regenerate": True})
        assert brief_response.status_code == 200
        brief_id = brief_response.json()["brief"]["id"]

        outline_response = client.post(f"/projects/{project_id}/outline:generate", json={"brief_id": brief_id})
        assert outline_response.status_code == 200
        outline_id = outline_response.json()["outline"]["id"]

        slide_plan_response = client.post(f"/projects/{project_id}/slide-plan:generate", json={"outline_id": outline_id})
        assert slide_plan_response.status_code == 200
        slide_plan_id = slide_plan_response.json()["slide_plan"]["id"]

        render_response = client.post(f"/projects/{project_id}/artifact:generate", json={"slide_plan_id": slide_plan_id})
        assert render_response.status_code == 200
        artifact_id = render_response.json()["artifact"]["id"]

        export_response = client.post(
            f"/projects/{project_id}/export",
            json={"artifact_id": artifact_id, "export_format": "pptx"},
        )
        assert export_response.status_code == 200
        export_payload = export_response.json()

        detail_response = client.get(f"/projects/{project_id}")
        assert detail_response.status_code == 200
        detail_payload = detail_response.json()

    export_job = export_payload["export_job"]
    export_path = Path(export_job["export_path"])
    archive_manifest_path = Path(export_job["metadata"]["archive_manifest_path"])
    export_log_path = Path(export_job["metadata"]["export_log_path"])
    assert export_path.exists()
    assert export_path.suffix == ".pptx"
    assert archive_manifest_path.exists()
    assert export_log_path.exists()
    presentation = Presentation(export_path)
    archive_manifest = json.loads(archive_manifest_path.read_text(encoding="utf-8"))
    export_log = json.loads(export_log_path.read_text(encoding="utf-8"))
    assert export_job["status"] == "succeeded"
    assert export_job["run_id"].startswith("run-")
    assert export_job["metadata"]["export_kind"] == "pptx_from_svg_pages"
    assert export_job["metadata"]["file_count"] >= 1
    assert export_job["metadata"]["renderer"] == "cairosvg+python-pptx"
    assert export_job["metadata"]["run_id"] == export_job["run_id"]
    assert export_job["run_id"] in export_job["export_path"]
    assert len(export_job["metadata"]["rendered_files"]) == len(presentation.slides)
    assert len(presentation.slides) == export_job["metadata"]["file_count"]
    assert archive_manifest["project_id"] == project_id
    assert archive_manifest["run_id"] == export_job["run_id"]
    assert archive_manifest["export_path"] == export_job["export_path"]
    assert archive_manifest["artifacts"]["export_output"] == export_job["export_path"]
    assert archive_manifest["artifacts"]["slide_artifact"].endswith("slide-artifact.json")
    assert export_log["run_id"] == export_job["run_id"]
    assert export_log["archive_manifest_path"] == export_job["metadata"]["archive_manifest_path"]
    assert export_log["status"] == "succeeded"
    assert export_payload["task_run"]["task_type"] == "export"
    assert export_payload["task_run"]["task_status"] == "succeeded"
    assert export_payload["task_run"]["result"]["run_id"] == export_job["run_id"]
    assert export_payload["task_run"]["result"]["archive_manifest_path"] == export_job["metadata"]["archive_manifest_path"]
    assert detail_payload["project"]["status"] == "exported"
    assert detail_payload["latest_export"]["id"] == export_job["id"]
    assert detail_payload["latest_export"]["run_id"] == export_job["run_id"]
    assert detail_payload["latest_export"]["export_path"] == export_job["export_path"]


def test_export_failure_is_persisted_for_traceability(tmp_path: Path) -> None:
    database_path = tmp_path / "export-failure-test.db"

    os.environ["DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"
    os.environ["AUTO_CREATE_TABLES"] = "true"

    from app.main import create_app

    app = create_app()

    project_payload = {
        "name": "Export Failure Demo",
        "description": "Verify failed export attempts are persisted.",
        "source_mode": "file",
        "tags": ["test"],
    }

    with TestClient(app) as client:
        create_response = client.post("/projects", json=project_payload)
        assert create_response.status_code == 201
        project_id = create_response.json()["project"]["id"]

        export_response = client.post(
            f"/projects/{project_id}/export",
            json={"artifact_id": "missing-artifact", "export_format": "pptx"},
        )
        assert export_response.status_code == 400
        assert export_response.json()["detail"] == "Project has no rendered artifact to export"

        detail_response = client.get(f"/projects/{project_id}")
        assert detail_response.status_code == 200
        detail_payload = detail_response.json()

        status_response = client.get(f"/projects/{project_id}/status")
        assert status_response.status_code == 200
        status_payload = status_response.json()

    assert detail_payload["project"]["status"] == "export_failed"
    assert detail_payload["latest_export"] is None
    assert status_payload["current_task"]["task_type"] == "export"
    assert status_payload["current_task"]["task_status"] == "failed"
    assert status_payload["current_task"]["error_message"] == "Project has no rendered artifact to export"


def test_pdf_preview_export_writes_preview_path(tmp_path: Path) -> None:
    database_path = tmp_path / "export-pdf-test.db"
    storage_root = Path("storage")

    os.environ["DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"
    os.environ["AUTO_CREATE_TABLES"] = "true"

    from app.main import create_app

    app = create_app()

    project_payload = {
        "name": "Export PDF Demo",
        "description": "Verify PDF preview exports persist and write output.",
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
        "extracted_summary": "A compact source summary for PDF export tests.",
        "metadata": {},
    }

    with TestClient(app) as client:
        create_response = client.post("/projects", json=project_payload)
        assert create_response.status_code == 201
        project_id = create_response.json()["project"]["id"]

        register_response = client.post(f"/projects/{project_id}/files", json=file_payload)
        assert register_response.status_code == 201

        brief_response = client.post(f"/projects/{project_id}/brief:generate", json={"force_regenerate": True})
        assert brief_response.status_code == 200
        brief_id = brief_response.json()["brief"]["id"]

        outline_response = client.post(f"/projects/{project_id}/outline:generate", json={"brief_id": brief_id})
        assert outline_response.status_code == 200
        outline_id = outline_response.json()["outline"]["id"]

        slide_plan_response = client.post(f"/projects/{project_id}/slide-plan:generate", json={"outline_id": outline_id})
        assert slide_plan_response.status_code == 200
        slide_plan_id = slide_plan_response.json()["slide_plan"]["id"]

        render_response = client.post(f"/projects/{project_id}/artifact:generate", json={"slide_plan_id": slide_plan_id})
        assert render_response.status_code == 200
        artifact_id = render_response.json()["artifact"]["id"]

        export_response = client.post(
            f"/projects/{project_id}/export",
            json={"artifact_id": artifact_id, "export_format": "pdf"},
        )
        assert export_response.status_code == 200
        export_payload = export_response.json()

        detail_response = client.get(f"/projects/{project_id}")
        assert detail_response.status_code == 200
        detail_payload = detail_response.json()

    export_job = export_payload["export_job"]
    preview_pdf_path = Path(export_job["preview_pdf_path"])
    archive_manifest_path = Path(export_job["metadata"]["archive_manifest_path"])
    assert storage_root.exists()
    assert preview_pdf_path.exists()
    assert archive_manifest_path.exists()
    assert preview_pdf_path.suffix == ".pdf"
    reader = PdfReader(str(preview_pdf_path))
    archive_manifest = json.loads(archive_manifest_path.read_text(encoding="utf-8"))
    assert len(reader.pages) == export_job["metadata"]["file_count"]
    assert export_job["status"] == "succeeded"
    assert export_job["run_id"].startswith("run-")
    assert export_job["metadata"]["export_kind"] == "pdf_preview_from_svg_pages"
    assert export_job["metadata"]["renderer"] == "cairosvg+pypdf"
    assert export_job["export_path"] == export_job["preview_pdf_path"]
    assert archive_manifest["run_id"] == export_job["run_id"]
    assert archive_manifest["preview_pdf_path"] == export_job["preview_pdf_path"]
    assert archive_manifest["export_format"] == "pdf"
    assert detail_payload["project"]["status"] == "exported"
    assert detail_payload["latest_export"]["id"] == export_job["id"]
    assert detail_payload["latest_export"]["preview_pdf_path"] == export_job["preview_pdf_path"]


def test_repeated_exports_create_distinct_run_ids_and_paths(tmp_path: Path) -> None:
    database_path = tmp_path / "export-run-id-test.db"

    os.environ["DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"
    os.environ["AUTO_CREATE_TABLES"] = "true"

    from app.main import create_app

    app = create_app()

    project_payload = {
        "name": "Export Run ID Demo",
        "description": "Verify repeated exports produce distinct run ids and output paths.",
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
        "extracted_summary": "A compact source summary for run id tests.",
        "metadata": {},
    }

    with TestClient(app) as client:
        create_response = client.post("/projects", json=project_payload)
        assert create_response.status_code == 201
        project_id = create_response.json()["project"]["id"]

        register_response = client.post(f"/projects/{project_id}/files", json=file_payload)
        assert register_response.status_code == 201

        brief_response = client.post(f"/projects/{project_id}/brief:generate", json={"force_regenerate": True})
        assert brief_response.status_code == 200
        brief_id = brief_response.json()["brief"]["id"]

        outline_response = client.post(f"/projects/{project_id}/outline:generate", json={"brief_id": brief_id})
        assert outline_response.status_code == 200
        outline_id = outline_response.json()["outline"]["id"]

        slide_plan_response = client.post(f"/projects/{project_id}/slide-plan:generate", json={"outline_id": outline_id})
        assert slide_plan_response.status_code == 200
        slide_plan_id = slide_plan_response.json()["slide_plan"]["id"]

        render_response = client.post(f"/projects/{project_id}/artifact:generate", json={"slide_plan_id": slide_plan_id})
        assert render_response.status_code == 200
        artifact_id = render_response.json()["artifact"]["id"]

        first_export_response = client.post(
            f"/projects/{project_id}/export",
            json={"artifact_id": artifact_id, "export_format": "pptx"},
        )
        assert first_export_response.status_code == 200
        first_export_job = first_export_response.json()["export_job"]

        second_export_response = client.post(
            f"/projects/{project_id}/export",
            json={"artifact_id": artifact_id, "export_format": "pptx"},
        )
        assert second_export_response.status_code == 200
        second_export_job = second_export_response.json()["export_job"]

        detail_response = client.get(f"/projects/{project_id}")
        assert detail_response.status_code == 200
        detail_payload = detail_response.json()

    assert first_export_job["run_id"] != second_export_job["run_id"]
    assert first_export_job["export_path"] != second_export_job["export_path"]
    assert Path(first_export_job["export_path"]).exists()
    assert Path(second_export_job["export_path"]).exists()
    assert first_export_job["run_id"] in first_export_job["export_path"]
    assert second_export_job["run_id"] in second_export_job["export_path"]
    assert detail_payload["latest_export"]["id"] == second_export_job["id"]
    assert detail_payload["latest_export"]["run_id"] == second_export_job["run_id"]