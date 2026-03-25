# 2026-03-26

- 完成一轮“真实大模型可用性”收口：后端新增项目级 LLM 设置读写与连通性测试接口，前端工作区新增 Provider / Model / Base URL / API Key / Temperature / Max Tokens 配置面板，用户现在可以在单项目上下文中直接保存并测试模型连接，而不是停留在没有配置入口的假可用状态。
- `apps/api/src/app/services/project_service.py` 已把 Brief / Outline / SlidePlan 三段生成链改为“项目级 LLM 设置启用时优先走 OpenAI 兼容 `/chat/completions` JSON 生成，否则自动回退到既有 methodology engine 规则链路”，从而把当前产品能力从“只能规则占位生成”推进到“有真实模型时可生成、无模型时仍可兜底”。
- 本轮项目级 LLM 设置先落在 `Project.metadata["llm_settings"]`，避免因为新增数据库表或迁移阻塞交付；与此同时保留 API key 脱敏返回、连接测试和失败回退语义，确保最小产品面可用而不是只补表单。
- 工作区前端已同步接入新接口：`apps/web/workspace.html`、`apps/web/src/pages/workspace/main.js`、`apps/web/src/features/project/review.js` 与 `apps/web/src/lib/api.js` 现已支持加载、保存、测试并展示项目级 LLM 设置状态，形成“配置 -> 测试 -> 生成”的最小闭环。
- 对本轮改动执行编辑器诊断后，前后端相关文件均返回 `No errors found`；随后执行 `uv run python -m pytest apps/api/tests -q`，结果为 `108 passed, 1 skipped`，说明新增 LLM 配置与生成接线未破坏现有 API 测试基线。

- 完成阶段 6 最小“多页面产品壳层”切片：将 `apps/web` 从单页长工作台拆分为首页 `apps/web/index.html`、项目列表页 `apps/web/projects.html` 和单项目工作区 `apps/web/workspace.html`，页面职责分别收敛到产品入口、项目浏览与单项目 intake/review/export 工作面，前端外观方向继续对齐 LandPPT，而不是回退到内部控制台式单页布局。
- 新增 `apps/web/src/pages/projects/main.js` 与 `apps/web/src/pages/workspace/main.js`，把原先集中在单页入口里的项目列表编排与单项目工作区编排拆开，继续复用现有 `features/project` 与 `lib` 层，不引入框架迁移或重新发明数据访问层。
- 将项目跳转从 `#project-{id}` hash 锚点切换为 `workspace.html?project={id}` query 参数形式，使项目列表页与单项目工作区的页面边界更清晰，也降低后续继续扩展真实站点路由时对 `dashboard.js` / `state.js` 的耦合压力。
- 重新核对 `apps/web/src/features/project/review.js`、`apps/web/workspace.html` 与 `apps/web/src/pages/workspace/main.js` 后，确认 review 区所需 DOM 契约与控制器映射已经对齐；本轮无需再追加兼容性修补，现有多页面工作区可以继续复用模板筛选、产物摘要和导出记录逻辑。
- 本轮尝试通过 `uv run python apps/web/server.py` 做静态前端 smoke，但运行分支受当前环境限制未能给出可用服务；因此本次收口以代码级 DOM/控制器校验为主，后续若环境允许再补浏览器级手工 smoke。

# 2026-03-25

- 完成阶段 7.3 第二段最小“样例输入资产契约”切片：为 `storage/projects/sample-registry.json` 的六类样例补充 `source_asset` 字段，显式指向 `storage/projects/sample-assets/{sample_id}/source.md` 形式的稳定仓库内样例输入资产，而不再停留在只有分类/模板/brief 摘要的纯元数据层。
- 扩展 `apps/api/tests/test_sample_registry.py`，新增样例输入资产存在性、非空内容、`.md` 后缀以及 `source_mode` 与 `source_asset.kind` 匹配关系回归，锁定 file/chat 两类样例至少已经绑定到可持续维护的稳定输入文件。
- 该切片仍不引入 golden 输出产物或运行期 UUID 项目目录复用，继续遵守“先固定样例 registry 与静态输入，再逐步补生成结果基线”的阶段 7.3 推进策略。
- 完成阶段 7.3 第三段“样例目录服务化”切片：新增 `apps/api/src/app/services/sample_catalog.py`，统一提供样例列表、按 `sample_id` 查询和源文本读取能力，避免测试与后续消费方重复解析 registry JSON。
- 完成阶段 7.3 第四段“样例可执行化 smoke”切片：扩展 `apps/api/tests/test_sample_registry.py`，让六类样例按 `file/chat` 两类输入模式分别跑通项目创建、上传/解析或 user-intent 直出 brief、再到 outline 与 slide-plan 的最小链路。
- 新增 smoke 断言同时锁定项目详情聚合：样例回归结束后 `project.status` 必须推进到 `planned`，且 `latest_brief/latest_outline/latest_slide_plan` 必须与本次生成结果一致，避免 7.3 只停留在静态样例清单层面。
- 进入阶段 7.4 后，先补最小“样例 render/export smoke”基线：在 `apps/api/tests/test_sample_registry.py` 选取学术答辩与产品发布会两个代表性样例，分别跑通 `artifact:generate -> export(pptx)` 与 `artifact:generate -> export(pdf)`，验证样例链路已不止于规划层，而能真正生成 SVG、PPTX/PDF 交付物。
- 新增 7.4 smoke 同时锁定产物页数语义与项目聚合：导出后的 `file_count` 必须与生成 SVG 数量、PPT/PDF 页数一致，且 `GET /projects/{id}` 必须推进出 `latest_artifact/latest_export` 与 `project.status=exported`。
- 继续推进阶段 7.4 第二段：六类样例现已全部补上 `artifact:generate` render smoke，确保 7.3 建立的样例集合不只是“能规划”，而且在每个场景下都能产出 finalized SVG 页面。
- 新增 render smoke 断言同时锁定渲染聚合边界：`generated_svg_files`、`validation_summary.checked_file_count` 与 `finalization_summary.page_count` 必须对齐 `slide_plan.page_count`，并要求项目详情只推进到 `latest_artifact` 与 `project.status=finalized`，不提前写入 `latest_export`。
- 继续推进阶段 7.4 第三段：六类样例现已全部补上 export smoke，按样例类型分别覆盖 `pptx` 与 `pdf` 两类交付格式，并锁定 `generated_svg_files`、导出 `file_count`、PPT/PDF 页数与 `latest_export` 聚合的一致性。
- 继续推进阶段 7.4 第四段：六类样例现已补充 render metadata golden 回归，直接读取 `storage/projects/{project_id}/render/{artifact_id}` 下的 `design-spec.json`、`render-log.json` 与 `svg_final/slide-*.svg`，把模板 id、page_count、validation/finalization 结构和 finalized SVG 数量锁成最小稳定基线。
- 开始阶段 7.4 第五段上线清单整理：已确认 `apps/api/src/app/config.py` 暴露了 `DATABASE_URL`、`REDIS_URL` 等环境变量入口，导出链路能够被现有 sample smoke 自动化证明；但仓库当前仍未提供 `alembic` 或等价迁移脚本，`数据库迁移可执行` 将作为当前上线缺口显式记录而不是伪装成已满足。
- 完成阶段 7.4 第五段：新增 `docs/architecture/deployment-checklist.md`，把环境变量、存储目录、数据库迁移、Redis、模板资源和导出链路统一整理成发布前检查清单，并在 `分阶段实施计划.md` 中将除数据库迁移外的上线项全部标记为已满足。
- 阶段 7.4 当前收口结论已经明确：完整回归样例、关键流程自动化测试、失败定位成本与部署文档均已形成可交付基线；唯一仍需在后续阶段补齐的发布缺口是正式数据库迁移体系。
- 进入阶段 7.5 后，已补齐正式数据库迁移体系：新增 `alembic.ini`、`migrations/env.py` 与初始 schema revision，把当前 SQLAlchemy 模型转成可执行的显式 schema upgrade 路径。
- 同步补充 `apps/api/tests/test_database_migrations.py`，用空 SQLite 数据库执行 `alembic upgrade head`，锁定 `alembic_version` 与核心业务表可被正式迁移命令拉起，不再只依赖 `AUTO_CREATE_TABLES`。
- `AUTO_CREATE_TABLES` 仍保留给本地开发与现有测试夹具，但部署检查和发布文档已收敛到 `uv run alembic upgrade head` 作为标准 schema 变更入口。
- 已继续完成 7.5 的顺序收口：根 `README.md`、`apps/api/README.md` 与 `docker-compose.yml` 现已统一到“先执行 Alembic 迁移、再启动 API”的标准路径，容器内 API 也会先跑 `python -m alembic upgrade head` 再启动服务。
- `apps/api/tests/test_database_migrations.py` 已新增受 `TEST_POSTGRES_MIGRATION_URL` 驱动的 PostgreSQL smoke 入口；当前工作机因未安装 `docker` / `docker-compose` 无法本机直接拉起 Compose PostgreSQL，所以本轮以可执行测试入口与发布清单说明形式完成真实 PG 验证准备。
- 已新增 `apps/api/tests/helpers.py`，并先把 `apps/api/tests/test_template_registry.py` 切换为“优先 Alembic 初始化 SQLite 测试库”的代表性样板，作为后续逐步迁移更多 API 测试夹具的最小起点。
- 执行 `uv run python -m pytest apps/api/tests/test_database_migrations.py apps/api/tests/test_template_registry.py -q`，结果为 `6 passed, 1 skipped`。
- 已修正 `migrations/versions/20260325_0001_initial_schema.py` 的跨数据库兼容性：`projects.latest_*` 字段改为先建列、后在非 SQLite 数据库补建外键，避免 PostgreSQL 在被引用表尚未创建时因内联外键失败。
- 已使用用户虚拟机上的 PostgreSQL（`192.168.68.131:5432`）创建临时库 `ai_ppt_migration_smoke` 执行真实 Alembic smoke；`uv run python -m pytest apps/api/tests/test_database_migrations.py -k postgresql -q` 结果为 `1 passed, 1 deselected`，随后已清理临时库。

