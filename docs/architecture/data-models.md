# 核心数据模型

## 目标

阶段 1 先固化系统核心对象，保证输入理解、方法论规划、SVG 渲染与导出链路共享同一套领域契约。

## 统一约束

- 所有主业务对象使用 `id` 作为主键，默认采用 UUID 字符串
- 所有时间字段统一使用 UTC `datetime`
- 所有状态字段通过枚举定义，不使用任意字符串
- 所有对象保留 `metadata` 或 `extra` 类型 JSON 扩展字段，以支持后续演进
- 所有文件路径均使用相对项目根目录的逻辑路径，不直接依赖绝对路径

## Project

| 字段                    | 类型          | 必填 | 默认值   | 生命周期              | 写入方             | 读取方           |
| ----------------------- | ------------- | ---- | -------- | --------------------- | ------------------ | ---------------- |
| id                      | string        | 是   | 自动生成 | 创建后固定            | API                | 全链路           |
| name                    | string        | 是   | 无       | 可更新                | API / Web          | 全链路           |
| description             | string        | 否   | null     | 可更新                | API / Web          | Web / Planner    |
| status                  | ProjectStatus | 是   | created  | 按状态机流转          | Worker / API       | 全链路           |
| source_mode             | SourceMode    | 是   | mixed    | 创建时确定，可调整    | API                | Intake / Planner |
| owner_id                | string        | 否   | null     | 创建时写入            | API                | 权限层           |
| tags                    | list[string]  | 否   | []       | 可更新                | API / Web          | Web              |
| current_template_id     | string        | 否   | null     | 规划或渲染前后更新    | Planner / Renderer | Renderer / Web   |
| latest_source_bundle_id | string        | 否   | null     | 解析后更新            | Ingestion          | Planner          |
| latest_brief_id         | string        | 否   | null     | 生成 Brief 后更新     | Methodology Engine | Web              |
| latest_outline_id       | string        | 否   | null     | 生成 Outline 后更新   | Methodology Engine | Web              |
| latest_slide_plan_id    | string        | 否   | null     | 生成 SlidePlan 后更新 | Methodology Engine | Renderer         |
| latest_artifact_id      | string        | 否   | null     | 渲染后更新            | Renderer           | Export           |
| last_error_code         | string        | 否   | null     | 失败时更新            | API / Worker       | Web / Ops        |
| metadata                | object        | 否   | {}       | 持续扩展              | 任意模块           | 全链路           |
| created_at              | datetime      | 是   | 当前时间 | 创建时写入            | API                | 全链路           |
| updated_at              | datetime      | 是   | 当前时间 | 每次变更更新          | API / Worker       | 全链路           |

## ProjectFile

| 字段              | 类型             | 必填 | 默认值        | 生命周期       | 写入方       | 读取方          |
| ----------------- | ---------------- | ---- | ------------- | -------------- | ------------ | --------------- |
| id                | string           | 是   | 自动生成      | 创建后固定     | API          | Ingestion / Web |
| project_id        | string           | 是   | 无            | 固定           | API          | 全链路          |
| file_name         | string           | 是   | 无            | 固定           | API          | Web / Parser    |
| file_type         | ProjectFileType  | 是   | auto_detected | 创建时确定     | API          | Parser          |
| storage_path      | string           | 是   | 无            | 固定           | API          | Parser / Export |
| mime_type         | string           | 否   | null          | 创建时写入     | API          | Parser          |
| size_bytes        | int              | 是   | 0             | 固定           | API          | Web             |
| checksum          | string           | 否   | null          | 创建后固定     | API          | Dedup / Audit   |
| upload_status     | FileUploadStatus | 是   | uploaded      | 解析前后可更新 | API / Worker | Web             |
| parse_status      | ParseStatus      | 是   | pending       | 解析阶段流转   | Parser       | Web / Planner   |
| parse_error       | string           | 否   | null          | 失败时更新     | Parser       | Web             |
| extracted_summary | string           | 否   | null          | 解析后更新     | Parser       | Web / Planner   |
| metadata          | object           | 否   | {}            | 持续扩展       | API / Parser | 全链路          |
| created_at        | datetime         | 是   | 当前时间      | 创建时写入     | API          | 全链路          |
| updated_at        | datetime         | 是   | 当前时间      | 每次变更更新   | API / Worker | 全链路          |

