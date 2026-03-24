import { createApiClient } from "../../lib/api.js";
import { renderDashboard, focusActiveProject } from "../../features/project/dashboard.js";
import { createReviewController } from "../../features/project/review.js";
import { createAppState, getActiveProjectId } from "../../features/project/state.js";

const dom = {
  dashboardGrid: document.getElementById("dashboard-grid"),
  statusBanner: document.getElementById("status-banner"),
  refreshButton: document.getElementById("refresh-button"),
  apiBaseInput: document.getElementById("api-base"),
  statusFilter: document.getElementById("status-filter"),
  searchInput: document.getElementById("search-input"),
  template: document.getElementById("project-card-template"),
  reviewEmptyState: document.getElementById("review-empty-state"),
  reviewContent: document.getElementById("review-content"),
  reviewKicker: document.getElementById("review-kicker"),
  reviewTitle: document.getElementById("review-title"),
  reviewStatus: document.getElementById("review-status"),
  reviewDescription: document.getElementById("review-description"),
  reviewMeta: document.getElementById("review-meta"),
  artifactSummary: document.getElementById("artifact-summary"),
  artifactPreviewGrid: document.getElementById("artifact-preview-grid"),
  exportHistory: document.getElementById("export-history"),
  reviewEmptyMessage: document.querySelector("#review-empty-state p:last-of-type"),
  briefGoal: document.getElementById("brief-goal"),
  briefAudience: document.getElementById("brief-audience"),
  briefCoreMessage: document.getElementById("brief-core-message"),
  briefStoryline: document.getElementById("brief-storyline"),
  briefTone: document.getElementById("brief-tone"),
  briefPageCount: document.getElementById("brief-page-count"),
  briefStylePreferences: document.getElementById("brief-style-preferences"),
  briefRisks: document.getElementById("brief-risks"),
  briefAssumptions: document.getElementById("brief-assumptions"),
  outlineTitle: document.getElementById("outline-title"),
  outlineSummary: document.getElementById("outline-summary"),
  outlineChapters: document.getElementById("outline-chapters"),
  slidePlanDirection: document.getElementById("slide-plan-direction"),
  slidePlanPageCount: document.getElementById("slide-plan-page-count"),
  slidePlanSlides: document.getElementById("slide-plan-slides"),
  saveBriefButton: document.getElementById("save-brief-button"),
  saveOutlineButton: document.getElementById("save-outline-button"),
  saveSlidePlanButton: document.getElementById("save-slide-plan-button"),
  templateScenarioFilter: document.getElementById("template-scenario-filter"),
  templateStyleFilter: document.getElementById("template-style-filter"),
  templateDensityFilter: document.getElementById("template-density-filter"),
  templateIndustryFilter: document.getElementById("template-industry-filter"),
  templateSelect: document.getElementById("template-select"),
  templateFilterHint: document.getElementById("template-filter-hint"),
  templatePreviewGrid: document.getElementById("template-preview-grid"),
  rerunSlidePlanButton: document.getElementById("rerun-slide-plan-button"),
  rerenderArtifactButton: document.getElementById("rerender-artifact-button"),
  exportFormatSelect: document.getElementById("export-format-select"),
  exportArtifactId: document.getElementById("export-artifact-id"),
  runExportButton: document.getElementById("run-export-button"),
  metricProjects: document.getElementById("metric-projects"),
  metricExports: document.getElementById("metric-exports"),
  metricRisks: document.getElementById("metric-risks"),
};

const state = createAppState();

function getApiBase() {
  return dom.apiBaseInput.value.trim().replace(/\/$/, "");
}

const api = createApiClient(getApiBase);
const review = createReviewController(dom, state);

function createExportSelectionHandler(exportHistory, latestExport) {
  return async function handleExportSelection(exportId) {
    if (!state.currentProjectId || exportId === state.selectedExportId) {
      return;
    }
    state.selectedExportId = exportId;
    dom.statusBanner.textContent = "正在切换导出历史版本...";
    try {
      const exportPayload = await api.getProjectExport(state.currentProjectId, exportId);
      review.renderArtifactSummary(state.currentProjectDetail.latest_artifact, exportPayload.export_job);
      review.renderExportDelta(exportPayload.export_job, latestExport);
      review.renderExportHistory(exportHistory.exports || [], {
        selectedExportId: state.selectedExportId,
        onSelectExport: createExportSelectionHandler(exportHistory, latestExport),
      });
      dom.statusBanner.textContent = `已切换到导出版本 ${exportPayload.export_job.run_id}。`;
    } catch (error) {
      dom.statusBanner.textContent = `切换导出版本失败：${error.message}`;
    }
  };
}

