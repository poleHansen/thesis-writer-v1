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


def test_list_project_exports_returns_recent_runs_in_desc_order(tmp_path: Path) -> None:
    database_path = tmp_path / "export-history-test.db"

    os.environ["DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"
    os.environ["AUTO_CREATE_TABLES"] = "true"

    from app.main import create_app

    app = create_app()

    project_payload = {
        "name": "Export History Demo",
        "description": "Verify recent export runs are listed.",
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
        "extracted_summary": "A compact source summary for export history tests.",
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

        run_ids = []
        for export_format in ["pptx", "pdf", "pptx"]:
          export_response = client.post(
              f"/projects/{project_id}/export",
              json={"artifact_id": artifact_id, "export_format": export_format},
          )
          assert export_response.status_code == 200
          run_ids.append(export_response.json()["export_job"]["run_id"])

        history_response = client.get(f"/projects/{project_id}/exports?limit=2")
        assert history_response.status_code == 200
        history_payload = history_response.json()

    assert len(history_payload["exports"]) == 2
    assert history_payload["exports"][0]["run_id"] == run_ids[2]
    assert history_payload["exports"][1]["run_id"] == run_ids[1]


def test_get_project_export_returns_selected_run_and_rejects_foreign_project(tmp_path: Path) -> None:
    database_path = tmp_path / "export-detail-test.db"

    os.environ["DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"
    os.environ["AUTO_CREATE_TABLES"] = "true"

    from app.main import create_app

    app = create_app()

    def build_project(client: TestClient, name: str) -> tuple[str, str]:
        project_response = client.post(
            "/projects",
            json={
                "name": name,
                "description": "Export detail lookup test.",
                "source_mode": "file",
                "tags": ["test"],
            },
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["project"]["id"]

        file_response = client.post(
            f"/projects/{project_id}/files",
            json={
                "file_name": "demo.md",
                "file_type": "markdown",
                "storage_path": "storage/uploads/demo.md",
                "mime_type": "text/markdown",
                "size_bytes": 128,
                "checksum": f"checksum-{name}",
                "extracted_summary": "A compact source summary for export detail tests.",
                "metadata": {},
            },
        )
        assert file_response.status_code == 201

        brief_id = client.post(f"/projects/{project_id}/brief:generate", json={"force_regenerate": True}).json()["brief"]["id"]
        outline_id = client.post(f"/projects/{project_id}/outline:generate", json={"brief_id": brief_id}).json()["outline"]["id"]
        slide_plan_id = client.post(f"/projects/{project_id}/slide-plan:generate", json={"outline_id": outline_id}).json()["slide_plan"]["id"]
        artifact_id = client.post(f"/projects/{project_id}/artifact:generate", json={"slide_plan_id": slide_plan_id}).json()["artifact"]["id"]

        export_response = client.post(
            f"/projects/{project_id}/export",
            json={"artifact_id": artifact_id, "export_format": "pptx"},
        )
        assert export_response.status_code == 200
        export_id = export_response.json()["export_job"]["id"]
        return project_id, export_id

    with TestClient(app) as client:
        first_project_id, first_export_id = build_project(client, "Export Detail One")
        second_project_id, _ = build_project(client, "Export Detail Two")

        detail_response = client.get(f"/projects/{first_project_id}/exports/{first_export_id}")
        assert detail_response.status_code == 200
        detail_payload = detail_response.json()

        foreign_response = client.get(f"/projects/{second_project_id}/exports/{first_export_id}")
        assert foreign_response.status_code == 404

    assert detail_payload["export_job"]["id"] == first_export_id
    assert detail_payload["export_job"]["project_id"] == first_project_id


def test_list_projects_dashboard_returns_aggregated_project_summary(tmp_path: Path) -> None:
    database_path = tmp_path / "dashboard-test.db"

    os.environ["DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"
    os.environ["AUTO_CREATE_TABLES"] = "true"

    from app.main import create_app

    app = create_app()

    project_payload = {
        "name": "Dashboard Demo",
        "description": "Verify dashboard aggregation returns project summary.",
        "source_mode": "file",
        "tags": ["phase6", "dashboard"],
    }

    file_payload = {
        "file_name": "demo.md",
        "file_type": "markdown",
        "storage_path": "storage/uploads/demo.md",
        "mime_type": "text/markdown",
        "size_bytes": 128,
        "checksum": "demo-checksum",
        "extracted_summary": "A compact source summary for dashboard tests.",
        "metadata": {},
    }

    with TestClient(app) as client:
        create_response = client.post("/projects", json=project_payload)
        assert create_response.status_code == 201
        project = create_response.json()["project"]
        project_id = project["id"]

        register_response = client.post(f"/projects/{project_id}/files", json=file_payload)
        assert register_response.status_code == 201

        brief_response = client.post(f"/projects/{project_id}/brief:generate", json={"force_regenerate": True})
        assert brief_response.status_code == 200
        brief = brief_response.json()["brief"]

        outline_response = client.post(f"/projects/{project_id}/outline:generate", json={"brief_id": brief["id"]})
        assert outline_response.status_code == 200
        outline = outline_response.json()["outline"]

        slide_plan_response = client.post(f"/projects/{project_id}/slide-plan:generate", json={"outline_id": outline["id"]})
        assert slide_plan_response.status_code == 200
        slide_plan = slide_plan_response.json()["slide_plan"]

        artifact_response = client.post(f"/projects/{project_id}/artifact:generate", json={"slide_plan_id": slide_plan["id"]})
        assert artifact_response.status_code == 200
        artifact = artifact_response.json()["artifact"]

        export_response = client.post(
            f"/projects/{project_id}/export",
            json={"artifact_id": artifact["id"], "export_format": "pdf"},
        )
        assert export_response.status_code == 200
        export_job = export_response.json()["export_job"]

        dashboard_response = client.get("/projects")
        assert dashboard_response.status_code == 200
        dashboard_payload = dashboard_response.json()

    assert len(dashboard_payload["projects"]) == 1
    dashboard_item = dashboard_payload["projects"][0]
    assert dashboard_item["project"]["id"] == project_id
    assert dashboard_item["project"]["name"] == project_payload["name"]
    assert dashboard_item["project"]["status"] == "exported"
    assert dashboard_item["file_count"] == 1
    assert dashboard_item["parsed_file_count"] == 0
    assert dashboard_item["failed_file_count"] == 0
    assert dashboard_item["latest_brief"]["id"] == brief["id"]
    assert dashboard_item["latest_outline"]["id"] == outline["id"]
    assert dashboard_item["latest_slide_plan"]["id"] == slide_plan["id"]
    assert dashboard_item["latest_artifact"]["id"] == artifact["id"]
    assert dashboard_item["latest_export"]["id"] == export_job["id"]
    assert dashboard_item["latest_export"]["preview_pdf_path"] == export_job["preview_pdf_path"]
    assert dashboard_item["current_task"]["task_type"] == "export"
    assert dashboard_item["current_task"]["task_status"] == "succeeded"


def test_project_detail_status_and_export_history_remain_consistent_across_pipeline(tmp_path: Path) -> None:
    database_path = tmp_path / "project-detail-status-test.db"

    os.environ["DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"
    os.environ["AUTO_CREATE_TABLES"] = "true"

    from app.main import create_app

    app = create_app()

    project_payload = {
        "name": "Project Detail Status Demo",
        "description": "Verify project detail, status, and export history stay aligned.",
        "source_mode": "file",
        "tags": ["phase7", "api-integration"],
    }

    file_payload = {
        "file_name": "demo.md",
        "file_type": "markdown",
        "storage_path": "storage/uploads/demo.md",
        "mime_type": "text/markdown",
        "size_bytes": 128,
        "checksum": "detail-status-checksum",
        "extracted_summary": "A compact source summary for project detail and status tests.",
        "metadata": {},
    }

    with TestClient(app) as client:
        create_response = client.post("/projects", json=project_payload)
        assert create_response.status_code == 201
        project_id = create_response.json()["project"]["id"]

        initial_detail_response = client.get(f"/projects/{project_id}")
        assert initial_detail_response.status_code == 200
        initial_detail = initial_detail_response.json()

        initial_status_response = client.get(f"/projects/{project_id}/status")
        assert initial_status_response.status_code == 200
        initial_status = initial_status_response.json()

        empty_history_response = client.get(f"/projects/{project_id}/exports")
        assert empty_history_response.status_code == 200
        empty_history = empty_history_response.json()

        register_response = client.post(f"/projects/{project_id}/files", json=file_payload)
        assert register_response.status_code == 201

        brief_response = client.post(f"/projects/{project_id}/brief:generate", json={"force_regenerate": True})
        assert brief_response.status_code == 200
        brief = brief_response.json()["brief"]

        outline_response = client.post(f"/projects/{project_id}/outline:generate", json={"brief_id": brief["id"]})
        assert outline_response.status_code == 200
        outline = outline_response.json()["outline"]

        slide_plan_response = client.post(f"/projects/{project_id}/slide-plan:generate", json={"outline_id": outline["id"]})
        assert slide_plan_response.status_code == 200
        slide_plan = slide_plan_response.json()["slide_plan"]

        artifact_response = client.post(f"/projects/{project_id}/artifact:generate", json={"slide_plan_id": slide_plan["id"]})
        assert artifact_response.status_code == 200
        artifact = artifact_response.json()["artifact"]

        detail_after_render_response = client.get(f"/projects/{project_id}")
        assert detail_after_render_response.status_code == 200
        detail_after_render = detail_after_render_response.json()

        status_after_render_response = client.get(f"/projects/{project_id}/status")
        assert status_after_render_response.status_code == 200
        status_after_render = status_after_render_response.json()

        export_response = client.post(
            f"/projects/{project_id}/export",
            json={"artifact_id": artifact["id"], "export_format": "pptx"},
        )
        assert export_response.status_code == 200
        export_job = export_response.json()["export_job"]

        final_detail_response = client.get(f"/projects/{project_id}")
        assert final_detail_response.status_code == 200
        final_detail = final_detail_response.json()

        final_status_response = client.get(f"/projects/{project_id}/status")
        assert final_status_response.status_code == 200
        final_status = final_status_response.json()

        export_history_response = client.get(f"/projects/{project_id}/exports")
        assert export_history_response.status_code == 200
        export_history = export_history_response.json()

        export_detail_response = client.get(f"/projects/{project_id}/exports/{export_job['id']}")
        assert export_detail_response.status_code == 200
        export_detail = export_detail_response.json()

    assert initial_detail["project"]["id"] == project_id
    assert initial_detail["project"]["status"] == "created"
    assert initial_detail["latest_brief"] is None
    assert initial_detail["latest_outline"] is None
    assert initial_detail["latest_slide_plan"] is None
    assert initial_detail["latest_artifact"] is None
    assert initial_detail["latest_export"] is None

    assert initial_status["project_id"] == project_id
    assert initial_status["project_status"] == "created"
    assert initial_status["current_task"]["task_type"] == "ingest"
    assert initial_status["current_task"]["task_status"] == "succeeded"
    assert initial_status["recent_tasks"][-1]["task_type"] == "ingest"
    assert empty_history["exports"] == []

    assert detail_after_render["project"]["status"] == "finalized"
    assert detail_after_render["latest_brief"]["id"] == brief["id"]
    assert detail_after_render["latest_outline"]["id"] == outline["id"]
    assert detail_after_render["latest_slide_plan"]["id"] == slide_plan["id"]
    assert detail_after_render["latest_artifact"]["id"] == artifact["id"]
    assert detail_after_render["latest_export"] is None

    assert status_after_render["project_status"] == "finalized"
    assert status_after_render["current_task"]["task_type"] == "render"
    assert status_after_render["current_task"]["task_status"] == "succeeded"
    assert status_after_render["recent_tasks"][-1]["task_type"] == "render"

    assert final_detail["project"]["status"] == "exported"
    assert final_detail["latest_brief"]["id"] == brief["id"]
    assert final_detail["latest_outline"]["id"] == outline["id"]
    assert final_detail["latest_slide_plan"]["id"] == slide_plan["id"]
    assert final_detail["latest_artifact"]["id"] == artifact["id"]
    assert final_detail["latest_export"]["id"] == export_job["id"]
    assert final_detail["latest_export"]["run_id"] == export_job["run_id"]

    assert final_status["project_status"] == "exported"
    assert final_status["current_task"]["task_type"] == "export"
    assert final_status["current_task"]["task_status"] == "succeeded"
    assert final_status["recent_tasks"][-1]["task_type"] == "export"
    assert len(final_status["recent_tasks"]) >= 5

    assert len(export_history["exports"]) == 1
    assert export_history["exports"][0]["id"] == export_job["id"]
    assert export_history["exports"][0]["run_id"] == export_job["run_id"]
    assert export_detail["export_job"]["id"] == export_job["id"]
    assert export_detail["export_job"]["project_id"] == project_id


def test_template_override_can_regenerate_slide_plan_and_artifact(tmp_path: Path) -> None:
    database_path = tmp_path / "template-override-test.db"

    os.environ["DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"
    os.environ["AUTO_CREATE_TABLES"] = "true"

    from app.main import create_app

    app = create_app()

    project_payload = {
        "name": "Template Override Demo",
        "description": "Verify preferred template and artifact template overrides are respected.",
        "source_mode": "file",
        "tags": ["phase6", "template"],
    }

    file_payload = {
        "file_name": "demo.md",
        "file_type": "markdown",
        "storage_path": "storage/uploads/demo.md",
        "mime_type": "text/markdown",
        "size_bytes": 128,
        "checksum": "demo-checksum",
        "extracted_summary": "A compact source summary for template override tests.",
        "metadata": {},
    }

    with TestClient(app) as client:
        templates_response = client.get("/projects/templates")
        assert templates_response.status_code == 200
        templates = templates_response.json()["templates"]
        assert len(templates) >= 2
        preferred_template_id = templates[0]["template_id"]
        rerender_template_id = templates[1]["template_id"]

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

        slide_plan_response = client.post(
            f"/projects/{project_id}/slide-plan:generate",
            json={
                "outline_id": outline_id,
                "preferred_template_id": preferred_template_id,
                "force_regenerate": True,
            },
        )
        assert slide_plan_response.status_code == 200
        slide_plan = slide_plan_response.json()["slide_plan"]

        artifact_response = client.post(
            f"/projects/{project_id}/artifact:generate",
            json={
                "slide_plan_id": slide_plan["id"],
                "template_id": rerender_template_id,
            },
        )
        assert artifact_response.status_code == 200
        artifact = artifact_response.json()["artifact"]

        detail_response = client.get(f"/projects/{project_id}")
        assert detail_response.status_code == 200
        detail_payload = detail_response.json()

    latest_slide_plan = detail_payload["latest_slide_plan"]
    latest_artifact = detail_payload["latest_artifact"]

    assert latest_slide_plan["id"] == slide_plan["id"]
    assert latest_slide_plan["metadata"]["preferred_template_id"] == preferred_template_id
    assert artifact["id"] == latest_artifact["id"]
    assert latest_artifact["metadata"]["template_id"] == rerender_template_id
    assert latest_artifact["metadata"]["template_name"]
    assert latest_artifact["render_status"] in {"succeeded", "partial"}