## SourceBundle

| 字段                | 类型                 | 必填 | 默认值   | 生命周期         | 写入方                 | 读取方             |
| ------------------- | -------------------- | ---- | -------- | ---------------- | ---------------------- | ------------------ |
| id                  | string               | 是   | 自动生成 | 创建后固定       | Ingestion              | Planner            |
| project_id          | string               | 是   | 无       | 固定             | Ingestion              | 全链路             |
| source_file_ids     | list[string]         | 否   | []       | 解析后可更新     | Ingestion              | Planner            |
| source_mode         | SourceMode           | 是   | mixed    | 固定             | Ingestion              | Planner            |
| user_intent         | UserIntent           | 否   | null     | 澄清后可更新     | API / Clarifier        | Planner            |
| raw_markdown        | string               | 否   | null     | 解析阶段生成     | Parser                 | Normalizer         |
| normalized_markdown | string               | 否   | null     | 规范化后生成     | Normalizer             | Methodology Engine |
| page_chunks         | list[SourceChunk]    | 否   | []       | 解析阶段生成     | Parser                 | Research / Planner |
| tables              | list[ExtractedAsset] | 否   | []       | 解析阶段生成     | Parser                 | Planner            |
| images              | list[ExtractedAsset] | 否   | []       | 解析阶段生成     | Parser                 | Planner / Renderer |
| citations           | list[string]         | 否   | []       | 解析或研究后更新 | Parser / Research      | Planner            |
| language            | string               | 否   | zh-CN    | 可检测更新       | Ingestion              | LLM Gateway        |
| status              | BundleStatus         | 是   | ready    | 解析链路更新     | Ingestion / Normalizer | Planner            |
| metadata            | object               | 否   | {}       | 持续扩展         | Ingestion              | 全链路             |
| created_at          | datetime             | 是   | 当前时间 | 创建时写入       | Ingestion              | 全链路             |
| updated_at          | datetime             | 是   | 当前时间 | 每次变更更新     | Ingestion / Worker     | 全链路             |

## PresentationBrief

| 字段                   | 类型         | 必填 | 默认值       | 生命周期     | 写入方                   | 读取方            |
| ---------------------- | ------------ | ---- | ------------ | ------------ | ------------------------ | ----------------- |
| id                     | string       | 是   | 自动生成     | 创建后固定   | Methodology Engine       | Web / Planner     |
| project_id             | string       | 是   | 无           | 固定         | Methodology Engine       | 全链路            |
| source_bundle_id       | string       | 是   | 无           | 固定         | Methodology Engine       | Planner           |
| presentation_goal      | string       | 是   | 无           | 可人工修订   | Methodology Engine / Web | Outline Generator |
| target_audience        | string       | 是   | 无           | 可人工修订   | Methodology Engine / Web | Outline Generator |
| core_message           | string       | 是   | 无           | 可人工修订   | Methodology Engine / Web | Outline Generator |
| storyline              | string       | 是   | 无           | 可人工修订   | Methodology Engine / Web | Outline Generator |
| recommended_page_count | int          | 是   | 12           | 可人工修订   | Methodology Engine / Web | Slide Planner     |
| tone                   | string       | 否   | professional | 可人工修订   | Methodology Engine / Web | Renderer          |
| style_preferences      | list[string] | 否   | []           | 可人工修订   | Methodology Engine / Web | Renderer          |
| risks                  | list[string] | 否   | []           | 可人工修订   | Methodology Engine / Web | Web               |
| assumptions            | list[string] | 否   | []           | 可人工修订   | Methodology Engine / Web | Web               |
| status                 | ReviewStatus | 是   | draft        | 审阅流转     | Methodology Engine / Web | 全链路            |
| metadata               | object       | 否   | {}           | 持续扩展     | Methodology Engine       | 全链路            |
| created_at             | datetime     | 是   | 当前时间     | 创建时写入   | Methodology Engine       | 全链路            |
| updated_at             | datetime     | 是   | 当前时间     | 每次变更更新 | Methodology Engine / Web | 全链路            |