function getSelectedExportId(detail, exportHistoryPayload) {
  if (state.selectedExportId) {
    return state.selectedExportId;
  }
  if (detail && detail.latest_export && detail.latest_export.id) {
    return detail.latest_export.id;
  }
  const exports = exportHistoryPayload && Array.isArray(exportHistoryPayload.exports) ? exportHistoryPayload.exports : [];
  return exports.length ? exports[0].id : "";
}

async function loadProjectDetail(projectId, options = {}) {
  const { preserveBanner = false } = options;
  review.setReviewDisabledState(true);
  if (!preserveBanner) {
    dom.statusBanner.textContent = `正在加载项目 ${projectId} 的审阅详情...`;
  }
  try {
    const [detail, exportHistory] = await Promise.all([
      api.getProjectDetail(projectId),
      api.getProjectExports(projectId, 5),
    ]);
    const selectedExportId = getSelectedExportId(detail, exportHistory);
    let selectedExport = detail.latest_export;
    if (selectedExportId) {
      const exportPayload = await api.getProjectExport(projectId, selectedExportId);
      selectedExport = exportPayload.export_job;
      state.selectedExportId = selectedExport.id;
    } else {
      state.selectedExportId = "";
    }
    review.populateReview(detail);
    review.renderArtifactSummary(detail.latest_artifact, selectedExport);
    review.renderArtifactPreview(detail.latest_artifact);
    review.renderExportDelta(selectedExport, detail.latest_export);
    review.renderExportHistory(exportHistory.exports || [], {
      selectedExportId: state.selectedExportId,
      onSelectExport: createExportSelectionHandler(exportHistory, detail.latest_export),
    });
    if (!preserveBanner) {
      dom.statusBanner.textContent = `已加载项目 ${detail.project.name} 的阶段审阅详情。`;
    }
  } catch (error) {
    review.resetReviewPanel(`项目详情加载失败：${error.message}`);
    dom.statusBanner.textContent = `加载项目 ${projectId} 详情失败：${error.message}`;
  }
}

async function loadTemplates() {
  try {
    const payload = await api.getTemplates();
    state.availableTemplates = payload.templates || [];
    review.renderTemplateOptions(dom.templateSelect.value);
  } catch (error) {
    state.availableTemplates = [];
    review.renderTemplateOptions("");
    dom.statusBanner.textContent = `模板列表加载失败：${error.message}。当前仍可继续审阅，但无法在页面内切换模板。`;
  }
}

function handleTemplateFilterChange() {
  review.renderTemplateOptions(dom.templateSelect.value);
}

async function loadDashboard(options = {}) {
  const { preserveSelection = false, preserveBanner = false } = options;
  if (!preserveBanner) {
    dom.statusBanner.textContent = "正在同步项目摘要...";
  }
  dom.refreshButton.disabled = true;
  try {
    const payload = await api.getProjects();
    state.dashboardItems = payload.projects || [];
    renderDashboard(state.dashboardItems, dom);
    const activeProjectId = preserveSelection ? state.currentProjectId || getActiveProjectId() : getActiveProjectId();
    if (activeProjectId) {
      const exists = state.dashboardItems.some((item) => item.project.id === activeProjectId);
      if (exists) {
        await loadProjectDetail(activeProjectId, { preserveBanner: true });
      } else {
        review.resetReviewPanel();
      }
    } else {
      review.resetReviewPanel();
    }
  } catch (error) {
    state.dashboardItems = [];
    dom.dashboardGrid.innerHTML = "";
    dom.metricProjects.textContent = "0";
    dom.metricExports.textContent = "0";
    dom.metricRisks.textContent = "0";
    review.resetReviewPanel(`当前无法获取项目列表：${error.message}`);
    dom.statusBanner.textContent = `加载失败：${error.message}。请确认 API 已在 ${getApiBase()} 启动，并允许跨域访问。`;
  } finally {
    dom.refreshButton.disabled = false;
  }
}

