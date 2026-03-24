# thesis-writer-v1

毕业论文初稿自动生成平台

## 环境要求

- Python 3.11+
- uv

## 安装依赖

在仓库根目录执行：

```bash
uv sync
```

## 本地启动

### 启动 API

在仓库根目录执行：

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir apps/api/src --reload
```

访问地址：

- API: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

### 启动 Web

在仓库根目录执行：

```bash
uv run python apps/web/server.py
```

访问地址：

- Web: http://127.0.0.1:3000

## 子应用说明

- Web 说明见 `apps/web/README.md`
- API 说明见 `apps/api/README.md`

## Docker Compose

如果需要使用容器启动依赖服务和应用，可在仓库根目录执行：

```bash
docker compose up --build
```
