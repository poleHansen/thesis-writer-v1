# 工程规范

## 命名规范

- Python 包名使用小写下划线
- API 路由使用复数资源名
- 数据模型统一采用名词型 PascalCase
- 环境变量统一使用大写下划线

## 目录规范

- apps/ 放可运行应用
- packages/ 放可复用业务包
- docs/architecture/ 放架构与契约文档
- storage/ 放本地开发环境数据
- infra/ 放部署与运维辅助文件

## 环境变量规范

- 应用级变量统一以前缀 APP\_ 开头
- 数据库变量统一以 POSTGRES\_ 开头
- Redis 变量统一以 REDIS\_ 开头
- 对外密钥统一写入 .env，不入库

## 日志规范

- 使用 JSON 结构化日志作为后续默认形态
- 每条日志至少带 timestamp、level、service、message、request_id
- 任务链路日志要带 project_id 和 task_run_id

## 错误码规范

- HTTP API 错误采用 domain + numeric code 形式
- 阶段 1 开始定义统一错误码表
- 所有后台任务失败必须有 machine-readable error_code

## 提交规范

- 采用 Conventional Commits
- 范围建议使用 api、web、core-types、docs、infra、renderer、export
- 每次提交只解决一个明确问题
