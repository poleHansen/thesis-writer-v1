import { createApiClient } from "../../lib/api.js";
import { renderDashboard, focusActiveProject } from "../../features/project/dashboard.js";
import { createIntakeController } from "../../features/project/intake.js";
import { createReviewController } from "../../features/project/review.js";
import { createAppState, getActiveProjectId } from "../../features/project/state.js";

const dom = {
  dashboardGrid: document.getElementById("dashboard-grid"),
  statusBanner: document.getElementById("status-banner"),
  runtimeBanner: document.getElementById("runtime-banner"),
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
  intakeProjectName: document.getElementById("intake-project-name"),
  intakeSourceMode: document.getElementById("intake-source-mode"),
  intakeProjectDescription: document.getElementById("intake-project-description"),
  intakeProjectTags: document.getElementById("intake-project-tags"),
  createProjectButton: document.getElementById("create-project-button"),
  intakeProjectSelect: document.getElementById("intake-project-select"),
  intakeFileType: document.getElementById("intake-file-type"),
  intakeLocalFile: document.getElementById("intake-local-file"),
  intakeInlineContent: document.getElementById("intake-inline-content"),
  intakeInlineFileName: document.getElementById("intake-inline-file-name"),
  intakeMimeType: document.getElementById("intake-mime-type"),
  uploadFileButton: document.getElementById("upload-file-button"),
  intakeFileSelect: document.getElementById("intake-file-select"),
  intakeUserIntent: document.getElementById("intake-user-intent"),
  intakeRebuildBundle: document.getElementById("intake-rebuild-bundle"),
  intakeForceBrief: document.getElementById("intake-force-brief"),
  intakeForceOutline: document.getElementById("intake-force-outline"),
  parseFilesButton: document.getElementById("parse-files-button"),
  generateBriefButton: document.getElementById("generate-brief-button"),
  generateOutlineButton: document.getElementById("generate-outline-button"),
  intakeStream: document.getElementById("intake-stream"),
  exportDelta: document.getElementById("export-delta"),
};

const state = createAppState();

function getApiBase() {
  return dom.apiBaseInput.value.trim().replace(/\/$/, "");
}

const api = createApiClient(getApiBase);
const intake = createIntakeController(dom, state);
const review = createReviewController(dom, state);

function showRuntimeError(message) {
  if (!dom.runtimeBanner) {
    return;
  }
  dom.runtimeBanner.hidden = false;
  dom.runtimeBanner.textContent = message;
}

function clearRuntimeError() {
  if (!dom.runtimeBanner) {
    return;
  }
  dom.runtimeBanner.hidden = true;
  dom.runtimeBanner.textContent = "";
}

function wrapEvent(handler, fallbackMessage) {
  return async function wrappedHandler(...args) {
    clearRuntimeError();
    try {
      await handler(...args);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      showRuntimeError(`${fallbackMessage}：${message}`);
      dom.statusBanner.textContent = `${fallbackMessage}：${message}`;
    }
  };
}

function buildUserIntentPayload() {
  const text = dom.intakeUserIntent.value.trim();
  if (!text) {
    return null;
  }
  return {
    raw_text: text,
    user_notes: text,
  };
}

async function refreshProjectFiles(projectId) {
  if (!projectId) {
    state.currentProjectFiles = [];
    intake.renderProjectFiles([]);
    return;
  }
  const payload = await api.getProjectFiles(projectId);
  state.currentProjectFiles = payload.files || [];
  intake.renderProjectFiles(state.currentProjectFiles);
}

function syncIntakeProjectOptions(selectedProjectId = "") {
  intake.renderProjectOptions(state.dashboardItems, selectedProjectId || state.currentProjectId || getActiveProjectId());
}

