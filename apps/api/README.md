# API 应用

## 本地运行

```bash
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir apps/api/src --reload
```

默认地址: http://127.0.0.1:8000

接口文档:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## 健康检查

- GET /health
