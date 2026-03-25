import { formatDate } from "../../lib/formatters.js";
import { getActiveProjectId, getProjectHash } from "./state.js";

function summarizePlanning(item) {
  const lines = [];
  if (item.latest_brief) {
    lines.push(`Brief: ${item.latest_brief.presentation_goal}`);
  }
  if (item.latest_outline) {
    lines.push(`Outline: ${item.latest_outline.title}`);
  }
  if (item.latest_slide_plan) {
    lines.push(`Slides: ${item.latest_slide_plan.page_count} pages planned`);
  }
  return lines;
}

function summarizeOutput(item) {
  const lines = [];
  if (item.latest_artifact) {
    lines.push(`Render: ${item.latest_artifact.render_status}`);
    if (item.latest_artifact.metadata && item.latest_artifact.metadata.template_name) {
      lines.push(`Template: ${item.latest_artifact.metadata.template_name}`);
    }
  }
  if (item.latest_export) {
    lines.push(`Export: ${item.latest_export.status} (${item.latest_export.export_format})`);
  }
  if (item.current_task) {
    lines.push(`Task: ${item.current_task.task_type} / ${item.current_task.task_status}`);
  }
  return lines;
}

function createList(documentRef, items, emptyText) {
  if (!items.length) {
    const empty = documentRef.createElement("p");
    empty.className = "empty-line";
    empty.textContent = emptyText;
    return empty;
  }

  const list = documentRef.createElement("ul");
  list.className = "mini-list";
  items.forEach((item) => {
    const row = documentRef.createElement("li");
    row.textContent = item;
    list.appendChild(row);
  });
  return list;
}

function matchesSearch(item, query) {
  if (!query) {
    return true;
  }

  const searchableContent = [
    item.project.name,
    item.project.description || "",
    item.project.status || "",
    item.project.source_mode || "",
    ...(item.project.tags || []),
    item.latest_brief ? item.latest_brief.presentation_goal || "" : "",
    item.latest_brief ? item.latest_brief.target_audience || "" : "",
    item.latest_outline ? item.latest_outline.title || "" : "",
  ]
    .join("\n")
    .toLocaleLowerCase();

  return searchableContent.includes(query);
}

export function getFilteredItems(items, statusValue, searchValue) {
  const query = searchValue.trim().toLocaleLowerCase();

  return items.filter((item) => {
    const projectStatus = String(item.project.status || "");
    const matchesStatus =
      statusValue === "all" ||
      projectStatus === statusValue ||
      (statusValue === "failed" && projectStatus.endsWith("failed"));

    return matchesStatus && matchesSearch(item, query);
  });
}

function renderProjectCard(item, dom) {
  const fragment = dom.template.content.cloneNode(true);
  const card = fragment.querySelector(".project-card");
  const title = fragment.querySelector(".project-title");
  const statusPill = fragment.querySelector(".status-pill");

  card.id = `project-${item.project.id}`;
  card.dataset.projectId = item.project.id;

  fragment.querySelector(".project-kicker").textContent = `Updated ${formatDate(item.project.updated_at)}`;
  statusPill.textContent = item.project.status;
  statusPill.dataset.status = item.project.status;
  fragment.querySelector(".project-description").textContent = item.project.description || "暂无项目描述。";

  const titleLink = document.createElement("a");
  titleLink.href = getProjectHash(item.project.id);
  titleLink.className = "project-link";
  titleLink.textContent = item.project.name;
  title.textContent = "";
  title.appendChild(titleLink);

  const stats = fragment.querySelector(".project-stats");
  const statValues = [
    ["Files", item.file_count],
    ["Parsed", item.parsed_file_count],
    ["Failed", item.failed_file_count],
    ["Tags", item.project.tags.length],
  ];
  statValues.forEach(([label, value]) => {
    const stat = document.createElement("div");
    stat.className = "stat-chip";
    stat.innerHTML = `<span>${label}</span><strong>${value}</strong>`;
    stats.appendChild(stat);
  });

  const inputLines = [`Mode: ${item.project.source_mode}`];
  if (item.latest_brief) {
    inputLines.push(`Audience: ${item.latest_brief.target_audience}`);
  }
  if (item.latest_brief && item.latest_brief.style_preferences.length) {
    inputLines.push(`Style: ${item.latest_brief.style_preferences.join(" / ")}`);
  }

  fragment.querySelector(".panel-inputs").appendChild(createList(document, inputLines, "暂无输入摘要"));
  fragment.querySelector(".panel-planning").appendChild(createList(document, summarizePlanning(item), "尚未生成 Brief / Outline / Slide Plan"));
  const outputPanel = fragment.querySelector(".panel-output");
  outputPanel.appendChild(createList(document, summarizeOutput(item), "尚未产生渲染或导出结果"));

  const detailLink = document.createElement("a");
  detailLink.href = getProjectHash(item.project.id);
  detailLink.className = "detail-link";
  detailLink.textContent = "进入项目工作区";
  outputPanel.appendChild(detailLink);

  card.addEventListener("click", (event) => {
    const clickedLink = event.target.closest("a");
    if (!clickedLink) {
      window.location.href = getProjectHash(item.project.id);
    }
  });

  return fragment;
}

function updateMetrics(items, dom) {
  dom.metricProjects.textContent = String(items.length);
  dom.metricExports.textContent = String(items.filter((item) => item.latest_export && item.latest_export.status === "succeeded").length);
  dom.metricRisks.textContent = String(
    items.filter(
      (item) =>
        item.failed_file_count > 0 ||
        (item.latest_artifact &&
          item.latest_artifact.render_status !== "succeeded" &&
          item.latest_artifact.render_status !== "partial" &&
          item.latest_artifact.render_status !== "pending"),
    ).length,
  );
}

export function focusActiveProject() {
  const activeProjectId = getActiveProjectId();
  document.querySelectorAll(".project-card.is-active").forEach((card) => {
    card.classList.remove("is-active");
  });

  if (!activeProjectId) {
    return;
  }

  const activeCard = document.querySelector(`[data-project-id="${CSS.escape(activeProjectId)}"]`);
  if (!activeCard) {
    return;
  }

  activeCard.classList.add("is-active");
  activeCard.scrollIntoView({ behavior: "smooth", block: "start" });
}

export function renderDashboard(items, dom) {
  const filteredItems = getFilteredItems(items, dom.statusFilter.value, dom.searchInput.value);
  dom.dashboardGrid.innerHTML = "";
  updateMetrics(filteredItems, dom);

  if (!items.length) {
    dom.statusBanner.textContent = "当前没有 PPT 项目。先创建项目后，这里会显示各阶段摘要。";
    return;
  }

  if (!filteredItems.length) {
    dom.statusBanner.textContent = "没有匹配当前筛选条件的项目。请调整状态或检索关键字。";
    return;
  }

  filteredItems.forEach((item) => {
    dom.dashboardGrid.appendChild(renderProjectCard(item, dom));
  });
  dom.statusBanner.textContent = `已显示 ${filteredItems.length} / ${items.length} 个 PPT 项目，最后刷新时间 ${formatDate(new Date().toISOString())}`;
  focusActiveProject();
}