# Web 应用

这是面向 AI PPT 生成网站的前端工作台，负责承接项目 intake、阶段审阅、模板切换、渲染结果查看与导出入口。

当前前端已拆分为多页面站点：

- `index.html`：产品首页与入口导航
- `projects.html`：项目列表与组合状态概览
- `workspace.html`：单项目 intake、审阅、生成与导出工作区

## 本地运行

```bash
uv sync
uv run python apps/web/server.py
```

默认地址: http://127.0.0.1:3000

如果 3000 端口被占用，可以临时换端口：

```bash
$env:WEB_PORT=3001
uv run python apps/web/server.py
```
