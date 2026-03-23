# 数据库表设计基线

## 目标

为阶段 1 提供数据库实现蓝图，后续可映射到 SQLAlchemy 或 SQLModel。

## projects

- 主键: `id` UUID / string
- 关键字段: `name`, `description`, `status`, `source_mode`, `owner_id`
- 关联: `latest_source_bundle_id`, `latest_brief_id`, `latest_outline_id`, `latest_slide_plan_id`, `latest_artifact_id`
- 时间字段: `created_at`, `updated_at`
- JSON 扩展: `metadata`
- 索引建议: `status`, `owner_id`, `updated_at`

## project_files

- 主键: `id`
- 外键: `project_id -> projects.id`
- 关键字段: `file_name`, `file_type`, `storage_path`, `mime_type`, `size_bytes`
- 状态字段: `upload_status`, `parse_status`
- 时间字段: `created_at`, `updated_at`
- JSON 扩展: `metadata`
- 索引建议: `project_id`, `parse_status`

## source_bundles

- 主键: `id`
- 外键: `project_id -> projects.id`
- 关键字段: `source_mode`, `user_intent`, `raw_markdown`, `normalized_markdown`, `language`, `status`
- 时间字段: `created_at`, `updated_at`
- JSON 扩展: `metadata`
- 索引建议: `project_id`, `status`

## presentation_briefs

- 主键: `id`
- 外键: `project_id -> projects.id`, `source_bundle_id -> source_bundles.id`
- 关键字段: `presentation_goal`, `target_audience`, `core_message`, `storyline`, `recommended_page_count`, `tone`, `status`
- 时间字段: `created_at`, `updated_at`
- JSON 扩展: `metadata`
- 索引建议: `project_id`, `status`

## outlines

- 主键: `id`
- 外键: `project_id -> projects.id`, `brief_id -> presentation_briefs.id`
- 关键字段: `title`, `chapters`, `summary`, `status`
- 时间字段: `created_at`, `updated_at`
- JSON 扩展: `metadata`
- 索引建议: `project_id`, `brief_id`, `status`

## slide_plans

- 主键: `id`
- 外键: `project_id -> projects.id`, `brief_id -> presentation_briefs.id`, `outline_id -> outlines.id`
- 关键字段: `page_count`, `slides`, `design_direction`, `status`
- 时间字段: `created_at`, `updated_at`
- JSON 扩展: `metadata`
- 索引建议: `project_id`, `outline_id`, `status`

## slide_artifacts

- 主键: `id`
- 外键: `project_id -> projects.id`, `slide_plan_id -> slide_plans.id`
- 关键字段: `template_id`, `svg_output_dir`, `svg_final_dir`, `render_status`, `log_path`
- 时间字段: `created_at`, `updated_at`
- JSON 扩展: `metadata`
- 索引建议: `project_id`, `slide_plan_id`, `render_status`

## templates

- 主键: `id`
- 业务唯一键: `template_id`
- 关键字段: `name`, `style_tags`, `scenario_tags`, `supported_layout_modes`, `density_range`, `color_scheme`, `design_spec_path`, `version`, `is_active`
- 时间字段: `created_at`, `updated_at`
- JSON 扩展: `metadata`
- 索引建议: `template_id`, `is_active`

## task_runs

- 主键: `id`
- 外键: `project_id -> projects.id`
- 关键字段: `task_type`, `task_status`, `trigger_source`, `payload`, `result`, `error_code`, `error_message`, `started_at`, `finished_at`
- 时间字段: `created_at`, `updated_at`
- 索引建议: `project_id`, `task_status`, `task_type`, `created_at`

## exports

- 主键: `id`
- 外键: `project_id -> projects.id`, `artifact_id -> slide_artifacts.id`
- 关键字段: `export_format`, `export_path`, `preview_pdf_path`, `status`, `error_message`
- 时间字段: `created_at`, `updated_at`
- JSON 扩展: `metadata`
- 索引建议: `project_id`, `artifact_id`, `status`