## Outline

| 字段       | 类型                 | 必填 | 默认值   | 生命周期     | 写入方                   | 读取方        |
| ---------- | -------------------- | ---- | -------- | ------------ | ------------------------ | ------------- |
| id         | string               | 是   | 自动生成 | 创建后固定   | Methodology Engine       | Web / Planner |
| project_id | string               | 是   | 无       | 固定         | Methodology Engine       | 全链路        |
| brief_id   | string               | 是   | 无       | 固定         | Methodology Engine       | Planner       |
| title      | string               | 是   | 无       | 可人工修订   | Methodology Engine / Web | Slide Planner |
| chapters   | list[OutlineSection] | 是   | []       | 可人工修订   | Methodology Engine / Web | Slide Planner |
| summary    | string               | 否   | null     | 可人工修订   | Methodology Engine / Web | Web           |
| status     | ReviewStatus         | 是   | draft    | 审阅流转     | Methodology Engine / Web | 全链路        |
| metadata   | object               | 否   | {}       | 持续扩展     | Methodology Engine       | 全链路        |
| created_at | datetime             | 是   | 当前时间 | 创建时写入   | Methodology Engine       | 全链路        |
| updated_at | datetime             | 是   | 当前时间 | 每次变更更新 | Methodology Engine / Web | 全链路        |

## SlidePlan

| 字段             | 类型                | 必填 | 默认值   | 生命周期     | 写入方                   | 读取方         |
| ---------------- | ------------------- | ---- | -------- | ------------ | ------------------------ | -------------- |
| id               | string              | 是   | 自动生成 | 创建后固定   | Methodology Engine       | Renderer / Web |
| project_id       | string              | 是   | 无       | 固定         | Methodology Engine       | 全链路         |
| brief_id         | string              | 是   | 无       | 固定         | Methodology Engine       | Renderer       |
| outline_id       | string              | 是   | 无       | 固定         | Methodology Engine       | Renderer       |
| page_count       | int                 | 是   | 0        | 生成时确定   | Methodology Engine       | Web / Renderer |
| slides           | list[SlidePlanItem] | 是   | []       | 可人工修订   | Methodology Engine / Web | Renderer       |
| design_direction | string              | 否   | null     | 可人工修订   | Methodology Engine / Web | Renderer       |
| status           | ReviewStatus        | 是   | draft    | 审阅流转     | Methodology Engine / Web | 全链路         |
| metadata         | object              | 否   | {}       | 持续扩展     | Methodology Engine       | 全链路         |
| created_at       | datetime            | 是   | 当前时间 | 创建时写入   | Methodology Engine       | 全链路         |
| updated_at       | datetime            | 是   | 当前时间 | 每次变更更新 | Methodology Engine / Web | 全链路         |

## SlideArtifact

