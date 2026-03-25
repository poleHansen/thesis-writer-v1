"""Initial API schema.

Revision ID: 20260325_0001
Revises:
Create Date: 2026-03-25 00:00:00

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


revision = "20260325_0001"
down_revision = None
branch_labels = None
depends_on = None


def _is_sqlite() -> bool:
    return op.get_bind().dialect.name == "sqlite"


def _has_fk(inspector: Inspector, table_name: str, constrained_columns: list[str]) -> bool:
    target_columns = tuple(constrained_columns)
    for foreign_key in inspector.get_foreign_keys(table_name):
        if tuple(foreign_key.get("constrained_columns") or []) == target_columns:
            return True
    return False


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("source_mode", sa.String(length=32), nullable=False),
        sa.Column("owner_id", sa.String(length=64), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("current_template_id", sa.String(length=128), nullable=True),
        sa.Column("latest_source_bundle_id", sa.String(length=64), nullable=True),
        sa.Column("latest_brief_id", sa.String(length=64), nullable=True),
        sa.Column("latest_outline_id", sa.String(length=64), nullable=True),
        sa.Column("latest_slide_plan_id", sa.String(length=64), nullable=True),
        sa.Column("latest_artifact_id", sa.String(length=64), nullable=True),
        sa.Column("last_error_code", sa.String(length=64), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_projects_name"), "projects", ["name"], unique=False)
    op.create_index(op.f("ix_projects_owner_id"), "projects", ["owner_id"], unique=False)
    op.create_index(op.f("ix_projects_status"), "projects", ["status"], unique=False)

    op.create_table(
        "task_runs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("task_type", sa.String(length=64), nullable=False),
        sa.Column("task_status", sa.String(length=32), nullable=False),
        sa.Column("trigger_source", sa.String(length=32), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_task_runs_project_id"), "task_runs", ["project_id"], unique=False)
    op.create_index(op.f("ix_task_runs_task_status"), "task_runs", ["task_status"], unique=False)
    op.create_index(op.f("ix_task_runs_task_type"), "task_runs", ["task_type"], unique=False)

    op.create_table(
        "project_files",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_type", sa.String(length=32), nullable=False),
        sa.Column("storage_path", sa.String(length=512), nullable=False),
        sa.Column("mime_type", sa.String(length=128), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("upload_status", sa.String(length=32), nullable=False),
        sa.Column("parse_status", sa.String(length=32), nullable=False),
        sa.Column("parse_error", sa.Text(), nullable=True),
        sa.Column("extracted_summary", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_project_files_file_type"), "project_files", ["file_type"], unique=False)
    op.create_index(op.f("ix_project_files_parse_status"), "project_files", ["parse_status"], unique=False)
    op.create_index(op.f("ix_project_files_project_id"), "project_files", ["project_id"], unique=False)
    op.create_index(op.f("ix_project_files_upload_status"), "project_files", ["upload_status"], unique=False)

    op.create_table(
        "source_bundles",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("source_file_ids", sa.JSON(), nullable=False),
        sa.Column("source_mode", sa.String(length=32), nullable=False),
        sa.Column("user_intent", sa.JSON(), nullable=True),
        sa.Column("raw_markdown", sa.Text(), nullable=True),
        sa.Column("normalized_markdown", sa.Text(), nullable=True),
        sa.Column("page_chunks", sa.JSON(), nullable=False),
        sa.Column("tables", sa.JSON(), nullable=False),
        sa.Column("images", sa.JSON(), nullable=False),
        sa.Column("citations", sa.JSON(), nullable=False),
        sa.Column("language", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_source_bundles_project_id"), "source_bundles", ["project_id"], unique=False)
    op.create_index(op.f("ix_source_bundles_status"), "source_bundles", ["status"], unique=False)

    op.create_table(
        "presentation_briefs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("source_bundle_id", sa.String(length=64), nullable=False),
        sa.Column("presentation_goal", sa.Text(), nullable=False),
        sa.Column("target_audience", sa.String(length=255), nullable=False),
        sa.Column("core_message", sa.Text(), nullable=False),
        sa.Column("storyline", sa.Text(), nullable=False),
        sa.Column("recommended_page_count", sa.Integer(), nullable=False),
        sa.Column("tone", sa.String(length=64), nullable=False),
        sa.Column("style_preferences", sa.JSON(), nullable=False),
        sa.Column("risks", sa.JSON(), nullable=False),
        sa.Column("assumptions", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["source_bundle_id"], ["source_bundles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_presentation_briefs_project_id"), "presentation_briefs", ["project_id"], unique=False)
    op.create_index(op.f("ix_presentation_briefs_source_bundle_id"), "presentation_briefs", ["source_bundle_id"], unique=False)
    op.create_index(op.f("ix_presentation_briefs_status"), "presentation_briefs", ["status"], unique=False)

    op.create_table(
        "outlines",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("brief_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("chapters", sa.JSON(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["brief_id"], ["presentation_briefs.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_outlines_brief_id"), "outlines", ["brief_id"], unique=False)
    op.create_index(op.f("ix_outlines_project_id"), "outlines", ["project_id"], unique=False)
    op.create_index(op.f("ix_outlines_status"), "outlines", ["status"], unique=False)

    op.create_table(
        "slide_plans",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("brief_id", sa.String(length=64), nullable=False),
        sa.Column("outline_id", sa.String(length=64), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column("slides", sa.JSON(), nullable=False),
        sa.Column("design_direction", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["brief_id"], ["presentation_briefs.id"]),
        sa.ForeignKeyConstraint(["outline_id"], ["outlines.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_slide_plans_brief_id"), "slide_plans", ["brief_id"], unique=False)
    op.create_index(op.f("ix_slide_plans_outline_id"), "slide_plans", ["outline_id"], unique=False)
    op.create_index(op.f("ix_slide_plans_project_id"), "slide_plans", ["project_id"], unique=False)
    op.create_index(op.f("ix_slide_plans_status"), "slide_plans", ["status"], unique=False)

    op.create_table(
        "templates",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("template_id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("style_tags", sa.JSON(), nullable=False),
        sa.Column("scenario_tags", sa.JSON(), nullable=False),
        sa.Column("supported_layout_modes", sa.JSON(), nullable=False),
        sa.Column("density_range", sa.String(length=32), nullable=False),
        sa.Column("color_scheme", sa.JSON(), nullable=False),
        sa.Column("design_spec_path", sa.String(length=512), nullable=False),
        sa.Column("preview_image_path", sa.String(length=512), nullable=True),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("template_id", name="uq_templates_template_id"),
    )
    op.create_index(op.f("ix_templates_is_active"), "templates", ["is_active"], unique=False)
    op.create_index(op.f("ix_templates_template_id"), "templates", ["template_id"], unique=False)

    op.create_table(
        "slide_artifacts",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("slide_plan_id", sa.String(length=64), nullable=False),
        sa.Column("template_id", sa.String(length=64), nullable=True),
        sa.Column("svg_output_dir", sa.String(length=512), nullable=True),
        sa.Column("svg_final_dir", sa.String(length=512), nullable=True),
        sa.Column("preview_image_paths", sa.JSON(), nullable=False),
        sa.Column("render_status", sa.String(length=32), nullable=False),
        sa.Column("failed_slide_ids", sa.JSON(), nullable=False),
        sa.Column("log_path", sa.String(length=512), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["slide_plan_id"], ["slide_plans.id"]),
        sa.ForeignKeyConstraint(["template_id"], ["templates.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_slide_artifacts_project_id"), "slide_artifacts", ["project_id"], unique=False)
    op.create_index(op.f("ix_slide_artifacts_render_status"), "slide_artifacts", ["render_status"], unique=False)
    op.create_index(op.f("ix_slide_artifacts_slide_plan_id"), "slide_artifacts", ["slide_plan_id"], unique=False)
    op.create_index(op.f("ix_slide_artifacts_template_id"), "slide_artifacts", ["template_id"], unique=False)

    op.create_table(
        "exports",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("artifact_id", sa.String(length=64), nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("export_format", sa.String(length=32), nullable=False),
        sa.Column("export_path", sa.String(length=512), nullable=True),
        sa.Column("preview_pdf_path", sa.String(length=512), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["artifact_id"], ["slide_artifacts.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_exports_artifact_id"), "exports", ["artifact_id"], unique=False)
    op.create_index(op.f("ix_exports_export_format"), "exports", ["export_format"], unique=False)
    op.create_index(op.f("ix_exports_project_id"), "exports", ["project_id"], unique=False)
    op.create_index(op.f("ix_exports_run_id"), "exports", ["run_id"], unique=False)
    op.create_index(op.f("ix_exports_status"), "exports", ["status"], unique=False)

    if not _is_sqlite():
        op.create_foreign_key(
            "fk_projects_latest_source_bundle_id_source_bundles",
            "projects",
            "source_bundles",
            ["latest_source_bundle_id"],
            ["id"],
        )
        op.create_foreign_key(
            "fk_projects_latest_brief_id_presentation_briefs",
            "projects",
            "presentation_briefs",
            ["latest_brief_id"],
            ["id"],
        )
        op.create_foreign_key(
            "fk_projects_latest_outline_id_outlines",
            "projects",
            "outlines",
            ["latest_outline_id"],
            ["id"],
        )
        op.create_foreign_key(
            "fk_projects_latest_slide_plan_id_slide_plans",
            "projects",
            "slide_plans",
            ["latest_slide_plan_id"],
            ["id"],
        )
        op.create_foreign_key(
            "fk_projects_latest_artifact_id_slide_artifacts",
            "projects",
            "slide_artifacts",
            ["latest_artifact_id"],
            ["id"],
        )

def downgrade() -> None:
    if not _is_sqlite():
        inspector = sa.inspect(op.get_bind())
        fk_specs = [
            ("fk_projects_latest_artifact_id_slide_artifacts", ["latest_artifact_id"]),
            ("fk_projects_latest_slide_plan_id_slide_plans", ["latest_slide_plan_id"]),
            ("fk_projects_latest_outline_id_outlines", ["latest_outline_id"]),
            ("fk_projects_latest_brief_id_presentation_briefs", ["latest_brief_id"]),
            ("fk_projects_latest_source_bundle_id_source_bundles", ["latest_source_bundle_id"]),
        ]
        for constraint_name, constrained_columns in fk_specs:
            if _has_fk(inspector, "projects", constrained_columns):
                op.drop_constraint(constraint_name, "projects", type_="foreignkey")

    op.drop_index(op.f("ix_exports_status"), table_name="exports")
    op.drop_index(op.f("ix_exports_run_id"), table_name="exports")
    op.drop_index(op.f("ix_exports_project_id"), table_name="exports")
    op.drop_index(op.f("ix_exports_export_format"), table_name="exports")
    op.drop_index(op.f("ix_exports_artifact_id"), table_name="exports")
    op.drop_table("exports")

    op.drop_index(op.f("ix_slide_artifacts_template_id"), table_name="slide_artifacts")
    op.drop_index(op.f("ix_slide_artifacts_slide_plan_id"), table_name="slide_artifacts")
    op.drop_index(op.f("ix_slide_artifacts_render_status"), table_name="slide_artifacts")
    op.drop_index(op.f("ix_slide_artifacts_project_id"), table_name="slide_artifacts")
    op.drop_table("slide_artifacts")

    op.drop_index(op.f("ix_templates_template_id"), table_name="templates")
    op.drop_index(op.f("ix_templates_is_active"), table_name="templates")
    op.drop_table("templates")

    op.drop_index(op.f("ix_slide_plans_status"), table_name="slide_plans")
    op.drop_index(op.f("ix_slide_plans_project_id"), table_name="slide_plans")
    op.drop_index(op.f("ix_slide_plans_outline_id"), table_name="slide_plans")
    op.drop_index(op.f("ix_slide_plans_brief_id"), table_name="slide_plans")
    op.drop_table("slide_plans")

    op.drop_index(op.f("ix_outlines_status"), table_name="outlines")
    op.drop_index(op.f("ix_outlines_project_id"), table_name="outlines")
    op.drop_index(op.f("ix_outlines_brief_id"), table_name="outlines")
    op.drop_table("outlines")

    op.drop_index(op.f("ix_presentation_briefs_status"), table_name="presentation_briefs")
    op.drop_index(op.f("ix_presentation_briefs_source_bundle_id"), table_name="presentation_briefs")
    op.drop_index(op.f("ix_presentation_briefs_project_id"), table_name="presentation_briefs")
    op.drop_table("presentation_briefs")

    op.drop_index(op.f("ix_source_bundles_status"), table_name="source_bundles")
    op.drop_index(op.f("ix_source_bundles_project_id"), table_name="source_bundles")
    op.drop_table("source_bundles")

    op.drop_index(op.f("ix_project_files_upload_status"), table_name="project_files")
    op.drop_index(op.f("ix_project_files_project_id"), table_name="project_files")
    op.drop_index(op.f("ix_project_files_parse_status"), table_name="project_files")
    op.drop_index(op.f("ix_project_files_file_type"), table_name="project_files")
    op.drop_table("project_files")

    op.drop_index(op.f("ix_task_runs_task_type"), table_name="task_runs")
    op.drop_index(op.f("ix_task_runs_task_status"), table_name="task_runs")
    op.drop_index(op.f("ix_task_runs_project_id"), table_name="task_runs")
    op.drop_table("task_runs")

    op.drop_index(op.f("ix_projects_status"), table_name="projects")
    op.drop_index(op.f("ix_projects_owner_id"), table_name="projects")
    op.drop_index(op.f("ix_projects_name"), table_name="projects")
    op.drop_table("projects")
