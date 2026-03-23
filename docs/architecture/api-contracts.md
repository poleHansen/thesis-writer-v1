# API 契约基线

## 目标

阶段 1 仅定义接口契约，不要求全部实现业务逻辑。

## 项目接口

### POST /projects

创建项目。

请求体：

- name: string
- description: string | null
- source_mode: `chat` | `file` | `mixed`
- tags: string[]

响应体：

- project: Project

### GET /projects/{project_id}

获取项目详情。

响应体：

- project: Project
- latest_source_bundle: SourceBundle | null
- latest_brief: PresentationBrief | null
- latest_outline: Outline | null
- latest_slide_plan: SlidePlan | null
- latest_artifact: SlideArtifact | null
- latest_export: ExportJob | null

### GET /projects/{project_id}/status

获取项目状态与最近任务。

响应体：

- project_id: string
- project_status: ProjectStatus
- current_task: TaskRun | null
- recent_tasks: TaskRun[]

## 文件接口

### POST /projects/{project_id}/files

上传一个或多个输入文件。

请求体：

- files: multipart file[]
- source_label: string | null

响应体：

- files: ProjectFile[]
- task_run: TaskRun

## 规划接口

### POST /projects/{project_id}/brief:generate

基于 `SourceBundle` 生成 `PresentationBrief`。

请求体：

- force_regenerate: bool
- user_intent_override: UserIntent | null

响应体：

- brief: PresentationBrief
- task_run: TaskRun

### POST /projects/{project_id}/outline:generate

基于 `PresentationBrief` 生成提纲。

请求体：

- brief_id: string | null
- force_regenerate: bool

响应体：

- outline: Outline
- task_run: TaskRun

### POST /projects/{project_id}/slide-plan:generate

基于 `Outline` 生成逐页规划。

请求体：

- outline_id: string | null
- preferred_template_id: string | null
- force_regenerate: bool

响应体：

- slide_plan: SlidePlan
- task_run: TaskRun

## 渲染与导出接口

### POST /projects/{project_id}/render

触发 SVG 渲染。

请求体：

- slide_plan_id: string | null
- template_id: string | null
- rerender_slide_ids: string[]

响应体：

- task_run: TaskRun
- artifact: SlideArtifact | null

### POST /projects/{project_id}/export

触发 PPTX 或 PDF 导出。

请求体：

- artifact_id: string | null
- export_format: `pptx` | `pdf`

响应体：

- task_run: TaskRun
- export_job: ExportJob

## 模板接口

### GET /templates

获取模板列表。

查询参数：

- style_tag: string | null
- scenario_tag: string | null
- layout_mode: string | null

响应体：

- templates: TemplateMeta[]