function createExportSelectionHandler(exportHistory, latestExport) {
  return async function handleExportSelection(exportId) {
    if (!state.currentProjectId || exportId === state.selectedExportId) {
      return;
    }
    state.selectedExportId = exportId;
    dom.statusBanner.textContent = "正在切换交付历史版本...";
    try {
      const exportPayload = await api.getProjectExport(state.currentProjectId, exportId);
      review.renderArtifactSummary(state.currentProjectDetail.latest_artifact, exportPayload.export_job);
      review.renderExportDelta(exportPayload.export_job, latestExport);
      review.renderExportHistory(exportHistory.exports || [], {
        selectedExportId: state.selectedExportId,
        onSelectExport: createExportSelectionHandler(exportHistory, latestExport),
      });
      dom.statusBanner.textContent = `已切换到交付版本 ${exportPayload.export_job.run_id}。`;
    } catch (error) {
      dom.statusBanner.textContent = `切换交付版本失败：${error.message}`;
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
    dom.statusBanner.textContent = `正在加载项目 ${projectId} 的 PPT 审阅详情...`;
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
    await refreshProjectFiles(projectId);
    syncIntakeProjectOptions(projectId);
    review.renderArtifactSummary(detail.latest_artifact, selectedExport);
    review.renderArtifactPreview(detail.latest_artifact);
    review.renderExportDelta(selectedExport, detail.latest_export);
    review.renderExportHistory(exportHistory.exports || [], {
      selectedExportId: state.selectedExportId,
      onSelectExport: createExportSelectionHandler(exportHistory, detail.latest_export),
    });
    if (!preserveBanner) {
      dom.statusBanner.textContent = `已加载项目 ${detail.project.name} 的 PPT 审阅详情。`;
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
    dom.statusBanner.textContent = `模板列表加载失败：${error.message}。当前仍可继续审阅，但暂时无法在页面内切换模板。`;
  }
}

function handleTemplateFilterChange() {
  review.renderTemplateOptions(dom.templateSelect.value);
}

async function loadDashboard(options = {}) {
  const { preserveSelection = false, preserveBanner = false } = options;
  if (!preserveBanner) {
    dom.statusBanner.textContent = "正在同步 PPT 项目摘要...";
  }
  dom.refreshButton.disabled = true;
  try {
    const payload = await api.getProjects();
    state.dashboardItems = payload.projects || [];
    renderDashboard(state.dashboardItems, dom);
    syncIntakeProjectOptions();
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
    intake.renderProjectOptions([], "");
    intake.renderProjectFiles([]);
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
  dom.statusBanner.textContent = "正在生成交付文件...";
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

dom.createProjectButton.addEventListener("click", wrapEvent(async () => {
  const payload = intake.getCreateProjectPayload();
  if (!payload) {
    dom.statusBanner.textContent = "请先填写项目名称。";
    return;
  }

  intake.setBusyState(true);
  dom.statusBanner.textContent = "正在创建项目...";
  try {
    const response = await api.createProject(payload);
    intake.pushEvent(`已创建项目 ${response.project.name}。`);
    await loadDashboard({ preserveSelection: true, preserveBanner: true });
    location.hash = `#${response.project.id}`;
    await loadProjectDetail(response.project.id, { preserveBanner: true });
    dom.statusBanner.textContent = `项目 ${response.project.name} 已创建，可继续上传材料。`;
  } catch (error) {
    dom.statusBanner.textContent = `创建项目失败：${error.message}`;
  } finally {
    intake.setBusyState(false);
  }
}, "创建项目时发生运行时错误"));

dom.intakeProjectSelect.addEventListener("change", wrapEvent(async () => {
  const projectId = dom.intakeProjectSelect.value;
  if (!projectId) {
    intake.renderProjectFiles([]);
    return;
  }
  location.hash = `#${projectId}`;
  await loadProjectDetail(projectId, { preserveBanner: true });
}, "切换项目时发生运行时错误"));

dom.uploadFileButton.addEventListener("click", wrapEvent(async () => {
  const projectId = dom.intakeProjectSelect.value;
  if (!projectId) {
    dom.statusBanner.textContent = "请先选择项目。";
    return;
  }

  intake.setBusyState(true);
  dom.statusBanner.textContent = "正在上传源材料...";
  try {
    const payload = await intake.getUploadPayload();
    if (!payload) {
      dom.statusBanner.textContent = "请选择本地文件，或填写 URL / 文本来源。";
      return;
    }
    const response = await api.uploadProjectFile(projectId, payload);
    intake.pushEvent(`已上传文件 ${response.file.file_name}。`);
    await refreshProjectFiles(projectId);
    await loadDashboard({ preserveSelection: true, preserveBanner: true });
    await loadProjectDetail(projectId, { preserveBanner: true });
    dom.statusBanner.textContent = `文件 ${response.file.file_name} 上传完成。`;
  } catch (error) {
    dom.statusBanner.textContent = `上传失败：${error.message}`;
  } finally {
    intake.setBusyState(false);
  }
}, "上传文件时发生运行时错误"));

dom.parseFilesButton.addEventListener("click", wrapEvent(async () => {
  const projectId = dom.intakeProjectSelect.value;
  if (!projectId) {
    dom.statusBanner.textContent = "请先选择项目。";
    return;
  }

  intake.setBusyState(true);
  dom.statusBanner.textContent = "正在解析文件并构建 source bundle...";
  try {
    const response = await api.parseProjectFiles(projectId, intake.getParsePayload(buildUserIntentPayload()));
    intake.pushEvent(`解析完成：${response.files.length} 个文件进入 bundle。`);
    await refreshProjectFiles(projectId);
    await loadDashboard({ preserveSelection: true, preserveBanner: true });
    await loadProjectDetail(projectId, { preserveBanner: true });
    dom.statusBanner.textContent = "文件解析完成，可继续生成 Brief。";
  } catch (error) {
    dom.statusBanner.textContent = `解析失败：${error.message}`;
  } finally {
    intake.setBusyState(false);
  }
}, "解析文件时发生运行时错误"));

dom.generateBriefButton.addEventListener("click", wrapEvent(async () => {
  const projectId = dom.intakeProjectSelect.value;
  if (!projectId) {
    dom.statusBanner.textContent = "请先选择项目。";
    return;
  }

  intake.setBusyState(true);
  dom.statusBanner.textContent = "正在生成初始 Brief...";
  try {
    const response = await api.generateBrief(projectId, intake.getBriefGenerationPayload(buildUserIntentPayload()));
    intake.pushEvent(`Brief 已生成：${response.brief.id}。`);
    await loadDashboard({ preserveSelection: true, preserveBanner: true });
    await loadProjectDetail(projectId, { preserveBanner: true });
    dom.statusBanner.textContent = "Brief 已生成，审阅区已同步。";
  } catch (error) {
    dom.statusBanner.textContent = `Brief 生成失败：${error.message}`;
  } finally {
    intake.setBusyState(false);
  }
}, "生成 Brief 时发生运行时错误"));

dom.generateOutlineButton.addEventListener("click", wrapEvent(async () => {
  const projectId = dom.intakeProjectSelect.value;
  if (!projectId) {
    dom.statusBanner.textContent = "请先选择项目。";
    return;
  }

  const detail = state.currentProjectDetail;
  if (!detail || !detail.latest_brief) {
    dom.statusBanner.textContent = "请先生成 Brief，再生成 Outline。";
    return;
  }

  intake.setBusyState(true);
  dom.statusBanner.textContent = "正在生成初始 Outline...";
  try {
    const response = await api.generateOutline(projectId, intake.getOutlineGenerationPayload(detail.latest_brief.id));
    intake.pushEvent(`Outline 已生成：${response.outline.id}。`);
    await loadDashboard({ preserveSelection: true, preserveBanner: true });
    await loadProjectDetail(projectId, { preserveBanner: true });
    dom.statusBanner.textContent = "Outline 已生成，下一步可进入 Slide Plan 审阅。";
  } catch (error) {
    dom.statusBanner.textContent = `Outline 生成失败：${error.message}`;
  } finally {
    intake.setBusyState(false);
  }
}, "生成 Outline 时发生运行时错误"));

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
window.addEventListener("error", (event) => {
  showRuntimeError(`页面脚本异常：${event.message}`);
});
window.addEventListener("unhandledrejection", (event) => {
  const reason = event.reason instanceof Error ? event.reason.message : String(event.reason);
  showRuntimeError(`未处理的异步异常：${reason}`);
});

review.setReviewDisabledState(true);
loadTemplates().finally(() => loadDashboard());