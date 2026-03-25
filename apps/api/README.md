# API 应用

这是 AI PPT 生成网站的后端 API，负责项目、文件、内容规划、渲染结果与导出链路的服务编排。

## 本地运行

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir apps/api/src --reload
```

说明：`AUTO_CREATE_TABLES` 仅用于本地开发和测试兜底，正式 schema 演进统一通过 `uv run alembic upgrade head`。

默认地址: http://127.0.0.1:8000

接口文档:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## 健康检查

- GET /health
