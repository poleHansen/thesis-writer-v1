# 项目状态机

## 主流程

```text
created
-> ingesting
-> parsed
-> analyzed
-> briefing
-> outlined
-> planned
-> rendering
-> finalized
-> exported
```

## 失败态

- parse_failed
- plan_failed
- render_failed
- export_failed

## 状态说明

- created: 项目已建立，但尚未开始摄取输入
- ingesting: 文件上传、聊天输入整理或 URL 抓取进行中
- parsed: 输入已被解析为原始结构化内容
- analyzed: `SourceBundle` 已规范化完成，可进入方法论链路
- briefing: 正在生成或修订 `PresentationBrief`
- outlined: 提纲已生成，可继续页规划
- planned: `SlidePlan` 已完成，可进入渲染
- rendering: 正在生成 SVG 页面与中间产物
- finalized: SVG 已完成整理与校验，可进入导出
- exported: 最终交付物已生成

## 失败恢复策略

- parse_failed: 允许重新解析文件或替换源文件后重试
- plan_failed: 允许修订 Brief / Outline 后重新规划
- render_failed: 允许按单页或整套重新渲染
- export_failed: 保留 `svg_final`，仅重试导出链路
