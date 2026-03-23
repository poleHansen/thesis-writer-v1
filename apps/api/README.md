# API 应用

## 本地运行

```bash
pip install -e .
uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir apps/api/src
```

## 健康检查

- GET /health
