# Findings

- 当前仓库要从“能跑”变成“真可用”，关键缺口不是页面好不好看，而是必须同时具备模型配置入口、连通性验证和真实调用路径。只有规则式 brief/outline/slide-plan 占位链路、却没有 provider/base_url/api_key/model 配置面，就不能算 AI PPT 产品可用。
- 对这轮缺口，最稳妥的最小实现不是先引入全局系统设置或新数据库表，而是先把 LLM 设置收敛到项目级上下文里，并暂存到 `Project.metadata`。这样可以在不阻塞交付的前提下，让“当前项目用哪个模型生成”立即具备真实可操作性；后续再决定是否上升为独立配置表或组织级密钥体系。
- 把 LLM 接入点放在 `ProjectService.generate_brief()`、`generate_outline()`、`generate_slide_plan()` 三段核心链路上，比单独做一个“测试接口”更关键。原因是用户真正关心的是生成结果是否能走模型，而不是页面上有没有一个能测通的按钮；测试按钮只能证明连通，不能证明产品主链已打通。
- 对当前仓库，LLM 接线后仍应保留 methodology engine 规则链路作为回退，而不是把模型调用失败直接变成整条生成链不可用。项目级“启用则优先走 LLM，失败则回退规则链”是更符合现阶段产品成熟度的选择，因为它同时满足真实生成能力和最小稳态可用性。
- `packages/llm-gateway` 作为 monorepo 复用方向是合理的，但在当前工作区/Pylance 解析边界下，运行中优先落到 `apps/api/src/app/services/llm_gateway.py` 更稳；这说明现阶段最重要的是先让产品能力接通，再在后续收口时做包级去重，而不是为了形式上的“包复用”牺牲交付稳定性。

- 当用户明确要求前端更像 LandPPT 且不能继续堆在一个页面时，当前仓库最稳妥的落地路径不是临时引入前端框架，而是继续沿用静态 HTML + 原生 ES module，把产品入口、项目列表和单项目工作区拆成多页面壳层。这样既能快速改变产品观感和信息架构，又不会打断现有 `features/project` 模块和真实 API 绑定。
- 这轮多页面拆分里，真正和单页路由强耦合的主要是项目跳转语义，而不是 review/intake 本身。重新核对后可以确认 `review.js` 的核心依赖仍是 DOM 契约；只要 `workspace.html` 和 `workspace/main.js` 继续提供同一组节点与映射，模板筛选、产物摘要和导出历史都可以原样复用，不需要为了多页面化去重写 feature 层。

- 当前项目的主要偏差不在架构层，而在产品叙事层：实施方案、任务计划和代码结构已经基本对齐“AI PPT 生成网站”，真正明显跑偏的是仓库首页与部分文档仍沿用“毕业论文初稿自动生成平台”的旧身份。
- 对这个仓库，最需要优先纠正的不是再加一层新能力，而是先把产品定位统一为“通用 AI PPT 生成平台”，再把“论文答辩”降级为场景标签，否则 README 和阶段计划会持续把实现牵回单一学术工具方向。
- 本轮继续往下看，真正需要优先纠偏的用户触点不仅是顶层 README，还包括 `pyproject.toml` 的包描述、`apps/web/index.html` 的 title/hero、Web 工作台运行态文案，以及 `分阶段实施计划.md` 里残留的样例/模板命名。只改架构文档不改这些首屏触点，产品感知仍会继续漂向 thesis/dashboard。
- 阶段计划里最关键的收口不是再加一条抽象愿景，而是明确阶段 6 的 Web 端默认目标：把它收敛成 AI PPT 网站的主入口，支持创建项目、上传或对话发起、审阅、模板切换、重生成和导出，而不是停留在“开发阶段看板”的叙事上。
- 对“继续完成 1/2/3”这一轮来说，最稳妥的边界不是做仓库级大重命名，而是只修正当前真实用户可见和运行时可见的身份字段，例如首页文案、API `app_name`、默认数据库名、核心包说明和计划文档中的仓库示意名称。这样可以继续压缩 thesis 气味，又不会引入导入路径、包名或发布元数据级别的连锁风险。
- 残留搜索结果需要分层判断：如果命中的是 `progress.md`、`findings.md` 里的“过去曾经存在的偏差”记录，或测试样例中的历史用词，它们表达的是项目演化事实，而不是当前产品身份。继续把这些历史记录全部洗掉，反而会损失审计价值。
- 当用户要求“先完成 1”时，最合理的完成标准应限定在活跃身份字段，而不是把仓库目录名、`.egg-info` 产物、技能文件说明和历史记录也一起重命名。前者是产品面收口，后者则会跨到构建产物、工具元数据和审计信息，风险与收益明显不对称。
- 步骤 2 的关键不只是把文案写得更“产品化”，而是把 `apps/web` 首屏层级从“开发控制台 + 工作台说明”改成明显的产品 front door：先讲清输入入口、生产闭环和实时工作区，再把 intake 与 review/workspace 作为同一站点里的两个连续区域展示。这样可以在不改动现有 JS 绑定的前提下，显著降低页面的内部工具感。
- 步骤 2 的第二轮应该继续停留在 HTML/CSS 语义层，而不是提前改 `dashboard.js` / `review.js`。当前 JS 模块对 DOM 结构依赖较重，更稳妥的路径是先用组合板说明、review 空态引导、review 顶部 band 和 project card 模板节奏把 workspace 区做成产品工作面，再决定是否需要触碰交互逻辑。