| 字段                | 类型         | 必填 | 默认值   | 生命周期        | 写入方   | 读取方       |
| ------------------- | ------------ | ---- | -------- | --------------- | -------- | ------------ |
| id                  | string       | 是   | 自动生成 | 创建后固定      | Renderer | Export / Web |
| project_id          | string       | 是   | 无       | 固定            | Renderer | 全链路       |
| slide_plan_id       | string       | 是   | 无       | 固定            | Renderer | Export       |
| template_id         | string       | 否   | null     | 渲染时确定      | Renderer | Web          |
| svg_output_dir      | string       | 否   | null     | 渲染时生成      | Renderer | Export       |
| svg_final_dir       | string       | 否   | null     | finalize 后更新 | Renderer | Export       |
| preview_image_paths | list[string] | 否   | []       | 渲染后更新      | Renderer | Web          |
| render_status       | RenderStatus | 是   | pending  | 渲染阶段流转    | Renderer | Web / Export |
| failed_slide_ids    | list[string] | 否   | []       | 失败时更新      | Renderer | Web          |
| log_path            | string       | 否   | null     | 渲染时更新      | Renderer | Ops          |
| metadata            | object       | 否   | {}       | 持续扩展        | Renderer | 全链路       |
| created_at          | datetime     | 是   | 当前时间 | 创建时写入      | Renderer | 全链路       |
| updated_at          | datetime     | 是   | 当前时间 | 每次变更更新    | Renderer | 全链路       |

## ExportJob

| 字段             | 类型         | 必填 | 默认值   | 生命周期     | 写入方         | 读取方    |
| ---------------- | ------------ | ---- | -------- | ------------ | -------------- | --------- |
| id               | string       | 是   | 自动生成 | 创建后固定   | Export Service | Web / Ops |
| project_id       | string       | 是   | 无       | 固定         | Export Service | 全链路    |
| artifact_id      | string       | 是   | 无       | 固定         | Export Service | 全链路    |
| export_format    | ExportFormat | 是   | pptx     | 固定         | Export Service | Web       |
| export_path      | string       | 否   | null     | 成功后写入   | Export Service | Web       |
| preview_pdf_path | string       | 否   | null     | 成功后可写入 | Export Service | Web       |
| status           | ExportStatus | 是   | pending  | 导出阶段流转 | Export Service | Web / Ops |
| error_message    | string       | 否   | null     | 失败时写入   | Export Service | Web       |
| metadata         | object       | 否   | {}       | 持续扩展     | Export Service | 全链路    |
| created_at       | datetime     | 是   | 当前时间 | 创建时写入   | Export Service | 全链路    |
| updated_at       | datetime     | 是   | 当前时间 | 每次变更更新 | Export Service | 全链路    |

## TemplateMeta

| 字段                   | 类型             | 必填 | 默认值   | 生命周期     | 写入方            | 读取方        |
| ---------------------- | ---------------- | ---- | -------- | ------------ | ----------------- | ------------- |
| id                     | string           | 是   | 自动生成 | 创建后固定   | Template Registry | 全链路        |
| template_id            | string           | 是   | 无       | 固定         | Template Registry | 全链路        |
| name                   | string           | 是   | 无       | 可更新       | Template Registry | 全链路        |
| style_tags             | list[string]     | 否   | []       | 可更新       | Template Registry | Planner / Web |
| scenario_tags          | list[string]     | 否   | []       | 可更新       | Template Registry | Planner / Web |
| supported_layout_modes | list[LayoutMode] | 否   | []       | 可更新       | Template Registry | Renderer      |
| density_range          | string           | 否   | medium   | 可更新       | Template Registry | Planner       |
| color_scheme           | list[string]     | 否   | []       | 可更新       | Template Registry | Renderer      |
| design_spec_path       | string           | 是   | 无       | 可更新       | Template Registry | Renderer      |
| preview_image_path     | string           | 否   | null     | 可更新       | Template Registry | Web           |
| version                | string           | 是   | 1.0.0    | 可更新       | Template Registry | Renderer      |
| is_active              | bool             | 是   | true     | 可更新       | Template Registry | Web           |
| metadata               | object           | 否   | {}       | 持续扩展     | Template Registry | 全链路        |
| created_at             | datetime         | 是   | 当前时间 | 创建时写入   | Template Registry | 全链路        |
| updated_at             | datetime         | 是   | 当前时间 | 每次变更更新 | Template Registry | 全链路        |

## TaskRun