async function saveReviewSection(endpoint, payload, successMessage) {
  if (!state.currentProjectId) {
    return;
  }
  review.setReviewDisabledState(true);
  dom.statusBanner.textContent = "正在提交审阅修改...";
  try {
    await api.patchReviewSection(state.currentProjectId, endpoint, payload);
    await loadDashboard({ preserveSelection: true, preserveBanner: true });
    await loadProjectDetail(state.currentProjectId, { preserveBanner: true });
    dom.statusBanner.textContent = successMessage;
  } catch (error) {
    dom.statusBanner.textContent = `提交失败：${error.message}`;
    review.setReviewDisabledState(false);
  }
}

async function triggerGeneration(endpoint, payload, successMessage) {
  if (!state.currentProjectId) {
    return;
  }
  review.setReviewDisabledState(true);
  dom.statusBanner.textContent = "正在执行阶段重生成...";
  try {
    await api.triggerGeneration(state.currentProjectId, endpoint, payload);
    await loadDashboard({ preserveSelection: true, preserveBanner: true });
    await loadProjectDetail(state.currentProjectId, { preserveBanner: true });
    dom.statusBanner.textContent = successMessage;
  } catch (error) {
    dom.statusBanner.textContent = `重生成失败：${error.message}`;
    review.setReviewDisabledState(false);
  }
}

async function triggerExport(payload, successMessage) {
  if (!state.currentProjectId) {
    return;
  }
  review.setReviewDisabledState(true);
  dom.statusBanner.textContent = "正在生成导出文件...";
  try {
    await api.triggerExport(state.currentProjectId, payload);
    await loadDashboard({ preserveSelection: true, preserveBanner: true });
    await loadProjectDetail(state.currentProjectId, { preserveBanner: true });
    dom.statusBanner.textContent = successMessage;
  } catch (error) {
    dom.statusBanner.textContent = `导出失败：${error.message}`;
    review.setReviewDisabledState(false);
  }
}

async function handleHashSelection() {
  const activeProjectId = getActiveProjectId();
  focusActiveProject();
  if (!activeProjectId) {
    review.resetReviewPanel();
    return;
  }
  if (!state.dashboardItems.some((item) => item.project.id === activeProjectId)) {
    review.resetReviewPanel("当前筛选条件下未显示该项目，请调整筛选条件后再审阅。\n");
    return;
  }
  await loadProjectDetail(activeProjectId, { preserveBanner: true });
}

dom.saveBriefButton.addEventListener("click", async () => {
  await saveReviewSection("brief", review.getBriefPayload(), "Brief 已更新并重新同步看板摘要。");
});

dom.saveOutlineButton.addEventListener("click", async () => {
  await saveReviewSection("outline", review.getOutlinePayload(), "Outline 已更新并重新同步看板摘要。");
});

dom.saveSlidePlanButton.addEventListener("click", async () => {
  await saveReviewSection("slide-plan", review.getSlidePlanPayload(), "Slide Plan 已更新并重新同步看板摘要。");
});

dom.rerunSlidePlanButton.addEventListener("click", async () => {
  await triggerGeneration("slide-plan:generate", review.getRegenerateSlidePlanPayload(), "已按所选模板重生成 Slide Plan，并刷新审阅工作区。");
});

dom.rerenderArtifactButton.addEventListener("click", async () => {
  await triggerGeneration("artifact:generate", review.getRerenderArtifactPayload(), "已按所选模板完成整体重渲染，并刷新审阅工作区。");
});

dom.runExportButton.addEventListener("click", async () => {
  const exportFormat = dom.exportFormatSelect.value || "pptx";
  const successMessage = exportFormat === "pdf"
    ? "已生成 PDF 预览，并刷新导出结果摘要。"
    : "已生成 PPTX 导出文件，并刷新导出结果摘要。";
  await triggerExport(review.getExportPayload(), successMessage);
});

dom.refreshButton.addEventListener("click", () => loadDashboard());
dom.statusFilter.addEventListener("change", () => renderDashboard(state.dashboardItems, dom));
dom.searchInput.addEventListener("input", () => renderDashboard(state.dashboardItems, dom));
dom.templateScenarioFilter.addEventListener("change", handleTemplateFilterChange);
dom.templateStyleFilter.addEventListener("change", handleTemplateFilterChange);
dom.templateDensityFilter.addEventListener("change", handleTemplateFilterChange);
dom.templateIndustryFilter.addEventListener("input", handleTemplateFilterChange);
dom.templateSelect.addEventListener("change", handleTemplateFilterChange);
window.addEventListener("hashchange", handleHashSelection);

review.setReviewDisabledState(true);
loadTemplates().finally(() => loadDashboard());