- 当前 `apps/web` 继续保持静态页 + 原生 ES module 交付模式时，最稳妥的“前后端打通”路径不是先引入框架，而是补齐浏览器直连 API 所需的 CORS、把 intake 流程拆成独立 feature，并让页面入口只做编排。这样既能保持现有 `pages/features/lib` 分层，也能避免继续把创建/上传/解析/生成逻辑堆回单一入口脚本。
- 对当前最小可用链路，前端真正缺的不是 review/export，而是更靠前的 intake 主链：`POST /projects`、`POST /projects/{id}/files:upload`、`POST /projects/{id}/files:parse`、`POST /projects/{id}/brief:generate`、`POST /projects/{id}/outline:generate` 一旦接入，同页就能形成“先 intake、再审阅”的可用闭环。
- `uv run python -m pytest apps/api/tests` 在当前仓库里返回 `collecting 0 items`，说明虽然存在 `apps/api/tests/` 目录，但当前入口下没有可被 pytest 直接收集的测试模块或命名不匹配。后续若要把“前后端已打通”从人工联调推进到自动化回归，需要先修正测试收集入口，而不是误把这次命令当成通过的 green build。
- 当前 pytest 环境并非不可用：使用明确文件入口执行 `uv run python -m pytest apps/api/tests/test_artifact_persistence.py -k "project_detail_keeps or project_status_keeps or list_projects_dashboard" -q` 时，focused 回归已能正常收集并开始通过。因此问题更准确地说是“目录级入口未命中收集规则”，而不是“仓库里完全跑不起来 pytest”。后续若补 intake 自动化，应直接挂到现有可收集的测试文件或先修正目录级收集约定。