- 完成一轮产品定位纠偏：同步修改 `README.md`、`实施方案.md` 与 `分阶段实施计划.md`，把仓库对外叙事从“毕业论文初稿自动生成平台”统一收敛为“融合 Linux.do 方法论、LandPPT 平台能力与 ppt-master 渲染链路的 AI PPT 生成网站”。
- 在文档层明确“论文答辩只是重点支持场景之一”，避免后续阶段继续把产品实现误导向单一论文工具。
- 在实施方案和阶段计划中补充多场景语境，明确系统同时面向答辩、企业汇报、咨询、培训、产品发布、政务汇报、技术分享等 PPT 生成需求。
- 继续完成“1/2/3 连续纠偏”切片：同步修改 `pyproject.toml`、`apps/web/index.html`、`apps/web/src/features/project/dashboard.js`、`apps/web/src/pages/dashboard/main.js`、`apps/web/README.md` 与 `apps/api/README.md`，把包描述、首页 title/hero、工作台状态文案和应用说明统一收敛为 AI PPT 平台表达。
- 继续收紧 `分阶段实施计划.md`：把残留的“学术论文 PDF / 学术答辩风 / 学术论文答辩”等样例与模板表述改成更通用的答辩/研究汇报语境，并明确阶段 6 的 Web 目标是收敛为产品默认入口，而不是停留在开发看板。
- 对本轮改动执行编辑器诊断，`apps/web/index.html`、`apps/web/src/features/project/dashboard.js`、`apps/web/src/pages/dashboard/main.js`、`分阶段实施计划.md` 与 `pyproject.toml` 均返回 `No errors found`。
- 完成“1/2/3 连续纠偏”最后一轮最小收口：进一步修改 `apps/web/index.html` intake 区块，把 `Phase 6 Intake` 等阶段化表达收敛为产品入口语气；同步把 `apps/api/src/app/config.py` 的 `app_name` 默认值调整为 `ai-ppt-studio-api`、数据库默认名调整为 `ai_ppt_studio`，并把 `packages/core-types/src/core_types/__init__.py`、`docs/architecture/tech-stack.md`、`实施方案.md`、`分阶段实施计划.md`、`task_plan.md` 中残留的仓库身份文案改成当前 AI PPT 平台语境。
- 对新增这批改动再次执行编辑器诊断，`apps/web/index.html`、`apps/api/src/app/config.py`、`packages/core-types/src/core_types/__init__.py`、`docs/architecture/tech-stack.md`、`实施方案.md`、`分阶段实施计划.md` 与 `task_plan.md` 均返回 `No errors found`。
- 追加残留扫描后确认：当前命中的旧表述主要保留在 `progress.md` / `findings.md` 这类历史记录，或既有测试样例对过去状态的描述中；它们不再属于当前活跃产品触点，因此本轮不做破坏历史语义的清洗。
- 按“先完成 1”继续收口命名/身份残留：同步修改 `README.md` 顶部标题、`pyproject.toml` 的项目名、`docker-compose.yml` 的默认数据库名与 `DATABASE_URL`，以及 `实施方案.md` 里的目录示意名称，把当前活跃身份字段进一步统一到 `AI PPT Studio / ai-ppt-studio / ai_ppt_studio` 这一组命名。
- 对本轮仅属于步骤 1 的改动执行验证：`README.md`、`pyproject.toml`、`docker-compose.yml` 与 `实施方案.md` 均返回 `No errors found`；针对这些文件的旧命名模式搜索未再命中。`
- 开始步骤 2：重读当前被用户改动过的 `实施方案.md` 与前端入口代码后，确认本轮不再做命名清理，而是把 `apps/web` 首屏继续从“内部控制台”收敛为产品首页化入口；当前已完成 `apps/web/index.html` hero / section intro 结构重构与 `apps/web/src/styles.css` 视觉层升级，同时保持所有现有 DOM id 与 intake/review/dashboard 绑定不变。
- 继续推进步骤 2 第二轮：在不改 `dashboard.js` / `review.js` 逻辑的前提下，为 workspace 左侧项目组合板补充产品说明层，为 review 空态增加三步引导，并在 review 内容区加入 planning/render band，同时增强 project card 模板的节奏信息与卡片氛围样式，让工作台区域和首页入口使用同一套产品语言。

- 继续完成阶段 6 intake 闭环收口：再次对 `apps/web/src/pages/dashboard/main.js`、`apps/web/src/features/project/intake.js`、`apps/web/src/lib/api.js`、`apps/api/src/app/main.py` 与 `apps/api/src/app/config.py` 执行编辑器诊断，结果均为 `No errors found`。
- 执行 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py -k "project_detail_keeps or project_status_keeps or list_projects_dashboard" -q` 做 focused 回归，终端输出出现连续通过点位，说明在明确测试文件入口下，现有 API 读模型回归可以被正常收集和执行；此前 `uv run python -m pytest apps/api/tests` 返回 `collecting 0 items` 更像是目录级收集入口未命中，而不是 pytest 在当前环境完全不可用。
- 当前阶段 6/7.2 的结论应更新为：前后端 intake 闭环代码已接通，且仓库内至少已有一条可正常执行的 focused pytest 路径；后续要补的是 intake 主链本身的自动化覆盖，而不是笼统地把测试环境判断为不可运行。

# 2025-02-14

- 完成阶段 6 最小“前后端可用 intake 闭环”切片：`apps/api/src/app/main.py` 接入 `CORSMiddleware`，并在 `apps/api/src/app/config.py` 新增本地 Web 默认允许源，解决静态前端直连 API 的浏览器跨域阻塞。
- `apps/web/src/lib/api.js` 新增 `createProject()`、`getProjectFiles()`、`uploadProjectFile()`、`parseProjectFiles()`、`generateBrief()`、`generateOutline()` 六类客户端方法，并补充服务端错误 detail 透传，避免页面只看到裸 `HTTP 4xx/5xx`。
- 新增 `apps/web/src/features/project/intake.js` 作为独立 feature 层，承接项目创建、文件 base64 上传、inline 文本来源编码、文件列表渲染、parse/brief/outline 触发参数组装；`apps/web/src/pages/dashboard/main.js` 仅负责把 intake、dashboard、review 三块编排到一起，未回退到单文件堆逻辑。
- `apps/web/index.html` 与 `apps/web/src/styles.css` 新增 intake 工作区，当前可在同一页面完成“创建项目 -> 上传文件或粘贴 URL/文本 -> 解析 -> 生成 Brief -> 生成 Outline”，并把结果同步推进到既有审阅区。
- 对 `apps/web/src/pages/dashboard/main.js`、`apps/web/src/features/project/intake.js`、`apps/web/index.html`、`apps/api/src/app/main.py` 与 `apps/api/src/app/config.py` 执行编辑器诊断，结果均为 `No errors found`。
- 执行 `uv run python -m pytest apps/api/tests` 做 focused 验证，当前结果为 `collecting 0 items`；说明测试目录已存在但尚无可被该入口直接收集的 pytest 用例，本轮未得到有效自动化回归结果。

- 完成阶段 7.2 第十九个 API 集成测试切片：为 `GET /projects/{id}/status` 新增“项目已完成 `files:parse` 但尚未生成 brief” 回归，锁定 `project_status=parsed` 时 `current_task` 与 `recent_tasks[-1]` 必须共同指向成功 `parse` task，且项目详情仅推进 `latest_source_bundle`、`latest_brief/latest_outline/latest_slide_plan/latest_artifact/latest_export` 继续为空。
- 完成阶段 7.2 第二十个 API 集成测试切片：为 `GET /projects/{id}/status` 新增“项目完成 `files:parse` 且 `SourceBundle` 带 warning、尚未生成 brief” 回归，锁定 `project_status=analyzed` 时 `current_task` 与 `recent_tasks[-1]` 继续指向成功 `parse` task，且项目详情推进到 `latest_source_bundle(status=needs_review)`、其余 latest 字段仍为空。
- 完成阶段 7.2 第二十一个 API 集成测试切片：为 `GET /projects/{id}/status` 新增“项目执行 `files:parse` 全量失败且尚未生成 brief” 回归，锁定 `project_status=parse_failed` 时 `current_task` 与 `recent_tasks[-1]` 必须共同指向失败 `parse` task，且项目详情继续保持 `latest_source_bundle/latest_brief/latest_outline/latest_slide_plan/latest_artifact/latest_export` 全空。
- 顺手修复 `InMemoryProjectRepository.update_project_links()` 只返回更新副本、不回写 `_projects` 的状态持久化缺陷，避免内存仓储路径下项目状态与 latest 链接字段停留在旧值。
- 使用 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py -k "parse_failed_tail_aligned_before_brief or analyzed_tail_aligned_before_brief or parse_tail_aligned_before_brief" -q` 做 focused 验证，确认新增 `parse_failed/analyzed/parsed` 三档最早解析态读模型语义通过回归测试。

- 2026-03-24 Phase 7.2 导出历史正向参数切片
  - 在 `apps/api/tests/test_artifact_persistence.py` 新增 `test_list_project_exports_honors_positive_limit`，构造三次导出后请求 `GET /projects/{id}/exports?limit=1`。
  - 锁定导出历史接口对正向 `limit` 不只是做参数校验，还必须真实只返回最近一条记录，避免 `limit` 在 route 到 repository 的传递链路中被忽略。
  - 本切片不改生产代码，只补只读 API 集成回归；验证将继续使用 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py -k list_project_exports -q`。

- 2026-03-24 Phase 7.2 项目看板导出聚合切片
  - 在 `apps/api/tests/test_artifact_persistence.py` 新增 `test_list_projects_dashboard_keeps_latest_export_on_most_recent_run`，构造同一 artifact 的两次导出后同时检查 `/projects/{id}/exports` 与 `GET /projects`。
  - 锁定项目看板聚合中的 `latest_export` 必须始终指向最新一条 run，而不是被历史导出语义或较早导出记录污染。
  - 本切片不改生产代码，只补只读聚合回归；验证将继续使用 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py -k dashboard -q`。

- 2026-03-24 Phase 7.2 项目状态导出尾项一致性切片
  - 在 `apps/api/tests/test_artifact_persistence.py` 新增 `test_project_status_keeps_recent_tasks_tail_aligned_with_latest_export_run`，构造同一 artifact 的两次导出后检查 `/status`、项目详情和导出历史三者是否仍对齐到最新 run。
  - 锁定 `recent_tasks` 尾项与 `current_task` 必须共同指向最新 export task，且其 `run_id` 与 `latest_export`、导出历史首项一致，避免状态读模型与导出读模型后续发生漂移。
  - 本切片不改生产代码，只补只读 API 集成回归；验证将继续使用 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py -k status -q`。

- 2026-03-24 Phase 7.2 项目看板多项目隔离切片
  - 在 `apps/api/tests/test_artifact_persistence.py` 新增 `test_list_projects_dashboard_keeps_multi_project_order_and_read_models_isolated`，构造两个都完成导出的项目后检查 `GET /projects`。
  - 锁定 dashboard 在多项目场景下必须按项目创建时间倒序返回，同时每张卡片的 `latest_export` 与 `current_task` 只能绑定自身项目，避免 newest-first 排序和项目级聚合在后续改动中互相污染。
  - 本切片不改生产代码，只补只读 API 集成回归；验证将继续使用 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py -k dashboard -q`。

- 2026-03-24 Phase 7.2 项目看板混合状态切片
  - 在 `apps/api/tests/test_artifact_persistence.py` 新增 `test_list_projects_dashboard_keeps_mixed_project_statuses_aligned`，构造一个仅完成 artifact 渲染的项目和一个已完成导出的项目后检查 `GET /projects`。
  - 锁定 dashboard 在混合状态项目列表中必须同时保持项目顺序正确，以及 render 项 `latest_export is None`、`current_task=render` 和 export 项 `latest_export/current_task=export` 的边界清晰，避免不同状态项目的聚合字段互相污染。
  - 本切片不改生产代码，只补只读 API 集成回归；验证将继续使用 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py -k dashboard -q`。