| 字段           | 类型       | 必填 | 默认值   | 生命周期       | 写入方       | 读取方    |
| -------------- | ---------- | ---- | -------- | -------------- | ------------ | --------- |
| id             | string     | 是   | 自动生成 | 创建后固定     | API / Worker | 全链路    |
| project_id     | string     | 是   | 无       | 固定           | API / Worker | 全链路    |
| task_type      | TaskType   | 是   | 无       | 固定           | API / Worker | 全链路    |
| task_status    | TaskStatus | 是   | pending  | 流转更新       | Worker       | 全链路    |
| trigger_source | string     | 否   | api      | 固定           | API / Worker | Ops       |
| payload        | object     | 否   | {}       | 创建时写入     | API / Worker | Worker    |
| result         | object     | 否   | {}       | 完成时写入     | Worker       | API / Web |
| error_code     | string     | 否   | null     | 失败时写入     | Worker       | API / Web |
| error_message  | string     | 否   | null     | 失败时写入     | Worker       | API / Web |
| started_at     | datetime   | 否   | null     | 开始执行时写入 | Worker       | Ops       |
| finished_at    | datetime   | 否   | null     | 执行结束时写入 | Worker       | Ops       |
| created_at     | datetime   | 是   | 当前时间 | 创建时写入     | API / Worker | 全链路    |
| updated_at     | datetime   | 是   | 当前时间 | 每次变更更新   | Worker       | 全链路    |

## 内嵌对象

### UserIntent

- audience: string | null
- scenario: string | null
- purpose: string | null
- desired_page_count: int | null
- style_preferences: list[string]
- emphasize_points: list[string]
- constraints: list[string]

### SourceChunk

- chunk_id: string
- page_number: int | null
- heading_path: list[string]
- content: string
- token_count: int | 0
- chunk_type: string

### ExtractedAsset

- asset_id: string
- asset_type: string
- source_file_id: string | null
- page_number: int | null
- title: string | null
- description: string | null
- storage_path: string | null
- metadata: object

### OutlineSection

- section_id: string
- title: string
- objective: string
- key_message: string
- supporting_points: list[string]
- estimated_slides: int
- children: list[OutlineSection]

### SlidePlanItem

- slide_id: string
- slide_number: int
- title: string
- conclusion: string
- layout_mode: LayoutMode
- content_blocks: list[ContentBlock]
- speaker_notes: string | null
- data_refs: list[string]
- visual_priority: string | null

### ContentBlock

- block_id: string
- block_type: string
- heading: string | null
- body: string | null
- bullets: list[string]
- asset_refs: list[string]
- chart_hint: string | null
- emphasis: string | null

## 数据库映射建议

| 表名                | 对象              | 说明               |
| ------------------- | ----------------- | ------------------ |
| projects            | Project           | 项目主表           |
| project_files       | ProjectFile       | 原始文件与解析状态 |
| source_bundles      | SourceBundle      | 统一输入快照       |
| presentation_briefs | PresentationBrief | Brief 结果         |
| outlines            | Outline           | 提纲结果           |
| slide_plans         | SlidePlan         | 逐页规划结果       |
| slide_artifacts     | SlideArtifact     | 渲染产物           |
| templates           | TemplateMeta      | 模板元数据         |
| task_runs           | TaskRun           | 后台任务运行记录   |
| exports             | ExportJob         | 导出任务记录       |

## 项目状态机

```text
created
-> ingesting
-> parsed
-> analyzed
-> briefing
-> outlined
-> planned
-> rendering
-> finalized
-> exported
```

失败态：

- parse_failed
- plan_failed
- render_failed
- export_failed

## API 基础接口

- POST /projects
- GET /projects/{project_id}
- POST /projects/{project_id}/files
- POST /projects/{project_id}/brief:generate
- POST /projects/{project_id}/outline:generate
- POST /projects/{project_id}/slide-plan:generate
- POST /projects/{project_id}/render
- POST /projects/{project_id}/export
- GET /projects/{project_id}/status
- GET /templates
