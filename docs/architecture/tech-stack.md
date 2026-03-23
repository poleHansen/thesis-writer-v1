# 技术栈基线

## 目标

为 thesis-writer-v1 建立阶段 0 的统一技术基线，保证后续各阶段在相同的工程约束下推进。

## 总体选型

- Web: 先采用静态前端骨架，后续升级到 React + Vite
- API: FastAPI
- 异步任务: Celery，消息代理与结果后端统一依赖 Redis
- 数据库: PostgreSQL 16
- 缓存与队列: Redis 7
- 对象存储: 本地存储，目录为 storage/
- 模板与渲染: Python 主导，后续接入 ppt-master 的 SVG 渲染链路
- 类型契约: Python Pydantic 模型为主，必要时再补前端 TypeScript SDK

## 模块语言划分

- apps/api: Python
- apps/web: HTML/CSS/JavaScript，后续迁移到 TypeScript
- packages/core-types: Python
- packages/ingestion: Python
- packages/methodology-engine: Python
- packages/template-registry: Python
- packages/svg-renderer: Python
- packages/export-service: Python
- packages/llm-gateway: Python

## 本地开发环境

- Python 3.11+
- Docker Desktop
- Docker Compose
- 可选 Node.js 20+，供后续 Web 升级使用

## 生产部署差异

- 本地使用 docker-compose 管理 PostgreSQL、Redis、API、Web
- 生产环境建议将 API、Worker、Web 分离部署
- 本地使用 storage/ 目录持久化，生产环境替换为对象存储
- 本地使用 .env，生产环境改为 Secret 管理