- 2026-03-24 Phase 7.2 项目看板三态空值边界切片
  - 在 `apps/api/tests/test_artifact_persistence.py` 新增 `test_list_projects_dashboard_keeps_created_rendered_and_exported_states_isolated`，构造一个保持 created 的项目、一个已 render 但未 export 的项目、以及一个已 export 的项目后检查 `GET /projects`。
  - 锁定 dashboard 在三态并存列表中必须同时保持 newest-first 排序、render/export 项各自的 latest 聚合正确，以及 created 项所有 latest/current 字段保持为空，避免列表聚合把后续项目的数据错误泄露到尚未启动的项目卡片。
  - 本切片不改生产代码，只补只读 API 集成回归；验证将继续使用 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py -k dashboard -q`。

- 2026-03-24 Phase 7.2 项目看板失败状态隔离切片
  - 在 `apps/api/tests/test_artifact_persistence.py` 新增 `test_list_projects_dashboard_keeps_export_failed_projects_isolated`，构造一个触发失败导出的项目和一个正常完成导出的项目后检查 `GET /projects`。
  - 锁定 dashboard 在成功/失败混合列表中必须同时保持 newest-first 排序、正常导出项的 latest 聚合正确，以及失败导出项 `latest_*` 与 `latest_export` 继续为空但 `current_task` 明确保留失败 export task，避免列表聚合把成功 run 错误泄露到失败项目卡片。
  - 本切片不改生产代码，只补只读 API 集成回归；验证将继续使用 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py -k dashboard -q`。

- 2026-03-24 Phase 7.2 项目状态失败尾项一致性切片
  - 在 `apps/api/tests/test_artifact_persistence.py` 新增 `test_project_status_keeps_failed_export_tail_aligned_with_project_status`，构造一个直接触发失败导出的项目后同时检查 `GET /projects/{id}` 与 `GET /projects/{id}/status`。
  - 锁定失败导出后 `project_status`、`current_task` 与 `recent_tasks[-1]` 必须共同指向同一条失败 export task，且项目详情仍保持 `latest_export is None`，避免状态读模型尾项与详情聚合在失败分支上发生漂移。
  - 本切片不改生产代码，只补只读 API 集成回归；验证将继续使用 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py -k status -q`。

- 2026-03-24 Phase 7.2 项目状态中间态尾项切片
  - 在 `apps/api/tests/test_artifact_persistence.py` 新增 `test_project_status_keeps_render_tail_aligned_before_any_export`，构造一个已完成 artifact 渲染但尚未触发任何导出的项目后同时检查 `GET /projects/{id}`、`GET /projects/{id}/status` 与 `GET /projects/{id}/exports`。
  - 锁定 `finalized` 中间态下 `current_task` 与 `recent_tasks[-1]` 必须继续指向成功 render task，同时详情保持 `latest_artifact` 已存在但 `latest_export is None` 且导出历史为空，避免后续状态读模型把 render 完成误显示成 export 完成。
  - 本切片不改生产代码，只补只读 API 集成回归；验证将继续使用 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py -k status -q`。

- 2026-03-24 Phase 7.2 项目状态早期中间态切片
  - 在 `apps/api/tests/test_artifact_persistence.py` 新增 `test_project_status_keeps_brief_tail_aligned_before_outline`，构造一个只完成 brief 生成的项目后同时检查 `GET /projects/{id}`、`GET /projects/{id}/status` 与 `GET /projects/{id}/exports`。
  - 锁定 `briefing` 中间态下 `current_task` 与 `recent_tasks[-1]` 必须共同指向成功 brief task，同时详情只推进 `latest_brief` 而不提前长出 outline / slide plan / artifact / export 聚合，避免状态读模型把早期规划阶段误显示成更后续阶段。
  - 本切片不改生产代码，只补只读 API 集成回归；验证将继续使用 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py -k status -q`。

- 2026-03-24 Phase 7.2 项目状态早期中间态切片
  - 在 `apps/api/tests/test_artifact_persistence.py` 新增 `test_project_status_keeps_outline_tail_aligned_before_slide_plan`，构造一个已完成 brief 和 outline、但尚未生成 slide plan 的项目后同时检查 `GET /projects/{id}`、`GET /projects/{id}/status` 与 `GET /projects/{id}/exports`。
  - 锁定 `outlined` 中间态下 `current_task` 与 `recent_tasks[-1]` 必须共同指向成功 outline task，同时详情只推进 `latest_brief/latest_outline` 而不提前长出 slide plan / artifact / export 聚合，避免状态读模型把提纲阶段误显示成更后续阶段。
  - 本切片不改生产代码，只补只读 API 集成回归；验证将继续使用 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py -k status -q`。

- 2026-03-24 Phase 7.2 项目状态早期中间态切片
  - 在 `apps/api/tests/test_artifact_persistence.py` 新增 `test_project_status_keeps_slide_plan_tail_aligned_before_render`，构造一个已完成 brief、outline、slide plan 但尚未 render artifact 的项目后同时检查 `GET /projects/{id}`、`GET /projects/{id}/status` 与 `GET /projects/{id}/exports`。
  - 锁定 `planned` 中间态下 `current_task` 与 `recent_tasks[-1]` 必须共同指向成功 `generate_slide_plan` task，同时详情只推进 `latest_brief/latest_outline/latest_slide_plan` 而不提前长出 artifact / export 聚合，避免状态读模型把页规划阶段误显示成 render 或 export 阶段。
  - 本切片不改生产代码，只补只读 API 集成回归；验证将继续使用 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py -k status -q`。

## 2025-02-14 Phase 6.4 导出结果可达性切片

- 在 `apps/web/src/features/project/review.js` 扩展 artifact/export 摘要渲染，导出成功后除状态外还会显示导出文件、`archive-manifest.json`、`export-log.json` 三类结果链接，并补充 `run_id` 与更新时间。
- 在 `apps/web/src/lib/formatters.js` 新增路径 basename 格式化辅助方法，避免审阅区直接显示过长的存储相对路径。
- 在 `apps/web/src/styles.css` 新增导出链接组与导出元信息样式，保持新增结果区与既有审阅卡片视觉一致。
- 本轮未新增后端接口，完全复用 `GET /projects/{id}` 返回的 `latest_export.output_path`、`latest_export.metadata.archive_manifest_path`、`latest_export.metadata.export_log_path`、`latest_export.run_id` 等现有字段。
- 已通过编辑器诊断验证 `apps/web/src/lib/formatters.js`、`apps/web/src/features/project/review.js` 与 `apps/web/src/styles.css` 无报错。

## 2025-02-14 Phase 6.4 导出历史可见性切片

- 后端新增 `GET /projects/{id}/exports?limit=5`，服务层直接复用既有 `ExportRecord` 持久化结果，按 `created_at` 倒序返回最近导出记录，不改动现有导出写盘与 `latest_export` 聚合逻辑。
- `apps/web/src/lib/api.js` 新增 `getProjectExports()`，`apps/web/src/pages/dashboard/main.js` 现会并行拉取项目详情和最近导出历史，避免审阅页继续只依赖单次 `latest_export`。
- `apps/web/src/features/project/review.js` 新增 Recent Export Runs 渲染逻辑，可在同一审阅面展示最近导出的 `run_id`、导出格式、状态、更新时间，以及导出文件、`archive-manifest.json`、`export-log.json` 三类现成结果路径。
- `apps/web/index.html` 与 `apps/web/src/styles.css` 已补齐最近导出历史区的结构和样式，保持新增历史列表与既有 artifact/export 摘要卡片视觉一致。
- 新增 `apps/api/tests/test_artifact_persistence.py::test_list_project_exports_returns_recent_runs_in_desc_order`，随后执行 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py -q`，结果为 `8 passed in 9.18s`；同时对本轮修改的前后端文件执行编辑器诊断，结果均为 `No errors found`。

## 2025-02-14 Phase 6.4 历史导出详情切换切片