- `GET /projects` 的 dashboard 聚合不仅要锁导出态和规划态，还需要单独锁最早解析阶段的多项目隔离；否则一旦列表层错误复用 detail/task 聚合，`parsed/analyzed/parse_failed` 这些“latest\_\*` 应全空”的卡片很容易被别的项目 source bundle 或失败结果污染。
- `apps/api/tests/test_artifact_persistence.py` 曾存在一个隐蔽测试收集缺口：`test_list_project_exports_honors_positive_limit` 被误缩进在另一个测试函数体内，编辑器不会报语法错，但 pytest 也不会把它当顶层用例收集。对长集成测试文件，阶段 7.2 后续继续加回归时要顺手警惕这类“逻辑存在、实际未执行”的结构性失真。
- `GET /projects` 的 dashboard 聚合在中间规划态也需要单独锁边界：`briefing`、`outlined`、`planned` 三类项目虽然都已有部分 `latest_*` 数据，但它们不应提前长出 `latest_artifact` 或 `latest_export`。如果不单独做列表级回归，后续有人复用后阶段聚合结果时，很容易让仍处于规划阶段的卡片看起来像已经开始渲染或导出。
- `GET /projects/{id}` 的 detail 聚合也要和 `status` 分开锁边界，不能因为已经有 `current_task/recent_tasks[-1]` 的 `outlined` 回归，就假设详情层一定安全。仓储当前会按 `latest_*_id` 逐层回填对象；如果不单独断言 detail 在 `outlined` 阶段仍保持 `latest_slide_plan/latest_artifact/latest_export` 全空，后续聚合调整很容易把提纲阶段错误推进到页规划或更后面的对象。
- `GET /projects/{id}` 的 `briefing` detail 边界也需要单独锁，而不能只依赖 `status` 的早期规划态回归。因为仓储会在 detail 层独立回填 `latest_brief/latest_outline/latest_slide_plan`，一旦后续有人调整 latest 解析顺序，最先被误推进的通常就是 “brief 已有就顺手长出 outline” 这一层。
- `GET /projects/{id}` 的 detail-only 边界不能只补规划中段。`parsed`、`analyzed`、`parse_failed`、`finalized`、`export_failed` 这些状态同样依赖仓储层各自不同的 latest 回填路径：前 3 档主要风险在 `latest_source_bundle` 是否被错误推进，`finalized` 风险在 `latest_artifact` 与 `latest_export` 的分界，`export_failed` 风险在失败 task 不应反向长出任何 latest 结果对象。Phase 7.2 收口时应把这些状态单独锁齐，才能真正说明 detail 聚合边界已闭合。
- Phase 7.2 收口 review 结论：当前 `apps/api/tests/test_artifact_persistence.py` 已分别覆盖 `/projects`、`/projects/{id}`、`/projects/{id}/status`、`/projects/{id}/exports`、`/projects/{id}/exports/{export_id}` 在 created / parsed / analyzed / parse_failed / briefing / outlined / planned / finalized / exported / export_failed 下的关键只读边界；未发现新的 P0/P1 级漏测。后续若新增 latest 聚合字段或新的只读投影视图，必须同步补独立边界回归，不能假设现有 status/detail/dashboard 用例会自然兜住。
- `created` 初始态也需要单独锁 detail/status/export-history 的一致性边界，不能只依赖全链路综合测试顺带覆盖。因为项目创建时就已经落下一条 ingest 成功任务，如果后续 read model 聚合调整不慎，最容易出现的是 `current_task` 还停在 ingest，但 detail 上已经错误挂出 parse 或生成链路的 `latest_*` 字段。
- `created` 初始态在 dashboard 列表层也要单独锁一次，而不能只依赖 mixed-state 列表回归。原因是 mixed-state 测试通常只盯排序和跨项目隔离，容易漏掉单项目最小场景下的默认计数值；一旦仓储默认值改坏，`file_count/parsed_file_count/failed_file_count` 最先漂移的正是这种“列表里只有 created 项目”的空输入边界。

- `files:parse` 成功并重建 `SourceBundle` 后，服务层会把项目状态推进到 `parsed`，同时写入 `TaskType.PARSE` 的成功 `TaskRun`；如果 Phase 7.2 只锁 `created/briefing/outlined/planned/finalized/exported/export_failed`，则 `parsed` 这一档读模型仍可能在后续重构中漂移而不被发现。
- 对仅含空白字符的 Markdown 执行 `files:parse` 会满足上传接口的最小长度约束，但 parser 仍会产出空内容 warning，从而使 `SourceBundle.status=needs_review`、项目状态推进到 `analyzed`；这给 Phase 7.2 提供了一个稳定、无需改生产代码的 `analyzed` 集成回归入口。
- `files:parse` 的全量失败路径不需要伪造磁盘异常；只要通过上传接口登记一个 parser 不支持的 `file_type`（例如 `binary`），服务层就会把该文件标记为 `parse_status=failed`、写入失败 `TaskRun(task_type=parse)`，并把项目状态推进到 `parse_failed` 且不生成 `SourceBundle`。这给 Phase 7.2 提供了一个稳定、无需改生产代码的 `parse_failed` 集成回归入口。
- `GET /projects/{id}/exports` 的 `limit` 契约需要同时锁住“非法值被 422 拦截”和“合法值真实裁剪结果集”两层语义；只测非正数校验还不足以防止后续 service/repository 改动让 `limit` 参数失效但表面仍保留在 API 上。
- `GET /projects` 的 dashboard 聚合虽然不直接返回历史导出列表，但它内部仍依赖项目详情里的 `latest_export` 解析逻辑；因此当同一 artifact 存在多次导出时，需要单独用集成回归锁定 `latest_export` 始终指向最近 run，避免历史列表查询和看板聚合在“当前结果”定义上发生漂移。
- `GET /projects/{id}/status` 当前直接复用按 `TaskRun.created_at.asc()` 返回的完整任务序列，并以尾项充当 `current_task`；因此当同一任务类型连续执行多次时，需要单独用集成回归锁定“尾项任务、current_task、latest_export、导出历史首项”仍共同指向最新 run，避免状态读模型与导出读模型对“当前任务”的定义发生漂移。
- `GET /projects` 的 dashboard 聚合在多项目场景下同时承载“项目列表排序”和“项目内 latest_export/current_task 聚合”两层语义；因此除了单项目正确性外，还需要单独用集成回归锁定 newest-first 排序与项目级读模型隔离，避免后续在复用详情聚合或调整列表排序时把别的项目 run 串到当前卡片上。
- `GET /projects` 在混合状态项目列表里不仅要保证排序和项目隔离，还要锁住“未导出项目的 latest_export 必须保持为空，current_task 保持 render”等空值/阶段边界语义；否则后续聚合代码一旦错误复用最近导出结果，就会让 render 项在 dashboard 上看起来像已经导出完成。
- `GET /projects` 在 created、finalized、exported 三态并存时，风险不只在 render/export 边界，还在“尚未启动的 created 项必须保持全空聚合”。如果不单独做回归，后续 dashboard 组装一旦错误复用上一张卡片的 detail/task 结果，就会让 created 项看起来像已经有 latest brief 或 current task。
- `GET /projects` 在 success/failed 混合导出列表里也需要单独锁边界：`export_failed` 项虽然会有失败 export task，但并不应该因此长出 `latest_export` 或其他 latest 结果对象。如果不单独做回归，后续 dashboard 聚合一旦从成功项目复用 detail 结果，失败项目就会被错误显示成已有交付件。
- `GET /projects/{id}/status` 的失败态也不能只校验 `current_task`；因为实现是“完整任务序列 + 尾项 current_task”双输出，如果不单独锁 `recent_tasks[-1]` 与 `project_status` 的一致性，后续改动很容易出现 current_task 已切到失败 export，但 recent_tasks 尾项或详情状态仍停留在上一个成功任务的漂移。
- `GET /projects/{id}/status` 的中间态也要单独锁边界，尤其是 render 已完成但 export 尚未发生时：如果不把 `project_status=finalized`、`current_task/recent_tasks[-1]=render`、`latest_export is None` 与空导出历史同时绑在一条回归里，后续聚合代码很容易把“已有 artifact”误推断成“已有 export”。
- `GET /projects/{id}/status` 的早期规划态同样需要细粒度锁边界。`briefing` 这一层的风险不是导出串读，而是“latest_brief 已推进”被误当成整个规划链都推进了；如果不单独做回归，后续详情聚合很容易提前长出 `latest_outline`、`latest_slide_plan` 甚至更后续字段。
- `GET /projects/{id}/status` 的早期规划边界不能只停在 `briefing`。`outlined` 这一层同样需要单独锁“latest_outline 已推进但 latest_slide_plan/latest_artifact/latest_export 仍为空”，否则后续状态聚合很容易把提纲阶段误显示成已经进入页规划或渲染阶段。
- `GET /projects/{id}/status` 的早期规划边界还需要继续推进到 `planned`。`latest_slide_plan` 已推进并不等于 artifact/render/export 已开始；如果不单独锁这层回归，后续状态聚合很容易把页规划阶段误显示成已经完成渲染或已有导出结果。

## 2025-02-14 导出结果最小可达性复用

- 阶段 6.4 的“导出后可直接拿结果”不需要新增下载接口；`GET /projects/{id}` 返回的 `latest_export` 已足够覆盖最小前端交付链路。
- 当前最有价值的最小结果入口是三类现成路径：`output_path`、`metadata.archive_manifest_path`、`metadata.export_log_path`，再配合 `run_id` 就能把“最新一次导出”变成可追溯的可交付结果。
- 对静态前端来说，先补“结果可达性”比先做“导出历史管理器”更合适，因为它不扩大后端契约面，也能直接验证版本化导出目录设计是否对用户可见。

## 2025-02-14 导出历史最小可见性复用

- 当 `ExportRecord` 已稳定持久化 `run_id`、`output_path`、`preview_pdf_path`、`metadata.archive_manifest_path` 与 `metadata.export_log_path` 后，阶段 6.4 的下一步不需要新建复杂下载管理器；补一个按时间倒序的 `GET /projects/{id}/exports` 即可低成本暴露最近历史版本。
- 对当前静态审阅页，最小历史可见性应优先做“最近几次导出列表”，而不是先做 run 对比或版本回退；这样既复用了既有版本化目录设计，也把新增后端契约面控制在只读查询范围内。

## 2025-02-14 历史导出详情切换复用

- 当静态审阅页已经具备最近导出列表后，下一步不必立刻引入版本对比器；补一个项目作用域内的 `GET /projects/{id}/exports/{export_id}`，再让前端以“选中 run -> 重绘现有摘要区”的方式切换详情，就能以很小的改动面把历史列表从“可见”推进到“可用”。
- 单条历史导出查询应强制做项目归属校验，而不是裸暴露全局 `export_id` 查询；这样既复用了仓储层现有 `ExportRecord`，也避免未来在多项目场景下把别的项目导出详情误暴露到当前审阅上下文。

## 2025-02-14 导出 run 差异摘要复用

- 当静态审阅页已经能查看指定历史 run 的完整详情后，下一步不必急着补 compare API；只要页面同时持有“所选 run 详情”和 `latest_export`，就可以在前端先生成格式、状态、时间和输出文件层面的最小差异摘要。
- 对当前 6.4 阶段，优先做只读 Run Delta 摘要比先做字段级深度 diff 或回滚按钮更稳妥，因为它不扩大后端契约面，却能立即回答“这个历史版本和当前最新版本差在哪里”。

## 2025-02-14 SVG 页级预览审阅复用

- 当 artifact 已持久化 `preview_image_paths` 或 `generated_svg_files` 时，阶段 6.2 的最小 SVG 审阅不必等待专用预览 API；静态前端可以直接消费这些相对路径，先把“页级可见”做出来。
- 对当前平台化阶段，更合适的推进顺序是“先有只读页级预览，再补页内批注和单页重生成”。这样既不扩大后端契约面，也能先验证现有 `svg_final` 产物是否真能被用户审阅。

## 2025-02-14 模板多维筛选复用

- 当 `GET /projects/templates` 已稳定返回 `scenario_tags`、`style_tags`、`density_range` 以及模板元数据时，阶段 6.4 的最小模板选择器不必先做服务端搜索；静态前端可以先在本地完成多维筛选，把模板发现闭环做出来。
- 对当前阶段六，优先补“先筛再选”的同页模板收敛，比先做模板推荐算法或搜索 API 更稳妥，因为它不扩大后端契约面，却能立即提升模板选择流程的清晰度。

## 2026-03-24 模板缩略预览复用

- 当 `GET /projects/templates` 已稳定返回 `preview_image_path` 与基础视觉元数据时，阶段 6.4 的下一步不必先补模板详情 API；静态前端可以直接把筛选结果渲染为模板卡片，先把“先看再选”的闭环做出来。
- 对当前阶段六，优先补模板缩略预览比先做推荐排序更稳妥，因为它不扩大后端契约面，却能立即降低纯文本模板下拉的选择成本。

# 关键发现

- ppt-master 的核心优势是 SVG-first，可生成更适合后续转为可编辑 PPT 的页面。
- LandPPT 的核心优势是平台化能力，包括 Web/API、项目管理、研究流程、模板管理和导出链路。
- Linux.do 方法的核心优势是专业 PPT 工作流：先澄清问题，再研究，再出提纲和页规划，再做视觉生成。
- 融合后的最佳结构应是双入口统一到同一个内容中间层，再进入统一的研究、提纲、页规划、设计和渲染流程。
- 模板层应保留 ppt-master 的 SVG 模板规范，同时引入 LandPPT 的模板管理与预览能力。
- 用户当前需要的不是架构说明，而是“可直接照着做”的实施蓝图，因此文档要从高层描述切换为阶段计划、任务清单、输入输出、验收标准和风险控制。
- 实施计划需要把抽象模块映射为具体目录、接口、数据模型、任务队列、测试与交付顺序。
- thesis-writer-v1 原先只有规划文档，没有代码工程骨架，因此必须从阶段 0 开始补 monorepo 基线。
- 当前机器被自动配置为 Python 3.6.2，和 FastAPI + Pydantic v2 基线不兼容；阶段 0 的代码已落地，但运行验证需要切换到 Python 3.11+ 或依赖 Docker。
- 已通过 uv 成功创建 Python 3.11.9 虚拟环境，并可在该环境下安装和运行项目依赖。
- API 与 Web 的本地短时启动验证均返回 200，说明阶段 0 的最小可运行骨架成立。
- 当前 shell 无法识别 docker 命令，后续若要验证 compose 拉起 PostgreSQL 与 Redis，需要先补 Docker CLI 可用性。
- 阶段 1 最适合先用文档固化模型，再用 Pydantic 落地统一契约，这样后续 API、数据库和任务编排可以围绕同一套对象推进。
- `packages/core-types` 已具备作为全项目统一领域模型包的基础条件，可直接支撑阶段 1 后续数据库层和接口层实现。
- monorepo 下的 `apps/api/src` 与 `packages/core-types/src` 需要同时加入工作区分析路径，否则 Pylance 会把有效源码误判为未解析导入。
- 阶段 1 的 API 骨架可以先用内存仓储完成契约打通，再在下一小阶段替换为真实 ORM 与 PostgreSQL 持久化实现，能显著降低联调成本。
- `core_types.common.CoreModel` 开启了 `use_enum_values=True`，因此进入仓储层的枚举字段实际表现为字符串；持久化代码不能再访问 `.value`。
- 在当前环境缺少 Docker / PostgreSQL 服务时，可用 SQLite 临时验证 SQLAlchemy 映射与仓储逻辑，先保证阶段目标推进。
- 阶段 1 的文件上传接口可以先只做“文件元数据登记”，把真实二进制存储与解析任务推迟到阶段 2，这样能先稳定 API 契约和状态字段。
- `POST /projects/{id}/brief:generate` 可以先基于已登记文件的元数据和摘要生成最小 `SourceBundle` / `PresentationBrief`，把深度解析和多文档归一化留到阶段 2。
- `POST /projects/{id}/outline:generate` 可以先基于 `PresentationBrief` 生成规则化章节骨架，后续再接入方法论引擎和更细的章节推理。
- FastAPI 本地接口自测依赖 `httpx`；如果使用 `TestClient`，需要明确把该依赖纳入开发环境。
- 使用 `TestClient(app)` 进行生命周期相关验证时，最好采用 `with TestClient(app) as client:`，否则启动期建表逻辑可能不执行。
- 项目详情里的 `latest_*_id` 字段如果不在仓储更新逻辑里同步推进，状态接口可能看起来“成功”但详情对象仍然落后，因此每新增一层核心对象都要同时更新项目关联字段。
- 若要在本地自测时临时把数据库从 `.env` 的 PostgreSQL 切到 SQLite，必须在导入 `app.main` 之前注入 `DATABASE_URL`，否则 `settings` 与 SQLAlchemy `engine` 会提前固化为默认连接串。
- `TemplateRegistryService` 当前的自动选模信号主要来自 `SlidePlan.design_direction`、`metadata.scenario_tags`、`metadata.style_tags` 等 token 交集，因此新增模板时优先补齐这些字段，比只增加配色更能立即提升选模质量。
- 在当前 Windows + Anaconda 环境下，`uv run pytest ...` 可能解析到外部 `pytest` 可执行文件，而不是项目 `.venv`；更稳妥的仓库内测试命令是 `uv run python -m pytest ...`。
- 当前仓库之前未把 `pytest` 固化到 `pyproject.toml`，会导致 `.venv` 虽有业务依赖却无法直接在项目解释器里运行测试；将 `pytest` 写入项目依赖后，`uv sync` 可恢复一致的测试基线。
- SVG 文本高度校验如果固定使用默认 `1.35` 行高，会与 renderer 中实际传入的 `1.0`、`1.15`、`1.2` 等值产生偏差；把 `line-height` 显式写入文本节点元数据，并让 validator 优先读取该值，能显著减少多行文本容器的误报和漏报。
- 在阶段 4 继续做文本越界治理时，不能只盯动态正文区；像 `section` 页左侧页码这类“看起来固定、实际仍是文本节点”的区域也应纳入统一 `_multiline_text()` 路径，否则会残留一批无法被一致校验的旁路文本容器。
- 对侧栏 bullet 场景，单条文本的 `data-max-height` 校验还不够，因为真正的越界常来自多条 bullet 的累计高度；因此 renderer 需要在 bullet 组层面显式维护总高度预算，优先从源头截断后续项，而不是把整组溢出留给后置 validator 被动发现。
- 对 TOC 场景，只有“动态 cursor 递增”还不够；如果条目自身的 `max_height` 与 `font_size * line_height * max_lines` 不匹配，换行会先被高度裁掉，导致两行分支根本不可达。目录区这类多项列表必须同时满足“单项可真实换行”和“项间步进跟随实际行数”两个条件，动态间距逻辑才有意义。
- 对 timeline 标签这类窄栏两行文本，风险和 TOC 是同一类：只声明 `max_lines=2` 不等于第二行真的能渲染出来。像 `font_size=18`、`line_height=1.15` 这样的配置，对应的高度预算必须显式覆盖第二行基线；否则测试里即使看到换行代码路径存在，实际 SVG 仍可能因为 `max_height` 偏小而退化为单行。
- 阶段 4 后续收尾时，不能只靠 `max_height` 与 `font_size * line_height * max_lines` 的肉眼估算继续猜缺陷；更稳妥的方式是先用 `_wrap_text()` 做数值探针，再补 renderer 级“第二行真实可达”回归。subtitle 与 card heading 这次就证明了：它们看起来接近风险边界，但实际预算是成立的，缺的是直接验收断言而不是生产代码修复。
- 同样的方法也适用于 `section title` 和 `chart caption`：即便这两块在视觉上接近收尾风险边界，探针结果仍显示当前预算足以容纳第二行，因此正确动作不是继续调高 `max_height`，而是把真实 `<tspan ... dy="...">` 输出纳入 renderer 回归，先锁定已成立的可达性，再决定是否存在新的生产问题。
- 这个探针优先的方法也适用于正文区：`hero summary` 与 `card body` 虽然分别是 3 行、4 行容器，看上去更像潜在高度风险点，但在当前 `_wrap_text()` 公式下预算依然成立。对这类容器，优先补“第三/第四行真实可达”回归，比继续机械调高 `max_height` 更能避免过度修复和无意义改动。
- 同一方法继续验证到 `cover body` 与 `ending body` 后，可以看出“正文区都一样”是错误假设：`cover body` 在当前预算下确实能稳定到 4 行，适合补真实可达回归；但 `ending body` 即使用更长样本探针，在居中布局和现有宽度/字号组合下仍只稳定产出 2 行，因此不能把 `hero/card/cover` 的多行经验机械外推到 ending 区，否则会把不存在的第三行能力写成错误测试。
- 对 `ending body` 这类居中大字号文案，正确收尾方式不是继续争论“理论上可否三行”，而是直接以真实 SVG 输出来定验收边界：当前 `<text x="640" y="380" ... text-anchor="middle">` 只稳定生成一个第二行 `<tspan x="640" dy="59.4">`，因此 renderer 回归应锁“第二行真实可达”，把第三行保留给未来真正的布局/字号调整，而不是提前写成错误期望。
- 阶段 4 收口时需要区分“高风险多行容器”与“低风险单行固定文案区”：footer 这种 `max_lines=1` 的截断设计，不应被误判为遗漏的多行能力缺口；section number 这类固定编号区只要已经纳入统一 `_multiline_text()` 约束链路并有元数据直测，就不值得再额外堆叠低收益测试。
- 当高风险多行容器已经覆盖到 subtitle、card heading、section title、chart caption、hero summary、card body、cover body、ending body、timeline label 与 TOC 这些真实风险点后，阶段 4 的下一步重点应切换为 phase boundary review、剩余视觉风险排查与出口标准确认，而不是继续机械枚举单行容器测试。
- 阶段边界 review 的判断标准不能只看“还有没有没测到的文本节点”，而要看 `分阶段实施计划.md` 里该阶段承诺的主能力是否已具备代码实现、针对性回归和可解释的残余风险。按这个口径，阶段 4 当前已经达到“可转入下一阶段，同时保留少量视觉尾项继续跟踪”的状态。
- 阶段 4 当前没有暴露新的 P0/P1 缺口；真正需要后移到下一阶段处理的风险，主要是导出链路联调、结果管理闭环以及跨模板视觉一致性，而不是继续在 renderer 内部扩写低收益文本回归。
- 阶段 5 的最小切入口不需要先做真实 PPTX 转换器；在现有代码里更合理的第一步是先把“只从 `svg_final/` 导出、失败前置校验、导出记录落库、项目详情可追溯”这条结果管理主链接通，再把真实 PPTX/PDF 生成替换进同一 API/仓储骨架。
- 当前仓储层原本只有 `get_export_job()` 读取路径，没有 `create_export_job()` 写路径；这说明 `ExportRecord` 虽已建模，但在 Phase 5 开始前实际仍停留在“数据结构预留”而不是“功能已接线”的状态。
- 对阶段 5 的第一段验收，优先验证“导出前必须来自 `svg_final/` 且 artifact 已 finalize”比验证真实 PPTX 内容更重要，因为这是后续真实导出器接入时最容易被绕开的根约束；本轮通过服务层前置校验把这条规则固定下来。
- 阶段 5 不能把“失败返回了 400”误当成结果管理闭环已经成立；如果失败导出没有同步写入 `ExportJob(status=failed)` 和失败 `TaskRun`，项目状态链路里就无法定位这次失败尝试，后续排障与审计都会失去抓手。
- `core_types.common.CoreModel` 的 `use_enum_values=True` 会让请求模型中的枚举字段在服务层表现为字符串，因此导出链路中的 `export_format` 不能假设始终可访问 `.value`；统一按字符串值处理，能同时规避成功路径和失败路径的同类隐患。
- 阶段 5 当前更稳妥的推进方式是先把“成功和失败都可追踪”的导出结果管理骨架做完整，再把真实 PPTX/PDF 生成器替换进已稳定的 API、仓储和任务状态流，而不是先堆真实导出实现后再补失败审计。
- 在当前仓库约束下，Phase 5 的真实 PPTX 最小实现不必一开始就依赖 PowerPoint、Apryse 或复杂 SVG->Shape 转换；先走 `svg_final -> PNG -> python-pptx` 的图片型导出链，可以较低成本获得“真实可打开的 PPTX 文件”与稳定测试面，后续再决定是否升级为更可编辑的 shape 级导出。
- 把真实导出器接到既有 `POST /projects/{id}/export` 骨架时，最重要的是保留原有前置约束和失败审计，而不是推倒重来；本轮直接复用 `svg_final` 校验、`ExportJob` 持久化和 `TaskRun` 记录，只替换成功路径的文件生成器，因此风险和改动面都更可控。
- 本轮 Phase 5 子切片 review 未发现新的 P0/P1 阻塞；首版 `run_id` 版本记录已接入 `ExportJob`、导出目录、API 返回与归档清单，同一 artifact 的重复导出已不会覆盖旧结果。当前残余风险主要收敛为“图片型 PPTX 仍不可编辑”和“尚未提供更完整的历史版本浏览/回退界面”，而不是导出链路完全不可用。
- PDF 预览的最小实现同样不需要新增独立 API；沿用既有 `POST /projects/{id}/export` 并按 `export_format` 分支，可以复用同一套 `svg_final` 前置校验、失败审计、`ExportJob` 持久化和项目详情聚合，只增加文件生成器与 `preview_pdf_path` 字段回填即可。
- 在当前依赖集下，用 `cairosvg.svg2pdf()` 逐页生成 PDF、再用 `pypdf` 合并为单个预览文件，是比引入新渲染后端更稳妥的第一步；它保留了 Phase 5 所需的真实 PDF 产物与可测页数语义，同时把改动面控制在现有导出骨架内。
- 阶段 6.1 的项目看板如果继续沿用现有 API 逐项目请求 `GET /projects/{id}` 与 `GET /projects/{id}/status`，前端会在项目数增长后迅速退化成 N+1 拉取模式；先在后端提供 `GET /projects` 聚合摘要接口，可以更低成本支撑看板视图，并复用仓储层已有 `latest_*` 聚合能力。
- 阶段 7.3 的“样例项目回归集”不适合直接复用 `storage/projects` 下散落的运行期 UUID 目录作为基线；这些目录天然受本地调试过程影响，内容不稳定、类别语义也不显式。先引入一个独立的 `sample-registry.json` 规范化清单，把样例类别、推荐模板和最小 brief 摘要固定下来，后续再逐步为每个样例补真实输入与 golden 产物，会比直接拿现有运行产物做回归更稳。
- 当前内置模板资产已经足够覆盖阶段 7.3 首批六类样例：`academic-defense` 可对应学术答辩，`consulting-premium`/`consulting-clean` 可承接企业战略与培训课件，`government-blue` 可承接政府汇报，`technology-grid` 可承接产品发布会与技术分享。因此阶段 7.3 的第一步无需先扩模板系统，优先把样例 registry 与模板存在性回归锁住更符合最小推进原则。
- 阶段 7.3 在 registry 骨架之后，下一条最小有效切片不是直接追求 golden 输出，而是先给每个样例补稳定 `source_asset` 映射，把 registry 从“只有元数据”推进到“可落到仓库内静态样例输入”。这样后续无论做 parse/brief golden 还是端到端 smoke，都有明确且可审计的输入基线，不必回退去依赖运行期 UUID 目录。
- 当阶段 7.3 从“静态样例清单”推进到“可执行样例基线”时，先抽一个轻量 `SampleCatalogService` 比在多个测试中重复 `json.loads(sample-registry.json)` 更稳。这样可以把 registry 结构依赖集中在一处，也为后续样例列表/样例导入接口留下直接复用点。
- 六类样例回归优先锁到规则式 `brief -> outline -> slide-plan` 链路是更合理的阶段切分：它已经足够覆盖 `source_mode`、样例输入、user intent、模板偏好和 `latest_*_id` 聚合，不需要一开始就把 render/export 全量 golden 也绑进 7.3 的最小闭环。
- 进入阶段 7.4 后，不必立即把六类样例全部升级成重型 golden；先挑一个 `file` 样例和一个 `chat` 样例，把 `artifact:generate -> export(pptx/pdf)` 跑通，更符合“最小真实交付基线”的推进原则，也能同时验证 render/export 与详情聚合没有断链。
- 对 7.4 的样例导出 smoke，最有价值的断言不是比对二进制文件内容，而是锁定 `generated_svg_files`、导出 `file_count`、PPT/PDF 页数和 `latest_artifact/latest_export` 聚合的一致性；这类断言对后续模板或渲染细节调整更稳，不会把测试脆弱性提前做高。
- 在有了代表性 export smoke 之后，下一刀最值得优先补的是“六类样例全量 render smoke”，而不是立刻把六类样例全部升到 export。因为 render 层已经覆盖模板选择、design spec、validator/finalizer 和 `latest_artifact` 聚合，是把样例回归面从 2 个扩到 6 个时性价比最高的验证层。
- 当六类样例已经全部跑通 render smoke 后，把它们继续扩到 export smoke 是合理的 7.4 下一刀，但仍应坚持“结构断言优先于二进制 golden”：验证 `export_kind`、`file_count`、PPT/PDF 页数、`preview_pdf_path` 和 `latest_export` 聚合即可，不要把 `.pptx/.pdf` 文件字节内容直接固化成快照。
- 对 7.4 的最小 golden 基线，直接读取 render 落盘目录中的 `design-spec.json`、`render-log.json` 和 `svg_final/slide-*.svg` 比比对完整 SVG 文本更稳。前者能锁住模板选择、page_count、validation/finalization 语义和 finalized 页面数量，后者则会因文案或细节排版微调而产生高噪声失败。
- 当前仓库的数据库初始化原先完全依赖 `AUTO_CREATE_TABLES` 与 `Base.metadata.create_all()`；要把它提升为可部署体系，最小可靠做法不是扩大启动时隐式建表逻辑，而是引入 `alembic` 初始 revision，并用 focused 测试直接验证 `upgrade head` 能从空库创建 schema。
- 当当前工作机缺少 Docker CLI 时，阶段 7.5 的 PostgreSQL 迁移验证不应退化成纯文档说明；更稳妥的做法是补一个受 `TEST_POSTGRES_MIGRATION_URL` 驱动的 smoke 测试入口，让同一套仓库能在 CI、预发或有现成 PostgreSQL 的环境执行真实 `upgrade head` 验证。
- 初始 Alembic revision 在 SQLite 下可过并不代表 PostgreSQL 也安全；像 `projects.latest_*` 这种指向后续表的外键，如果以内联方式放在 `projects` 建表语句里，会在 PostgreSQL 上因为被引用表尚未存在而失败。更稳妥的初始 schema 写法是先建列，等依赖表全部存在后再补外键，并对 SQLite 保持跳过追加外键的兼容分支。
- 现有 API 测试对 `AUTO_CREATE_TABLES=true` 仍存在广泛耦合，一次性替换全部测试风险过高；先抽公共 migration bootstrap helper，再在代表性测试文件中切换到 Alembic 预建库，是更可控的渐进迁移路径。
- 阶段 7.4 的发布文档不需要空泛重复 README。更有价值的做法是把“配置入口位置、需要检查的目录、哪些事项已有自动化证明、哪些事项仍是缺口”写成一份独立 checklist，这样后续进入 7.5/上线前收口时可以直接复用。
- 对样例 render smoke，最稳的断言依然是结构一致性而不是 SVG 文本快照：用 `generated_svg_files`、`checked_file_count`、`invalid_file_count`、`finalization_summary.page_count` 去锚定 `slide_plan.page_count`，能在保留高覆盖的同时减少模板文案微调导致的脆弱失败。
- 当前 `apps/web` 仍是纯静态页和 `http.server` 启动方式，因此阶段 6.1 的最小看板实现优先选择“无构建依赖、直接 fetch API”的方案更稳妥；等审阅闭环和交互复杂度上升后，再决定是否引入真正的前端框架重构。
- 由于 `apps/web/server.py` 只是静态文件服务器，前端直连 API 时默认会遇到跨域约束；现阶段看板先通过可配置 API Base 暴露该依赖，后续若要把 Web 作为默认操作入口，需要补 CORS 或反向代理，而不是在前端里硬编码规避。
- 对阶段 6.1 的看板接口，最有价值的第一条自动化回归不是前端 DOM 断言，而是 API 聚合断言：只要先锁住 `GET /projects` 对 `latest_brief`、`latest_outline`、`latest_slide_plan`、`latest_artifact`、`latest_export` 和 `current_task` 的返回语义，后续前端筛选、深链或框架重构都能在稳定数据契约上演进。
- 对当前无构建依赖的静态看板，筛选/检索与详情深链最稳妥的实现方式是继续留在客户端：先把 `GET /projects` 一次性拉回的聚合结果缓存在页面内，再基于状态和关键字做本地过滤，并用 `#project-{id}` 管理可分享定位，不必过早引入额外路由层或新增搜索 API。
- 阶段 6.2 的第一段审阅面同样不必先引入前端框架或新增 review 专用 API；复用现有静态页、`GET /projects/{id}` 聚合详情以及 `PATCH /projects/{id}/brief|outline|slide-plan`，先把“选中项目后可直接查看并轻量修订 latest 对象”这条最短审阅闭环接通，能更低成本验证交互需求。
- 对 SVG 审阅节点，当前更稳妥的推进顺序不是立即做完整页级预览器，而是先在审阅面暴露 artifact/export 摘要、`preview_pdf_path`、SVG 数量与 validation/finalization 信息，等确认审阅流和局部重生成需求后，再决定是嵌 iframe、图片缩略图还是独立预览页。
- 阶段 6.3 的第一段最小交付同样不应先发明“单页重生成”接口；在现有后端契约里，最小可行路线是先复用 `preferred_template_id` 和 `template_id`，把“更换模板后整体重生成 SlidePlan / 重渲染 Artifact”接到同一个审阅页，先验证模板驱动工作流成立，再决定局部重生成 API 的粒度。
- `ProjectService.generate_slide_plan()` 与 `TemplateRegistryService.resolve_template()` 已经天然支持模板覆盖，因此 6.3 的首个切片重点不在新增后端，而在前端把模板列表、覆盖参数和 regenerate 触发链路接通，同时用 focused API 回归锁住 latest slide plan / artifact 元数据的回写语义。
- `apps/web` 当前仍采用静态页面 + 原生 ES module 的轻量交付模式，因此“按实施方案分层”不等于必须立刻引入前端框架；更稳妥的做法是先把页面入口、项目域功能和公共 API/格式化能力拆到 `pages/features/lib`，先解决单文件脚本膨胀问题，再在此基础上继续推进 6.3/6.4 交互。
- 阶段 6.4 的最小导出交互同样不需要新增专用前端框架层或后端中转接口；在现有契约下，直接把 `POST /projects/{id}/export` 接进审阅工作区，并在成功后回刷 `GET /projects/{id}` 聚合详情，就足以先验证“从审阅到交付”的前端闭环。导出历史、版本浏览和下载管理应后置为下一层平台化增强，而不是阻塞当前最小切片。
- 阶段 7.2 的第一刀更适合先补项目聚合语义的 API 集成测试，而不是平均铺开到所有模块单测；`/projects/{id}`、`/projects/{id}/status`、`/projects/{id}/exports`、`/projects/{id}/exports/{export_id}` 这组接口横跨 latest 聚合、TaskRun 轨迹和导出记录，是当前最容易因后续改动而发生“接口各自正确、组合后不一致”的区域。
- 当这组项目聚合语义 happy path 已有集成回归后，下一刀优先级最高的不是更多成功场景，而是共享失败入口的一致性：只要服务层统一通过 `get_project()` 做缺失项目校验，就应有一条 grouped regression 锁住 `/projects/{id}`、`/status`、`/exports`、`/exports/{export_id}` 全部返回同一个 `404 Project not found` 契约，避免未来局部改动出现读模型端点错误语义分叉。
- 对导出详情端点，失败路径需要再细分一层：`GET /projects/{id}/exports/{export_id}` 既可能因为项目不存在返回 `Project not found`，也可能在项目存在时因为该导出记录缺失或不归属当前项目而返回 `Export job not found`。这两层 404 如果不分别做集成回归，后续很容易在仓储或服务重构时被错误合并。
- 对导出历史端点，空结果也是需要单独锁定的契约：`GET /projects/{id}/exports` 在项目存在但尚无任何导出记录时，应返回 `200` 与空数组，而不是因为 `latest_export` 为空或列表为空就退化成错误分支。否则后续若有人把历史接口偷懒实现为“读取 latest_export 或假定至少一条记录”，前端的初始审阅态会被无意义地打断。
- 对导出历史这类只读列表接口，参数边界也应尽量在路由层前置收紧，而不是把 `0`、负数之类模糊值传到服务/仓储层再默默返回空集。用 FastAPI `Query(..., ge=1)` 把 `limit` 契约声明清楚，比依赖底层数据库对 `.limit(0)` 或负数的宽松行为更稳妥，也更便于前端和测试统一预期。
- 对导出详情 path 参数，真正的“空值”URL 在 FastAPI 路由层面本就进不来，因此更值得锁定的是“形态异常但仍可路由”的 `export_id`。在当前实现里，这类输入只要项目存在，就应继续统一收敛到 `404 Export job not found`，而不是额外演化出新的 400/422 分支；否则前端只是在拼接历史详情链接时夹带了编码空白，也会遇到难以解释的错误语义分叉。
