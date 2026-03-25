# 上线检查清单

本文档用于阶段 7.4 的发布前检查，目标是把“环境变量、存储、依赖服务、模板资源、导出链路”收敛成一份可以逐项核对的清单。

## 1. 环境变量

当前 API 配置入口位于 `apps/api/src/app/config.py`，发布前至少需要确认以下变量：

- `APP_ENV`
- `APP_HOST`
- `APP_PORT`
- `DATABASE_URL`
- `REDIS_URL`
- `AUTO_CREATE_TABLES`
- `uv run alembic upgrade head`
- `CORS_ALLOW_ORIGINS`

当前状态：

- 已实现 `.env` 加载与默认值回退。
- `README.md` 与 `docker-compose.yml` 已给出本地开发和容器环境的默认覆盖方式。
- 仍建议在正式环境提供显式 `.env` 或部署平台 Secret，而不是依赖默认值。

## 2. 存储目录

发布前必须保证以下目录可创建、可写、可读取：

- `storage/projects/`
- `storage/uploads/`
- `storage/postgres/`（仅 Docker Compose 本地持久化场景）
- `storage/redis/`（仅 Docker Compose 本地持久化场景）

当前状态：

- 仓库已包含 `storage/projects/` 与 `storage/uploads/` 目录。
- sample regression 已证明项目、render、export 产物能够持续写入 `storage/projects/{project_id}`。
- 若部署到容器或云主机，需要把宿主卷权限作为上线前必查项。

## 3. 数据库迁移

发布前理想状态：

- 存在正式迁移脚本体系，例如 `alembic` 或同级替代方案。
- 可以在部署时独立执行迁移，而不是依赖应用启动时隐式建表。
- 至少有一条从空数据库执行到最新 schema 的验证路径。

当前状态：

- 仓库已提供 `alembic.ini`、`migrations/env.py` 与初始 schema revision，可执行 `uv run alembic upgrade head`。
- `AUTO_CREATE_TABLES` 仍保留为本地开发/测试便利开关，不应作为生产部署的 schema 管理手段。
- `apps/api/tests/test_database_migrations.py` 已验证空 SQLite 库可以通过正式迁移命令创建 `alembic_version` 与核心业务表。
- `apps/api/tests/test_database_migrations.py` 还提供了受 `TEST_POSTGRES_MIGRATION_URL` 驱动的 PostgreSQL smoke，用于在具备真实 PostgreSQL 实例时执行同一条 `upgrade head` 验证。
- 当前工作机仍未识别 `docker` / `docker-compose` 命令，因此本轮无法在本机直接拉起 Compose PostgreSQL；真实 PostgreSQL smoke 需在安装 Docker CLI 的环境或现成 PG 实例上执行。

结论：

- `数据库迁移可执行` 已满足。
- 若进入真实发布阶段，应默认执行 `uv run alembic upgrade head`，而不是依赖应用启动时自动建表。
- 若要补 PostgreSQL 发布前验证，推荐执行：`TEST_POSTGRES_MIGRATION_URL=postgresql://postgres:postgres@127.0.0.1:5432/ai_ppt_migration_test uv run python -m pytest apps/api/tests/test_database_migrations.py -q`。

## 4. Redis 可用性

发布前需要确认：

- `REDIS_URL` 指向可访问实例。
- 目标环境网络与认证配置允许 API 容器或进程访问 Redis。

当前状态：

- `apps/api/src/app/config.py` 已暴露 `redis_url`。
- `docker-compose.yml` 已提供本地 `redis:7` 服务与默认 `redis://redis:6379/0` 覆盖。

## 5. 模板资源完整性

发布前需要确认：

- `templates/builtin/` 目录完整存在。
- 内置模板 JSON 与 sample registry 推荐模板 id 一致。

当前状态：

- 当前模板目录包含 `academic-defense`、`consulting-clean`、`consulting-premium`、`government-blue`、`research-paper`、`technology-grid` 六个模板。
- `apps/api/tests/test_sample_registry.py` 已有自动化用例校验样例 registry 推荐模板全部存在于内置模板目录。

## 6. 导出链路可用性

发布前需要确认：

- `artifact:generate` 能输出 finalized SVG。
- `POST /projects/{id}/export` 能输出 `pptx` 或 `pdf`。
- 导出记录写回 `latest_export`，且页数与 SVG 数量一致。

当前状态：

- `apps/api/tests/test_sample_registry.py` 已覆盖六类样例的全量 render smoke。
- 同一测试文件已覆盖六类样例的全量 export smoke，并同时验证 `pptx` 与 `pdf` 两种格式。
- 当前 focused regression 结果为 `31 passed`。

## 7. 发布结论

阶段 7.4 当前结论：

- 完整回归样例：已满足。
- 关键流程自动化测试：已满足。
- 失败定位成本可接受：已基本满足，当前 sample smoke 与 render metadata golden 已能把问题定位到 planning、render、export 或聚合回写边界。
- 部署文档完整：已补齐本清单，数据库迁移已具备正式执行路径。