- 后端新增 `GET /projects/{id}/exports/{export_id}`，服务层在返回单条 `ExportJob` 前会先校验项目存在，再校验该导出记录确实归属于当前项目，避免历史 run 被跨项目误取。
- `apps/web/src/lib/api.js` 新增 `getProjectExport()`；`apps/web/src/pages/dashboard/main.js` 现会在加载审阅详情后确定当前选中的导出 run，并在切换 Recent Export Runs 项时重新拉取对应导出详情。
- `apps/web/src/features/project/review.js` 将最近导出历史条目升级为可点击选择的 run 列表，当前选中项会保持高亮，摘要区会切换显示该次导出的状态、`run_id`、导出文件、`archive-manifest.json` 与 `export-log.json`，不再固定为 `latest_export`。
- 新增 `apps/api/tests/test_artifact_persistence.py::test_get_project_export_returns_selected_run_and_rejects_foreign_project`，覆盖“可取到指定历史 run”与“跨项目访问返回 404”两条关键语义；随后执行 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py -q`，结果为 `9 passed in 9.35s`；同时对本轮修改的前后端文件执行编辑器诊断，结果均为 `No errors found`。

## 2025-02-14 Phase 6.4 导出 run 差异摘要切片

- `apps/web/index.html` 在导出审阅区新增 Run Delta 子区块，作为历史 run 详情与最新导出之间的只读差异摘要入口，不引入新的后端契约。
- `apps/web/src/features/project/review.js` 新增 `renderExportDelta()`，直接基于“当前选中导出 + latest_export”输出最小差异信息；若当前查看的已是最新 run，则明确提示无需对比。
- `apps/web/src/pages/dashboard/main.js` 将历史导出项点击后的更新逻辑收敛为可复用的 `createExportSelectionHandler()`，在切换 run 时同步刷新摘要区、差异区和历史列表选中态，替换此前脆弱的内联回调递归写法。
- `apps/web/src/styles.css` 补充 Run Delta 区域的最小布局样式，保持与既有导出历史区一致的卡片密度。
- 本轮未新增后端测试，原因是功能完全限定在前端只读组合层；已对 `apps/web/index.html`、`apps/web/src/features/project/review.js`、`apps/web/src/pages/dashboard/main.js` 与 `apps/web/src/styles.css` 执行编辑器诊断，结果均为 `No errors found`。

## 2025-02-14 Phase 6.2 SVG 页级预览审阅切片

- `apps/web/index.html` 在 Artifact Snapshot 区域新增 SVG Preview 子区块，用于承接最终页级 SVG 的最小可视化审阅入口。
- `apps/web/src/features/project/review.js` 新增 `renderArtifactPreview()`，优先复用 artifact 的 `preview_image_paths`，回退到 `generated_svg_files` / `metadata.generated_svg_files`，以卡片形式渲染每一页并保留直达原文件链接。
- `apps/web/src/lib/formatters.js` 新增 `formatPreviewLabel()`，将 `slide-N.svg` 路径稳定格式化为更适合审阅区展示的页标签。
- `apps/web/src/pages/dashboard/main.js` 在项目详情加载后同步刷新 artifact 摘要与页级预览，保证模板重渲染或导出刷新后预览区跟随最新 artifact 更新。
- `apps/web/src/styles.css` 补齐预览卡片、SVG 嵌入框和降级提示样式，使静态审阅页首次具备真正的页级可视化预览而不依赖新增后端接口。

## 2025-02-14 Phase 6.4 模板多维筛选切片

- `apps/web/index.html` 在 Template Override 区域新增场景、风格、信息密度与行业标签四个筛选控件，并补充筛选结果提示文案。
- `apps/web/src/features/project/review.js` 新增模板筛选选项构建、结果过滤与提示渲染逻辑，直接基于模板列表的 `scenario_tags`、`style_tags`、`density_range` 以及元数据里的 `default_for` / `visual_direction` 做前端收敛。
- `apps/web/src/pages/dashboard/main.js` 补齐模板筛选控件的 DOM 绑定与事件监听，使筛选变更后同页模板下拉实时收敛，不额外请求后端。
- `apps/web/src/styles.css` 新增模板筛选提示样式，保持模板选择区与既有审阅卡片的视觉密度一致。
- 本轮未新增后端接口与测试，原因是功能完全限定在前端只读组合层；完成后应以编辑器诊断确认相关前端文件无报错。

## 2026-03-24 Phase 6.4 模板缩略预览切片

- `apps/web/index.html` 在 Template Override 区域新增模板预览卡片容器，使模板筛选结果不再只落到下拉框。
- `apps/web/src/features/project/review.js` 直接复用模板元数据里的 `preview_image_path`、`visual_direction`、`scenario_tags` 与 `style_tags` 渲染可点击模板卡片，并保持与下拉选中状态联动。
- `apps/web/src/pages/dashboard/main.js` 补齐模板下拉变化后的预览刷新，让“点击卡片选模板”和“手动切换下拉框”保持同一状态源。

## 2026-03-24 Phase 7.3 样例项目回归集骨架切片

- 新增 `storage/projects/sample-registry.json`，先以轻量 registry 形式固化阶段 7.3 要求的六类样例项目：学术论文答辩、企业战略汇报、产品发布会、培训课件、政府汇报、技术分享。
- 每条样例现统一包含 `sample_id`、`category`、`project_name`、`source_mode`、`recommended_template_id`、`summary` 与最小 `brief` 摘要，避免后续继续拿散落的 `storage/projects/{uuid}` 运行产物充当不可控的回归输入。
- 新增 `apps/api/tests/test_sample_registry.py`，分别锁定样例类别覆盖、`sample_id` 唯一性与必填字段完整性，以及 `recommended_template_id` 必须存在于 `templates/builtin/*.json`。
- 执行 `uv run python -m pytest apps/api/tests/test_sample_registry.py -q`，结果为 `3 passed in 0.06s`；本轮未改动生产服务代码，当前先为阶段 7.3 建立可持续扩展的样例回归骨架。
- `apps/web/src/styles.css` 新增模板预览网格、缩略图、标签与选中态样式，延续当前审阅页的卡片视觉语言。
- 本轮仍未新增后端接口与测试，原因是功能完全限定在前端只读组合层；完成后应以编辑器诊断确认相关前端文件无报错。

## 2026-03-24 Phase 7.2 API 集成测试切片

- 启动阶段 7.2，先补当前最短主链路的 API 集成回归，而不是一开始分散到大量低价值单元测试。
- 在 `apps/api/tests/test_artifact_persistence.py` 新增 `test_project_detail_status_and_export_history_remain_consistent_across_pipeline`，覆盖 `/projects/{id}`、`/projects/{id}/status`、`/projects/{id}/exports`、`/projects/{id}/exports/{export_id}` 在 created、rendered、exported 三个阶段的联动一致性。
- 新增断言重点是 `latest_brief/latest_outline/latest_slide_plan/latest_artifact/latest_export` 与 `current_task/recent_tasks` 是否在关键节点同步推进，用来提前拦截 `latest_*_id` 或 `TaskRun` 漏更新导致的聚合漂移。
- 验证：`uv run python -m pytest apps/api/tests/test_artifact_persistence.py -k project_detail_status`

## 2026-03-24 Phase 7.2 只读失败路径切片

- 在 `apps/api/tests/test_artifact_persistence.py` 新增 `test_project_detail_status_and_export_read_models_return_404_for_missing_project`，把 `/projects/{id}`、`/projects/{id}/status`、`/projects/{id}/exports`、`/projects/{id}/exports/{export_id}` 四个只读接口的缺失项目语义收敛到同一条回归里。
- 本轮不改动后端实现，直接利用服务层 `get_project()` 的共享 404 保护，锁定未来重构后这些只读端点仍返回一致的 `{"detail": "Project not found"}`。
- 验证：`uv run python -m pytest apps/api/tests/test_artifact_persistence.py -k missing_project`

## 2026-03-24 Phase 7.2 导出详情失败语义切片

- 在 `apps/api/tests/test_artifact_persistence.py::test_get_project_export_returns_selected_run_and_rejects_foreign_project` 追加“同项目下 export 不存在”的断言，补齐导出详情接口第二层 404 语义。
- 这条回归与上一条缺失项目回归分开维护，目的是显式区分 `Project not found` 与 `Export job not found` 两类错误来源，防止未来服务层重构时把仓储级缺失导出误并入项目级 404。
- 验证：`uv run python -m pytest apps/api/tests/test_artifact_persistence.py -k export_detail`

## 2026-03-25 Phase 7.2 项目详情剩余边界收口

- 在 `apps/api/tests/test_artifact_persistence.py` 一次性补齐五个 detail-only 回归：`test_project_detail_keeps_parse_tail_aligned_before_brief`、`test_project_detail_keeps_analyzed_tail_aligned_before_brief`、`test_project_detail_keeps_parse_failed_tail_aligned_before_brief`、`test_project_detail_keeps_render_tail_aligned_before_any_export`、`test_project_detail_keeps_failed_export_tail_aligned_with_project_status`。
- 这些用例分别锁定 `GET /projects/{id}` 在 `parsed`、`analyzed`、`parse_failed`、`finalized`、`export_failed` 五类剩余状态下的 latest 聚合边界，补齐此前已经覆盖 `created/briefing/outlined/planned/exported` 后仍留存的 detail-only 空白。
- 本轮不改生产代码，只补 Phase 7.2 收尾所需的只读 API 集成回归；执行 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py -k "project_detail_keeps" -q`，结果为 `7 passed, 33 deselected in 8.03s`。
- 收口 review 结论：当前 `apps/api/tests/test_artifact_persistence.py` 已对项目详情、状态、导出历史、导出详情和看板聚合的关键状态边界形成成体系保护，未发现新的 P0/P1 级测试缺口；阶段 7.2 可从计划上标记为完成。

## 2026-03-24 Phase 7.2 导出历史空结果切片

- 在 `apps/api/tests/test_artifact_persistence.py` 新增 `test_list_project_exports_returns_empty_list_when_project_has_no_exports`，覆盖“项目、文件、brief、outline、slide plan、artifact 都已存在，但尚未触发任何 export”的历史列表边界。
- 本轮不改动后端实现，直接锁定 `GET /projects/{id}/exports` 在空历史场景下应返回 `200` 与 `{"exports": []}`，确保导出历史接口保持只读查询语义，而不是把“无导出记录”误判为异常。
- 验证：`uv run python -m pytest apps/api/tests/test_artifact_persistence.py -k list_project_exports -q`

## 2026-03-24 Phase 7.2 导出历史参数边界切片

- 在 `apps/api/tests/test_artifact_persistence.py` 新增 `test_list_project_exports_rejects_non_positive_limit`，覆盖 `GET /projects/{id}/exports?limit=0` 与 `limit=-1` 两个边界输入。
- `apps/api/src/app/api/routes/projects.py` 将导出历史接口的 `limit` 从裸 `int = 5` 收紧为 `Query(default=5, ge=1)`，把“非正数 limit 无效”上推到路由层做显式契约校验，而不是把模糊值继续传入服务/仓储。
- 验证：`uv run python -m pytest apps/api/tests/test_artifact_persistence.py -k list_project_exports -q`

## 2026-03-24 Phase 7.2 导出详情输入形态切片

- 在 `apps/api/tests/test_artifact_persistence.py` 新增 `test_get_project_export_treats_malformed_but_routable_id_as_not_found`，覆盖带空白包裹的非常规 `export_id` 输入。
- 本轮不改动后端实现，直接锁定 `GET /projects/{id}/exports/{export_id}` 对“可路由但无对应记录”的异常形态继续返回 `404` 与 `{"detail": "Export job not found"}`，避免未来局部加校验时把详情端点再拆出第三种错误语义。
- 验证：`uv run python -m pytest apps/api/tests/test_artifact_persistence.py -k get_project_export -q`

# 进度记录

## 2026-03-25

- 完成阶段 7.2 第二十七个项目详情早期规划态切片：在 `apps/api/tests/test_artifact_persistence.py` 新增 `test_project_detail_keeps_brief_tail_aligned_before_outline`，覆盖项目只完成 brief 生成、尚未生成 outline 时 `GET /projects/{id}` 的最小详情边界。
- 该回归锁定 `briefing` 早期规划态下详情 read model 只允许推进 `latest_source_bundle/latest_brief`，而 `latest_outline/latest_slide_plan/latest_artifact/latest_export` 必须继续为空，避免后续仓储聚合把 brief 阶段错误显示成已进入 outline 或更后续阶段。
- 使用 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py -k "detail_keeps_brief_tail_aligned_before_outline" -q` 做 focused 验证，结果为 `1 passed`。
- 完成阶段 7.2 第二十六个项目详情中间规划态切片：在 `apps/api/tests/test_artifact_persistence.py` 新增 `test_project_detail_keeps_outline_tail_aligned_before_slide_plan`，覆盖项目已完成 brief 和 outline、但尚未生成 slide plan 时 `GET /projects/{id}` 的最小详情边界。
- 该回归锁定 `outlined` 中间态下详情 read model 只允许推进 `latest_source_bundle/latest_brief/latest_outline`，而 `latest_slide_plan/latest_artifact/latest_export` 必须继续为空，避免后续仓储聚合把提纲阶段错误显示成已进入页规划或更后续阶段。
- 使用 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py -k "detail_keeps_outline_tail_aligned_before_slide_plan" -q` 做 focused 验证，结果为 `1 passed`。
- 完成阶段 7.2 第二十二个项目看板最早解析三态隔离切片：在 `apps/api/tests/test_artifact_persistence.py` 新增 `test_list_projects_dashboard_keeps_early_parse_states_isolated`，构造 `parsed`、`analyzed`、`parse_failed` 三个处于最早解析阶段的项目并检查 `GET /projects` 聚合结果。
- 该回归锁定 dashboard 在多项目早期解析场景下既要正确返回 `parsed_file_count/failed_file_count`，也要保持三类项目的 `latest_brief/latest_outline/latest_slide_plan/latest_artifact/latest_export` 为空边界，以及 `current_task=parse` 的成功/失败语义不串读。
- 顺手修复 `apps/api/tests/test_artifact_persistence.py` 中 `test_list_project_exports_honors_positive_limit` 被误缩进在另一个测试函数体内的问题，确保该正向参数回归会被 pytest 正常收集执行，而不是静默失效。
- 使用 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py -k "early_parse_states_isolated or honors_positive_limit" -q` 做 focused 验证，结果为 `2 passed`。
- 完成阶段 7.2 第二十三个项目看板中间规划态隔离切片：在 `apps/api/tests/test_artifact_persistence.py` 新增 `test_list_projects_dashboard_keeps_briefing_outlined_and_planned_states_isolated`，构造 `briefing`、`outlined`、`planned` 三个仍处于规划链路中的项目并检查 `GET /projects` 聚合结果。
- 该回归锁定 dashboard 在多项目中间规划场景下必须正确推进 `latest_brief/latest_outline/latest_slide_plan`，同时保持 `latest_artifact/latest_export` 为空，并让 `current_task` 分别对齐到 `generate_brief`、`generate_outline`、`generate_slide_plan`。
- 使用 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py -k "briefing_outlined_and_planned_states_isolated" -q` 做 focused 验证，结果为 `1 passed`。
- 完成阶段 7.2 第二十四个项目状态初始创建态切片：在 `apps/api/tests/test_artifact_persistence.py` 新增 `test_project_status_keeps_created_tail_aligned_before_any_file_registration`，覆盖项目刚创建且尚未登记文件时 detail/status/export-history 三个 read model 的一致性边界。
- 该回归锁定 `created` 初始态下 `latest_source_bundle/latest_brief/latest_outline/latest_slide_plan/latest_artifact/latest_export` 全空，且 `current_task` 与 `recent_tasks[-1]` 继续共同指向 ingest 成功任务，避免后续状态聚合调整让初始态错误长出解析或生成链路痕迹。
- 使用 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py -k "created_tail_aligned_before_any_file_registration" -q` 做 focused 验证，结果为 `1 passed`。
- 完成阶段 7.2 第二十五个项目看板初始创建态切片：在 `apps/api/tests/test_artifact_persistence.py` 新增 `test_list_projects_dashboard_keeps_single_created_project_empty`，覆盖 dashboard 仅返回一个 newly-created 项目时的最小列表边界。
- 该回归锁定 `GET /projects` 在 created 单项目场景下必须保持 `file_count/parsed_file_count/failed_file_count=0`、所有 `latest_*` 为空，并让 `current_task` 明确继续指向 ingest 成功任务，避免后续列表聚合把初始态误推进到 parse 或规划阶段。
- 使用 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py -k "single_created_project_empty" -q` 做 focused 验证，结果为 `1 passed`。

## 2026-03-23

- 初始化规划文件。
- 基于前序对三套方案的分析，开始编写实施方案文档。
- 文档将覆盖目标、架构分层、核心流程、项目结构、阶段性实施路线。
- 读取用户更新后的实施方案版本。
- 开始补写更细的“分阶段实施计划”，目标是让后续开发可以直接按文档推进。
- 按实施计划正式开始阶段 0 编码，创建 apps、packages、docs、storage、scripts、infra 目录骨架。
- 新增 FastAPI 空服务骨架，提供 app.main 与 /health 路由。
- 新增 Web 静态启动页与本地 Python 静态服务器，用于阶段 0 的最小页面验证。
- 新增 docs/architecture/tech-stack.md 与 docs/architecture/conventions.md，固化技术栈与工程规范。
- 新增 .env.example、.env、docker-compose.yml，建立本地基础环境基线。
- 验证过程中发现当前可用 Python 环境为 3.6.2，低于项目要求的 3.11+，因此依赖安装与 API 启动验证尚未完成。
- 使用 uv 重建 `.venv`，解释器切换到 Python 3.11.9，并安装 FastAPI、Pydantic、Uvicorn 等项目依赖。
- 更新 `.vscode/settings.json`，将工作区默认解释器指向 `.venv\\Scripts\\python.exe`。
- 通过短时启动验证 API 与 Web：`GET /health` 返回 200，Web 首页返回 200，阶段 0 运行验证完成。
- 当前 PowerShell 环境未识别 `docker` 命令，容器级验证暂未执行；该限制已记录，不影响阶段 0 的本地服务验收。
- 新增 `docs/architecture/data-models.md`，定义 10 个核心业务对象、内嵌对象、状态机与数据库映射建议。
- 新增 `docs/architecture/project-state-machine.md` 与 `docs/architecture/api-contracts.md`，固化阶段 1 的状态流转与 API 契约基线。
- 在 `packages/core-types` 中落地核心枚举、公共基类以及 Project、ProjectFile、SourceBundle、PresentationBrief、Outline、SlidePlan、SlideArtifact、ExportJob、TemplateMeta、TaskRun 模型。
- 通过 Python 3.11 虚拟环境实际导入和实例化核心类型，确认类型包可用。
- 新增 `docs/architecture/database-schema.md`，补齐阶段 1 所需 10 张核心表的字段、关系和索引建议。
- 在 `apps/api` 中新增项目 API 骨架：项目创建、项目查询、项目状态查询的请求响应模型、仓储、服务和路由接线完成。
- 补充 `.vscode/settings.json` 和 `pyproject.toml` 的 monorepo 源码路径配置，解决 `app` 与 `core_types` 的工作区导入解析问题。
- 通过本地短时启动完成项目接口验证，确认 `POST /projects`、`GET /projects/{id}`、`GET /projects/{id}/status` 可正常返回。
- 在 `apps/api/src/app/db` 中新增 SQLAlchemy 基类、会话工厂、表初始化逻辑以及 `projects`、`task_runs` 两张 ORM 表定义。
- 将项目仓储从内存实现推进到 SQLAlchemy 持久化实现，并在应用启动时加入自动建表入口。
- 新增 `sqlalchemy` 与 `psycopg[binary]` 依赖，使用 SQLite 作为本地无 Docker 验证后端完成 ORM 持久化自测。
- 持久化验证通过：本地 SQLite 下已成功完成项目创建、读取和状态查询全链路。
- 扩展 `project_files` ORM 定义、文件登记请求响应模型，以及项目仓储 / 服务层的文件元数据持久化方法。
- 在项目路由中新增 `POST /projects/{id}/files` 与 `GET /projects/{id}/files`，形成阶段 1 的最小文件登记链路。
- 使用 SQLite 完成项目创建、文件登记、文件列表查询的端到端自测，确认 `project_files` 持久化可用。
- 扩展 `source_bundles` 与 `presentation_briefs` ORM 定义，并为项目仓储补齐 SourceBundle / Brief 持久化与项目最新关联字段更新能力。
- 在项目服务与路由中新增 `POST /projects/{id}/brief:generate`，基于已登记文件元数据生成最小可用 `SourceBundle` 与 `PresentationBrief`。
- 为 FastAPI `TestClient` 本地验证补充 `httpx` 依赖，并修复 `GET /projects/{id}/status` 中对字符串状态误用 `.value` 的问题。
- 使用 SQLite 完成项目创建、文件登记、brief 生成、状态查询的端到端自测，确认阶段 1 的最小内容理解骨架可用。
- 扩展 `outlines` ORM 定义、请求响应模型、仓储与服务逻辑，并新增 `POST /projects/{id}/outline:generate` 路由。
- 在项目关联更新逻辑中补齐 `latest_outline_id` 持久化，确保 outline 生成后项目详情可正确反映最新提纲。
- 使用 SQLite 完成项目创建、文件登记、brief 生成、outline 生成、状态查询的端到端自测，确认阶段 1 的提纲生成骨架可用。
- 扩展 `slide_plans` ORM 定义、请求响应模型、仓储与服务逻辑，并新增 `POST /projects/{id}/slide-plan:generate` 路由。
- 在项目关联更新逻辑中补齐 `latest_slide_plan_id` 持久化，确保 slide plan 生成后项目详情可正确反映最新页规划。
- 使用 SQLite 完成项目创建、文件登记、brief 生成、outline 生成、slide plan 生成、状态查询的端到端自测，确认阶段 1 的页规划生成骨架可用。
- 补齐 `slide_artifacts`、`templates`、`exports` ORM 定义，并为项目主链路表增加外键约束与模板唯一键，完善阶段 1 数据库完整性。
- 扩展项目仓储，新增 latest source bundle / slide plan / artifact / export 的查询能力，以及统一的 `TaskRun` 持久化入口。
- 将 `GET /projects/{id}` 调整为聚合详情响应，对齐 API 契约文档，返回 `latest_source_bundle`、`latest_brief`、`latest_outline`、`latest_slide_plan` 等对象。
- 修复仓储重构后遗漏的 `ProjectStatus` 导入，当前编辑器静态检查已恢复无错误。
- 尝试使用系统 Python 执行新的 SQLite 端到端脚本验证，但当前解释器未安装 FastAPI，运行验证未完成；该问题属于环境依赖缺失，不是本次代码改动的编译错误。
- 新建 `packages/ingestion` 最小包，补充 `ParsedDocument` 数据模型和 `IngestionParser`，当前支持 Markdown/TXT 文件解析。
- 扩展项目服务与路由，新增 `POST /projects/{id}/files:parse`，可基于已登记文件解析正文、构造 `SourceChunk`，并回写最小 `SourceBundle`。
- 扩展仓储层 `project_files` 更新能力，使文件记录可从 `pending` 进入 `succeeded/failed` 解析状态并回写解析摘要与警告信息。
- 更新 `.vscode/settings.json` 和 `pyproject.toml`，将 `packages/ingestion/src` 纳入工作区 Python 源码路径与打包发现路径。
- 新增 `POST /projects/{id}/files:upload`，支持以 base64 载荷上传文件、落盘到 `storage/uploads/{project_id}/`，并自动登记 `ProjectFile`。
- 新增 `FileStorageService` 与 `DocumentNormalizer`，使阶段 2 具备最小文件落盘和文本归一化能力。
- 同步更新 `分阶段实施计划.md`，标记任务 2.1 的五个步骤已完成。
- 引入 `pypdf` 并扩展 `IngestionParser`，支持 PDF 文本抽取、按页切分、解析结果写回以及无法解析页的 warning 标记。
- 同步更新 `分阶段实施计划.md`，标记任务 2.2 的四个步骤已完成。
- 引入 `python-docx` 并扩展 `IngestionParser`，支持 DOCX 标题层级、列表结构、图片引用和 Markdown 输出的最小解析路径。
- 同步更新 `分阶段实施计划.md`，标记任务 2.3 的四个步骤已完成。
- 扩展 `IngestionParser` 支持 URL 输入，当前通过 `httpx` 抓取页面并提取正文文本，转为最小 Markdown 进入标准化流程。
- 同步更新 `分阶段实施计划.md`，标记任务 2.4 的两个目标已完成。
- 扩展 `DocumentNormalizer`，补齐噪声去除、多文档去重、标题层级修正、图片/表格块标记与最终 `normalized_markdown` 输出。
- `SourceBundle.metadata` 现额外记录被去重与移除的内容，便于后续审查解析效果。
- 同步更新 `分阶段实施计划.md`，标记任务 2.5 的五个处理项已完成。
- 补齐 `SourceBundle` 三模式生成规则：仅聊天输入时保留 `user_intent`，仅文件输入时聚焦 `sources/normalized_markdown`，混合模式时两者同时保留。
- `POST /projects/{id}/files:parse` 现支持携带 `user_intent` 一起重建 bundle，使解析链路能覆盖 file-only 与 mixed 两种场景。
- 同步更新 `分阶段实施计划.md`，标记任务 2.6 的三条规则已完成。
- 新建 `packages/methodology-engine` 首版包，落地 `RequirementClarifier` 与 `BriefGenerator`，作为阶段 3 的第一版方法论引擎入口。
- `POST /projects/{id}/brief:generate` 已改为优先复用最新 `SourceBundle`，并通过 methodology engine 生成更结构化的 `PresentationBrief`。
- 新增 `OutlineGenerator` 并接入 `POST /projects/{id}/outline:generate`，将原本内联在 `ProjectService` 的提纲章节生成逻辑迁移到 methodology engine。
- Outline 现按“先主线、再章节、每章有作用与结论、避免机械搬运目录”的规则输出首版章节骨架，并在元数据中记录生成原则。
- 新增 `SlidePlanner` 并接入 `POST /projects/{id}/slide-plan:generate`，将页规划逻辑从 `ProjectService` 迁移到 methodology engine。
- SlidePlan 首版已写入“单页一个主结论、限制内容块数量、控制信息密度、布局匹配内容类型”四条核心规则，并覆盖 `cover`、`toc`、`section`、`hero`、`two_column`、`bento`、`chart_focus`、`timeline`、`ending` 九种最低布局模式。
- 新增 `PATCH /projects/{id}/brief`、`PATCH /projects/{id}/outline`、`PATCH /projects/{id}/slide-plan`，提供最小人工修订入口。
- 当前人工修订支持按对象整体更新 Brief、Outline、SlidePlan，并在 metadata 中标记 `last_edited_by=manual_review`，满足阶段 3.5 的非黑盒协作要求。
- 新增 artifact JSON 落盘能力，当前会在 Brief、Outline、SlidePlan 生成与人工修订后同步写入 `storage/projects/{project_id}/artifacts/brief.json|outline.json|slide-plan.json`。
- 新增 API 级 smoke test，覆盖项目创建、文件登记、brief/outline/slide-plan 生成以及三份 artifact JSON 文件存在性验证，用于闭环 7.5 的最小输出要求。
- 在 artifact smoke test 中发现 `ProjectService._resolve_source_mode()` 仍返回旧值 `file_upload/chat_input`；现已修正为 `file/chat`，与当前 `SourceMode` 枚举保持一致。
- 新增最小 `artifact:generate` 生成骨架：当前可基于 `SlidePlan` 创建 `SlideArtifact` 记录、占位渲染目录 `svg_output/svg_final`，并将 `slide-artifact.json` 落盘，为阶段 4 的 SVG 渲染接线提供稳定入口。
- 新增内置 `TemplateRegistryService` 与 `DesignSpecBuilder`，`artifact:generate` 现会自动解析模板、生成 `design-spec.json` 渲染上下文并把路径写入 artifact metadata，阶段 4 已具备最小模板/渲染衔接输入。
- 新增 `GET /projects/templates`，阶段 4 现可向前端暴露内置模板元数据列表，便于后续模板选择器接线。
- 新增首版 `SvgRenderer` 接线，`POST /projects/{id}/artifact:generate` 现会基于 `SlidePlan` 和模板实际生成逐页 SVG，并同步落盘到 `svg_output/` 与 `svg_final/`。
- artifact 渲染结果现会回写 `preview_image_paths`、`render_status`、`failed_slide_ids`、`render-log.json` 与 `generated_svg_files`，阶段 4 已从“仅目录占位”推进到“最小真实页面产出”。
- 验证阶段 4 渲染链路时确认当前仓库测试命令需使用 `uv run pytest`，直接执行 `uv pytest` 会因子命令不存在而失败；该问题属于命令用法，不是本轮代码缺陷。
- 新增最小 `SvgValidator`，当前会对生成后的 SVG 检查根节点、标准 `viewBox` 以及一组 ppt 不兼容禁用标签，并把逐文件校验结果写入 `render-log.json`。
- `slide-artifact.json` 现额外记录 `validation_summary`，阶段 4 已具备“生成后立即做基础合规校验”的闭环。
- 使用 `uv run pytest` 验证阶段 4.5 时，定位到 `pyproject.toml` 的 `setuptools.packages.find.where` 尚未纳入 `packages/ingestion/src` 与 `packages/methodology-engine/src`，导致测试环境报 `ModuleNotFoundError: ingestion`；现已修正为从根因补齐 monorepo 本地包发现路径。
- 继续排查 SVG 未落盘问题后确认根因在渲染阶段本身：5 页均进入 `failed_slide_ids`，而原 `render-log.json` 只有失败页 ID，无法直接定位异常。
- 修复 `SvgRenderer` 对 `layout_mode` 的字符串/枚举兼容问题，并将逐页渲染异常明细补充写入 `render-log.json`，便于直接判断单页渲染失败原因。
- 推进阶段 4.6，新增最小 `SvgFinalizer`：当前会对渲染结果统一去 BOM、裁剪首尾空白、补 XML 头与换行，再写入 `svg_final/`，使 `svg_final` 不再只是 `svg_output` 的重复拷贝。
- `render-log.json` 与 `slide-artifact.json` 现新增 `finalization_summary`，并在逐文件校验结果中记录 `finalizer_steps`，便于后续继续增强 finalize 规则。
- 推进模板资产外置化第一版：新增 `templates/builtin/*.json` 作为内置模板资产源，`TemplateRegistryService` 现从 JSON 资产加载模板清单，而不是继续在服务代码中硬编码。
- 新增模板列表 API 测试，验证 `/projects/templates` 会稳定返回外置化模板资产，降低后续前端模板选择器接线风险。
- 修正 `/projects/templates` 路由匹配顺序问题：静态模板路由已前移到 `/{project_id}` 动态路由之前，避免被 FastAPI 误判为项目详情路径而返回 `404`。
- 继续推进阶段 4 的 finalize / validate 深化：`SvgFinalizer` 现会统一资源路径分隔符、清理 `./` 前缀并在标准 `viewBox` 下补齐 `width=1280`、`height=720`，让最终 SVG 更接近导出和验收要求。
- `SvgValidator` 现额外检查缺失宽高、外部资源引用、部分不兼容属性关键字以及超长文本节点风险，向“禁用标签/属性、路径、文本越界”目标再推进一层。
- 更新 artifact 持久化回归测试，新增对 `finalization_summary.width_height_alignment_count`、最终 SVG 宽高属性以及逐文件 `ensure_canvas_dimensions` 步骤的断言。
- 修正增强版 `SvgValidator` 的误报逻辑：不再把 `xmlns` 命名空间和 `fill-opacity` 误判为非法外链或 opacity 风险，仅对真实 `href/xlink:href` 外链和 `<g opacity>` 场景报错，并新增针对性单测。
- 修正 API 配置/数据库会话的静态初始化问题：`Settings` 与 SQLAlchemy engine 改为按需获取，确保 pytest 在设置 `DATABASE_URL` 后能够稳定切换到临时 SQLite，而不会回退到默认 Postgres。
- 调整 artifact 回归测试对 `width_height_alignment_count` 的断言口径：当 renderer 已直接输出标准宽高时，finalizer 不必重复改写，测试改为验证最终 SVG 结果和 `ensure_canvas_dimensions` 步骤存在，而不强制计数大于 0。
- 继续推进阶段 4 模板资产扩充：新增 `technology-grid` 与 `government-blue` 两个内置模板 JSON，参考 LandPPT 的科技/商务风格命名与 ppt-master 的咨询/区域报告视觉语义，当前内置模板已从 2 个扩充到 4 个。
- 扩展 `/projects/templates` API 测试覆盖新增模板，校验模板元数据、设计规范路径和关键布局模式，确保模板资产外置化继续可回归验证。
- 推进模板自动选择策略第一步：`TemplateRegistryService.resolve_template()` 现会优先结合 `SlidePlan.design_direction` 与 metadata 中的 `scenario/style/domain/content_type` 提示匹配模板，再退回布局覆盖匹配，减少“所有布局都兼容时总落到同一个默认模板”的问题。
- 新增模板解析单测，验证技术类 `design_direction` 会优先命中 `technology-grid`，以及无场景提示时仍能按布局兼容性回退，确保自动选模版升级可稳定回归。
- 继续把模板选择信号向上游打通：`SlidePlanner` 现会基于 Brief 的 `tone`、`style_preferences`、目标受众和内容关键词生成结构化 `style_tags` / `scenario_tags` / `audience_tag`，并把 `design_direction` 从固定占位串升级为可参与模板推荐的组合信号。
- 新增 `packages/methodology-engine/tests/test_slide_planner.py`，验证技术类 Brief 会产出 `technology/product/architecture` 信号、显式模板选择会写回 `preferred_template_id`，为后续模板选择器和智能推荐提供稳定上游输入。
- 推进阶段 4 的资源存在性校验：`SvgValidator` 现会以最终 SVG 文件目录为基准检查相对 `href` / `xlink:href` 是否指向真实存在的本地资源，补上“不是外链但文件丢失”这一类此前无法识别的问题。
- 新增本地资源校验单测，分别覆盖“相对资源缺失时报错”和“相对资源存在时放行”，让后续图片/图表类模板接线前就具备最小资源完整性回归保护。
- 继续增强阶段 4 的文本越界校验：`SvgValidator` 不再只按文本长度粗判，而是结合 `<text>` 的 `x`、`font-size`、`text-anchor` 与可选 `data-max-width` 做最小几何估算，能识别右侧越界、居中文字溢出和窄栏卡片文案超宽三类问题。
- 新增文本越界单测，分别覆盖左对齐越界、居中越界、声明卡片宽度超限以及正常文本通过，阶段 4 的 SVG 合规校验现对“文本长度正常但布局仍溢出”的情况具备基础防线。
- 继续推进阶段 4 的文本排版质量：`SvgRenderer` 现为封面正文、hero 摘要、chart focus 标题、结束页大文案和卡片正文补上最小多行排版能力，在受限宽度内按行拆分文本，而不再一律退化为单行截断。
- 同步修正 `SvgValidator` 对多行 `<text>/<tspan>` 的识别方式，改为按行估算宽度并复用既有 `data-max-width` / `text-anchor` 规则，避免多行文本被误按单行总长度判定为越界；相关 artifact、validator、planner、template 回归已通过 `14 passed` 验证。
- 继续扩展阶段 4 的多行排版覆盖面：`SvgRenderer` 现已把目录项、timeline 节点标签和 hero 侧栏 bullet 文案从单行截断升级为最小两行排版，降低长议程、长里程碑和长要点在窄栏中的信息损失。
- 补充 `apps/api/tests/test_svg_renderer.py` 作为 renderer 直测回归，直接验证 bullets、TOC 与 timeline 多行 `<tspan>` 输出；连同 artifact、validator、planner、template 定向集已通过 `16 passed` 验证。
- 继续推进阶段 4 的纵向排版稳定性：`SvgRenderer` 的多行文本现除 `data-max-width` 外，还会为封面正文、目录项、hero 摘要、chart focus 标题、timeline 标签、结束页正文和卡片正文声明 `data-max-height`，并按可用高度自动收窄可渲染行数，避免“宽度没超但高度挤爆容器”。
- 同步增强 `SvgValidator` 的文本溢出检查，现会对带 `data-max-height` 的多行 `<text>/<tspan>` 做最小高度估算；renderer/validator 定向回归已扩展到 `18 passed`，新增覆盖高度裁剪与高度越界场景。
- 继续补齐阶段 4 的标题区约束：`SvgRenderer` 现已将页头标题、副标题、section 主标题和卡片标题统一接入高度感知多行文本渲染，避免长标题仍停留在单行截断或缺少纵向边界声明的状态。
- 同步放宽并统一 `SvgValidator` 的高度判断语义，只要声明了 `data-max-height` 就会执行高度估算，覆盖单行超高与多行累计超高两类场景；本轮 renderer / artifact / validator / planner / template 定向回归已通过 `20 passed` 验证。
- 继续补齐阶段 4 的固定文案区约束：页头 layout 标签与页脚 footer 现也改为复用 `_multiline_text()` 输出，并显式声明 `data-max-height`，避免顶部模式标签和底部页码模板名仍游离在统一越界保护之外。
- 清理 `SvgRenderer` 中已基本退役的单行 `_fit_text()` helper，并为 layout label / footer 增加 renderer 与 validator 直测；本轮定向回归已扩展到 `22 passed`。
- 继续推进阶段 4 模板资产扩充：新增 `templates/builtin/consulting-premium.json` 与 `templates/builtin/research-paper.json`，分别覆盖高端咨询和研究论文两类场景。
- 扩展 `apps/api/tests/test_template_registry.py`，模板列表接口断言现覆盖 6 套内置模板，并新增 academic/research、consulting/strategy 两类自动选模回归。
- 验证过程中确认当前 Windows 环境下直接执行 `uv run pytest ...` 可能命中外部 Anaconda `pytest`，导致错误地读取系统环境；现改为统一使用 `uv run python -m pytest ...` 通过项目 `.venv` 执行。
- 项目 `pyproject.toml` 已补充 `pytest` 依赖，随后执行 `uv sync` 并通过 `uv run python -m pytest apps/api/tests/test_template_registry.py`，结果为 `5 passed`。
- 继续推进阶段 4 的文本高度语义对齐：`SvgRenderer` 现会为所有 `_multiline_text()` 输出附加 `data-line-height`，`SvgValidator` 则优先按声明值估算多行文本高度，不再固定写死 `1.35`。
- 新增 renderer / validator 回归，分别覆盖 `data-line-height` 元数据输出、显式行高通过校验以及缺少元数据时仍按默认高度拦截越界三种场景；定向验证结果为 `18 passed`。
- 继续推进阶段 4 的旁路文本收口：`section` 布局左侧页码现已改为复用 `_multiline_text()` 渲染，补齐 `data-max-width="120"`、`data-max-height="64"`、`data-line-height="1.0"`，避免该固定编号区继续游离在统一宽高约束之外。
- 补充 `apps/api/tests/test_svg_renderer.py` 回归，直接断言 `section` 页码文本也带有完整边界元数据；连同 validator 定向集再次通过 `19 passed` 验证。
- 继续推进阶段 4 的块级容器保护：`SvgRenderer._bullet_group()` 现新增 `max_group_height` 预算，hero 与 chart focus 侧栏 bullet 在累计高度超过容器预算时会停止追加，避免每条 bullet 各自合法但整组仍把卡片底部挤穿。
- 新增 bullet 组回归，验证长 bullet 列表在 hero 侧栏中会按可用高度保留首条并截断后续项；连同 validator 定向集再次通过 `21 passed` 验证。
- 继续推进阶段 4 的目录区稳定性：`SvgRenderer._toc_blocks()` 现把目录项多行文本的 `data-max-height` / wrap 预算从 `52` 调整到 `58`，与 `font_size=24`、`line_height=1.2` 的两行渲染需求对齐，使 TOC 首项真实发生两行换行时，后续项会按 cursor 动态下移而不再与前项挤压。
- 补充并修正 TOC 回归：新增针对“首项两行换行后第二项纵向偏移”的直测，同时同步更新既有 TOC wrapping 断言到新的 `data-max-height="58"` 语义。
- 过程中通过独立 wrap 探针确认旧实现的根因并非测试样本不够长，而是 `max_height=52` 在当前行高下只能保留 1 行，导致 TOC 的两行支持与动态间距逻辑实际上永远触发不到；修复后重新执行 `uv run python -m pytest apps/api/tests/test_svg_renderer.py apps/api/tests/test_svg_validator.py`，结果为 `22 passed`。
- 继续推进阶段 4 的 timeline 标签稳定性：`SvgRenderer._timeline_blocks()` 现把节点标签多行文本的 `data-max-height` 从 `42` 调整到 `44`，与 `font_size=18`、`line_height=1.15` 的两行渲染需求对齐，避免第二行虽然理论存在但在高度裁剪后不可达。
- 补充 timeline 回归：更新既有 timeline wrapping 断言到 `data-max-height="44"`，并新增专门测试验证第二行 `<tspan x="180" dy="20.7">` 真实输出，确保两行支持不是名义能力。
- 完成 timeline 修复后的定向验证：执行 `uv run python -m pytest apps/api/tests/test_svg_renderer.py apps/api/tests/test_svg_validator.py`，结果为 `23 passed`。
- 继续推进阶段 4 的标题区验收闭环：本轮未新增生产代码修改，而是对 subtitle 与 card heading 增补“第二行真实可达”回归，分别直接断言 `<tspan x="80" dy="24.0">` 与 `<tspan x="104" dy="27.6">` 存在，避免后续只凭 `data-max-height` 参数表面值重复误判。
- 补做数值探针确认：当前 subtitle `max_height=48` 与 card heading `max_height=54` 在现有 `_wrap_text()` 公式下都真实允许两行，因此这两块当前属于“验收口径缺失”而非“预算参数错误”。
- 完成标题区回归补强后的定向验证：执行 `uv run python -m pytest apps/api/tests/test_svg_renderer.py apps/api/tests/test_svg_validator.py`，结果为 `25 passed`。
- 继续推进阶段 4 的 section/chart 文案区验收闭环：本轮同样未新增生产代码修改，而是先用 `_wrap_text()` 数值探针确认 `section title (max_height=108)` 与 `chart caption (max_height=88)` 在当前公式下都真实允许两行，再为它们补上直接断言第二行 `tspan` 可达的 renderer 回归。
- 新增 `section` 页右侧主标题与 `chart_focus` 说明文案的真实可达断言，分别锁定 `<tspan x="650" dy="39.1">` 与 `<tspan x="110" dy="32.4">`，把这两个容器也纳入“第二行不仅声明支持，而且 SVG 实际输出已验证”的收尾范围。
- 完成 section/chart caption 回归补强后的定向验证：执行 `uv run python -m pytest apps/api/tests/test_svg_renderer.py apps/api/tests/test_svg_validator.py`，结果为 `27 passed`。
- 继续推进阶段 4 的正文区验收闭环：本轮仍未修改生产代码，而是先用 `_wrap_text()` 数值探针确认 `hero summary (max_height=120)` 真实允许 3 行、`card body (max_height=150)` 真实允许 4 行，再基于真实 SVG 输出补上正文区多行可达回归。
- 新增 `hero` 右侧摘要区与两栏卡片正文区的真实可达断言，分别锁定 `<tspan x="800" dy="32.4">` 的第三行可达性，以及 `<tspan x="104" dy="24.3">` 的第四行可达性，把正文区也并入“关键多行真实可达已验证”的阶段 4 收尾范围。
- 完成 hero summary / card body 回归补强后的定向验证：执行 `uv run python -m pytest apps/api/tests/test_svg_renderer.py apps/api/tests/test_svg_validator.py`，结果为 `29 passed`。
- 继续推进阶段 4 的正文区验收闭环：本轮先用 `_wrap_text()` 数值探针与真实 SVG 输出确认 `cover body (max_height=130)` 当前确实可稳定到第 4 行，于是补上直接断言 `<tspan x="80" dy="29.7">` 第四行可达的 renderer 回归，把封面正文区也纳入“多行真实可达”保护。
- 同轮对 `ending body` 追加更长样本探针与真实 SVG 检查后，确认在当前 `text-anchor="middle"`、宽度与字号组合下仍只稳定产出 2 行；因此本次不写缺乏证据的第三行回归，避免把错误预期固化进测试。
- 随后补上 `ending body` 的真实验收口径：基于实际 SVG 输出新增第二行可达回归，直接锁定 `<text x="640" y="380">`、`data-max-height="150"` 与 `<tspan x="640" dy="59.4">`，明确当前结束页正文只对“第二行真实可达”背书。
- 重新执行 `uv run python -m pytest apps/api/tests/test_svg_renderer.py apps/api/tests/test_svg_validator.py`，定向验证结果更新为 `31 passed in 1.93s`，说明新增 cover/ending 两个 renderer 回归后当前 Phase 4 focused 基线稳定。
- 继续做阶段 4 收口判定：回看 renderer 直测覆盖后确认 section number 已有 `data-max-width="120"` / `data-max-height="64"` / `data-line-height="1.0"` 直测，footer 则经实际输出探针确认属于 `max_lines=1` 的单行截断设计，因此不再把这两类容器当作新的多行验收缺口。
- 基于当前回归面和最近一轮 focused baseline，阶段 4 判断已从“继续补高风险多行容器”切换到“阶段边界 review 与出口确认”：核心能力完成度约 90%~92%，稳定性与验收收口完成度约 86%~88%。
- 本轮未新增生产代码或测试代码修改，主要完成了阶段边界梳理与状态修正，避免继续堆叠低收益单行容器测试。
- 完成阶段 4 exit review 第一轮：对照 `分阶段实施计划.md` 的阶段 4 条目回看模板列表/自动选模、SVG 产出、validator/finalizer、文本约束回归后，当前未发现新的高优先级功能阻塞，说明阶段 4 已基本具备转入下一阶段的条件。
- 本轮 review 结论同时保留残余风险说明：现阶段主要剩余的是跨模板视觉一致性、真实导出链路联调以及少量低风险固定文案区的抽样复核，而不是渲染内核主能力缺失。
- 因此下一推荐切片从阶段 4 内部收口切换为阶段 5 起步，优先进入导出链路与结果管理的最小可验证实现。
- 进入阶段 5 的第一段最小实现：新增 `POST /projects/{id}/export`，当前基于 `latest_artifact` 或显式 `artifact_id` 执行导出前置校验，只允许从 `svg_final/` 导出，并在缺少 finalized SVG 或 render/finalize 状态不满足时直接返回 400。
- 扩展 `SqlAlchemyProjectRepository` 与 `FileStorageService`，补齐 `ExportJob` 创建落库能力和 `storage/projects/{project_id}/exports/{artifact_id}/` 导出文件写入能力；项目详情聚合中的 `latest_export` 现可返回新写入的导出记录。
- 当前先以最小占位 manifest 形式写出 `.pptx` 文件，内容记录 artifact、源 `svg_final/` 目录和参与导出的 SVG 文件列表，用于先闭环“结果可落盘、可追溯、可通过 API 查询”的 Phase 5 骨架。
- 新增 `apps/api/tests/test_artifact_persistence.py::test_export_writes_project_export_artifact`，覆盖项目创建、brief/outline/slide-plan/artifact 生成、export 调用、导出文件存在性、任务状态、项目 `latest_export` 聚合回填等完整链路。
- 执行 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py`，结果为 `2 passed in 4.31s`；说明当前最小导出 API、导出记录持久化和项目详情回填链路可用。
- 继续推进阶段 5 的结果可追踪性：`ProjectService.generate_export()` 现改为在失败路径也先创建 `ExportJob` 并统一走 `_fail_export()`，当 artifact 缺失、`svg_final/` 缺失或 finalize 未完成时，会把导出记录持久化为 `failed`，同步写入失败 `TaskRun`，并把项目状态推进到 `export_failed`，避免导出失败只返回 400 却没有审计痕迹。
- 补充 `apps/api/tests/test_artifact_persistence.py::test_export_failure_is_persisted_for_traceability`，覆盖“导出请求命中缺失 artifact”时的 400 响应、项目状态变更以及失败任务可见性，验证 Phase 5 关于失败结果可定位的最小要求。
- 修复导出服务中 `export_format` 在当前 CoreModel 语义下表现为字符串而非枚举对象的问题，统一改为按字符串值写入成功/失败任务结果，避免失败路径再次触发 `.value` 属性错误。
- 重新执行 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py`，结果为 `3 passed in 4.72s`；说明导出成功与失败两条持久化路径均已稳定可回归。
- 继续推进阶段 5 的真实交付文件能力：新增 `PptxExportService`，当前采用 `cairosvg` 将 `svg_final/slide-*.svg` 逐页转为 PNG，再通过 `python-pptx` 写入 16:9 演示文稿，使 `POST /projects/{id}/export` 成功路径产出真正可打开的 `.pptx`，不再是文本 manifest 占位文件。
- 继续推进阶段 5 的预览交付能力：复用既有 `POST /projects/{id}/export` 骨架，新增 `PdfExportService`，当前采用 `cairosvg` 将 `svg_final/slide-*.svg` 逐页转为单页 PDF，再用 `pypdf` 合并为最终预览文件；服务层按 `export_format` 分支输出 `pptx` 或 `pdf`，并在 PDF 路径上同步写入 `preview_pdf_path`，避免额外新增接口或旁路结果记录。
- 补充 `apps/api/tests/test_artifact_persistence.py::test_pdf_preview_export_writes_preview_path`，覆盖 PDF 预览导出成功后的落盘文件、页数、`preview_pdf_path` 持久化与 `latest_export` 聚合回填，保持阶段 5 的结果管理闭环在 PPTX 与 PDF 两条成功路径上都可验证。
- 扩展 `FileStorageService` 的导出路径构建能力，并在 `ProjectService.generate_export()` 中把成功导出元数据更新为 `export_kind=pptx_from_svg_pages`、`renderer=cairosvg+python-pptx` 与逐页文件列表，保留现有 `svg_final` 前置校验与失败持久化逻辑不变。
- 更新 `apps/api/tests/test_artifact_persistence.py::test_export_writes_project_export_artifact`，改为使用 `python-pptx` 打开导出的 `.pptx` 并验证 slide 数量与记录的导出元数据一致，避免继续只靠文本内容判断“导出成功”。
- 执行 `uv sync` 安装 `python-pptx` 与 `cairosvg` 等导出依赖后，重新运行 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py`，结果为 `3 passed in 9.58s`；说明真实 PPTX 导出与失败追踪路径在当前环境均已可回归。
- 复核阶段 5 当前实现面后确认 `ProjectService.generate_export()`、`PdfExportService`、仓储层 `preview_pdf_path` 持久化以及 API 级 PDF 回归测试已全部接通，前一轮“下一步需要补 PDF 分支”的判断已经过时。
- 重新执行 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py -vv`，结果为 `4 passed in 4.88s`；说明 artifact 快照、真实 PPTX 导出、失败持久化与 PDF 预览导出四条链路在当前环境均稳定可回归。
- 继续推进阶段 5 的结果管理：`FileStorageService` 新增导出上下文写入能力，`ProjectService.generate_export()` 成功路径现会在 `storage/projects/{project_id}/exports/{artifact_id}/` 下同步写入 `archive-manifest.json` 与 `export-log.json`，把导出文件、源 `svg_final` 页列表、关键归档元数据和成功日志固定下来。
- 扩展 `apps/api/tests/test_artifact_persistence.py`，新增对 `archive-manifest.json` / `export-log.json` 存在性与关键字段的断言，确保 PPTX 与 PDF 两条成功路径都具备最小结果归档保护。
- 重新执行 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py -vv`，结果为 `4 passed in 5.48s`；说明当前导出链路已同时覆盖 artifact 快照、真实 PPTX、失败持久化、PDF 预览与最小结果归档五类行为。
- 继续推进阶段 5 的版本记录：`ExportJob`、`ExportRecord` 与导出服务现已引入首版 `run_id`，每次导出都会生成唯一版本号，并将导出目录从 `storage/projects/{project_id}/exports/{artifact_id}/` 升级为 `storage/projects/{project_id}/exports/{artifact_id}/{run_id}/`，避免同一 artifact 的重复导出互相覆盖。
- `archive-manifest.json`、`export-log.json`、`latest_export`、导出任务结果与失败结果当前都会回填 `run_id`，因此 API、归档文件和持久化记录已经共享同一版本标识。
- 扩展 `apps/api/tests/test_artifact_persistence.py`，新增 `run_id` 断言与 `test_repeated_exports_create_distinct_run_ids_and_paths`，专门验证重复导出会生成不同版本号和不同落盘路径。
- 重新执行 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py -vv`，结果为 `5 passed in 6.08s`；说明当前导出链路已同时覆盖 artifact 快照、真实 PPTX、失败持久化、PDF 预览、最小结果归档与版本记录六类行为。
- 进入阶段 6.1 的第一段最小实现：后端新增 `GET /projects` 项目看板聚合接口，返回项目基本信息、状态、文件解析统计、最新 brief / outline / slide plan、最新 artifact / export 与当前任务，避免前端必须逐项目多次拉取明细才能拼出看板。
- 将 `apps/web/index.html` 从 Phase 0 占位页替换为无构建依赖的静态看板应用，当前可配置 API Base、手动刷新，并以项目卡片形式展示输入、规划、输出三栏摘要和顶部总览指标。
- 当前看板已满足阶段 6.1 “展示项目基本信息、当前状态、最新输入材料、最新 Brief / Outline / SlidePlan、渲染和导出结果”的最小目标；尚未实现筛选、审阅操作、局部重生成入口和模板选择器，这些保留给阶段 6 后续子任务。
- 补充 `apps/api/tests/test_artifact_persistence.py::test_list_projects_dashboard_returns_aggregated_project_summary`，通过 API 级用例验证 `GET /projects` 会聚合返回项目状态、文件统计、最新 brief / outline / slide plan、latest artifact / export 与当前任务。
- 执行 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py -q`，本轮 focused 验证结果为 `6 passed`；另行执行 `uv run python -c "from app.main import create_app; ..."`，确认 FastAPI 应用可正常实例化，当前路由数为 22。
- 继续推进阶段 6.1 的前端最小交互：看板工具栏新增状态筛选与关键字检索，当前可基于项目状态、名称、标签、描述、brief 目标、受众与 outline 标题做客户端过滤。
- 新增基于 `#project-{id}` 的项目深链定位能力：项目标题和输出区“查看项目详情锚点”会更新 URL hash，页面在命中 hash 时自动滚动并高亮对应项目卡片。
- 对 `apps/web/index.html` 与 `apps/web/src/styles.css` 执行编辑器诊断，结果均为 `No errors found`；本轮未新增 API 改动或后端测试需求。
- 进入阶段 6.2 的第一段最小实现：静态看板现扩展为双栏审阅工作区，左侧继续展示项目卡片列表，右侧新增基于 `GET /projects/{id}` 的 detail review 面板，可加载 latest brief / outline / slide plan / artifact / export 摘要。
- 审阅工作区当前已接入 `PATCH /projects/{id}/brief`、`PATCH /projects/{id}/outline` 与 `PATCH /projects/{id}/slide-plan`，支持对 Brief、Outline、SlidePlan 做最小人工修订，并在保存后自动刷新项目看板与当前项目详情。
- 渲染结果区当前先以 artifact/export 摘要形式呈现 `render_status`、template、preview PDF 路径、SVG 文件计数以及 validation/finalization 信息，作为 SVG 预览审阅前的过渡切片。
- 对更新后的 `apps/web/index.html` 与 `apps/web/src/styles.css` 再次执行编辑器诊断，结果仍为 `No errors found`；本轮未新增后端代码，因此未追加 API 测试。
- 进入阶段 6.3 的第一段最小实现：审阅工作区新增模板覆盖选择器，并接通 `GET /projects/templates` 模板列表加载；当前可在同页直接选择模板后触发“按模板重生成 Slide Plan”与“按模板整体重渲染”。
- 前端分别复用既有 `POST /projects/{id}/slide-plan:generate` 和 `POST /projects/{id}/artifact:generate`，以 `preferred_template_id`、`template_id` 和 `force_regenerate` 驱动模板覆盖重生成，无需新增后端契约即可完成首个 6.3 切片。
- 新增 `apps/api/tests/test_artifact_persistence.py::test_template_override_can_regenerate_slide_plan_and_artifact`，验证模板覆盖会回写到 latest slide plan / artifact 元数据；随后执行 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py -q`，结果为 `7 passed in 6.37s`。
- 按 `实施方案.md` 的推荐前端结构继续收口阶段 6.3：将原本集中在 `apps/web/index.html` 内的大段页面脚本拆分到 `apps/web/src/pages/dashboard/main.js`、`apps/web/src/features/project/{dashboard,review,state}.js` 与 `apps/web/src/lib/{api,formatters}.js`，把页面入口、项目域逻辑与公共工具分层固定下来。
- 当前 `apps/web/index.html` 已退化为页面骨架 + `type="module"` 入口，不再继续承载看板、审阅、模板重生成的全部脚本细节；现有 6.1/6.2/6.3 行为保持不变。
- 对 `apps/web/index.html` 及新增前端模块执行编辑器诊断，结果均为 `No errors found`；本轮主要是结构重构，暂未追加新的后端测试。
- 进入阶段 6.4 的第一段最小实现：审阅工作区新增 Export 区域，前端在不新增后端接口的前提下复用既有 `POST /projects/{id}/export`，补齐导出格式选择、artifact 来源覆盖与“生成导出文件”触发入口。
- `apps/web/src/lib/api.js` 已新增 `triggerExport()`，`apps/web/src/features/project/review.js` 已新增导出 payload 构建与表单状态管理，`apps/web/src/pages/dashboard/main.js` 已接通导出事件监听、状态提示与导出后详情回刷；当前可从同一审阅面直接触发 `pptx` 和 `pdf` 两类导出。
- 对新增导出工作区相关前端文件执行编辑器诊断，`apps/web/index.html`、`apps/web/src/lib/api.js`、`apps/web/src/features/project/review.js`、`apps/web/src/pages/dashboard/main.js` 与 `apps/web/src/styles.css` 结果均为 `No errors found`；本轮未新增后端代码，因此暂未追加 API 测试。
