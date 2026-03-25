import { createApiClient } from "../../lib/api.js";
import { createIntakeController } from "../../features/project/intake.js";
import { createReviewController } from "../../features/project/review.js";
import { createAppState } from "../../features/project/state.js";
import { parseOutlineChapters, parseSlideEntries, splitCommaSeparated, splitLineSeparated } from "../../lib/formatters.js";

const dom = {
  statusBanner: document.getElementById("status-banner"),
  runtimeBanner: document.getElementById("runtime-banner"),
  refreshButton: document.getElementById("refresh-button"),
  apiBaseInput: document.getElementById("api-base"),
  statusFilter: document.getElementById("status-filter"),
  searchInput: document.getElementById("search-input"),
  reviewEmptyState: document.getElementById("review-empty-state"),
  reviewContent: document.getElementById("review-content"),
  reviewKicker: document.getElementById("review-kicker"),
  reviewTitle: document.getElementById("review-title"),
  reviewStatus: document.getElementById("review-status"),
  reviewDescription: document.getElementById("review-description"),
  reviewMeta: document.getElementById("review-meta"),
  llmProvider: document.getElementById("llm-provider"),
  llmModel: document.getElementById("llm-model"),
  llmBaseUrl: document.getElementById("llm-base-url"),
  llmApiKey: document.getElementById("llm-api-key"),
  llmTemperature: document.getElementById("llm-temperature"),
  llmMaxTokens: document.getElementById("llm-max-tokens"),
  llmEnabled: document.getElementById("llm-enabled"),
  llmStatusPanel: document.getElementById("llm-status-panel"),
  saveLlmSettingsButton: document.getElementById("save-llm-settings-button"),
  testLlmSettingsButton: document.getElementById("test-llm-settings-button"),
  artifactSummary: document.getElementById("artifact-summary"),
  artifactPreviewGrid: document.getElementById("artifact-preview-grid"),
  exportHistory: document.getElementById("export-history"),
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
  dom.runtimeBanner.hidden = false;
  dom.runtimeBanner.textContent = message;
}

function clearRuntimeError() {
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

function getRequestedProjectId() {
  const params = new URLSearchParams(window.location.search);
  return params.get("project") || "";
}

function getFilteredItems(items) {
  const query = dom.searchInput.value.trim().toLocaleLowerCase();
  const statusValue = dom.statusFilter.value;
  return items.filter((item) => {
    const matchesStatus = statusValue === "all" || String(item.project.status || "") === statusValue;
    if (!matchesStatus) {
      return false;
    }
    if (!query) {
      return true;
    }
    return [item.project.name, item.project.description || "", ...(item.project.tags || [])]
      .join("\n")
      .toLocaleLowerCase()
      .includes(query);
  });
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
  intake.renderProjectOptions(getFilteredItems(state.dashboardItems), selectedProjectId || state.currentProjectId);
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
      const message = error instanceof Error ? error.message : String(error);
      dom.statusBanner.textContent = `切换交付版本失败：${message}`;
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
  state.currentProjectId = projectId;
  if (!preserveBanner) {
    dom.statusBanner.textContent = `正在加载项目 ${projectId} 的 PPT 审阅详情...`;
  }
  try {
    const [detail, exportHistory, llmSettingsPayload] = await Promise.all([api.getProjectDetail(projectId), api.getProjectExports(projectId, 5), api.getProjectLlmSettings(projectId)]);
    state.currentProjectDetail = detail;
    state.currentLlmSettings = llmSettingsPayload.settings;
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
    review.renderLlmSettings(llmSettingsPayload.settings);
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
    const message = error instanceof Error ? error.message : String(error);
    review.resetReviewPanel(`项目详情加载失败：${message}`);
    dom.statusBanner.textContent = `加载项目 ${projectId} 详情失败：${message}`;
  }
}

async function saveProjectLlmSettings() {
  if (!state.currentProjectId) {
    return;
  }
  review.setReviewDisabledState(true);
  dom.statusBanner.textContent = "正在保存模型设置...";
  try {
    const response = await api.updateProjectLlmSettings(state.currentProjectId, review.getLlmSettingsPayload());
    review.renderLlmSettings(response.settings);
    dom.statusBanner.textContent = "模型设置已保存。";
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    dom.statusBanner.textContent = `模型设置保存失败：${message}`;
  } finally {
    review.setReviewDisabledState(false);
  }
}

async function testProjectLlmSettings() {
  if (!state.currentProjectId) {
    return;
  }
  review.setReviewDisabledState(true);
  dom.statusBanner.textContent = "正在测试模型连接...";
  try {
    const result = await api.testProjectLlmSettings(state.currentProjectId);
    dom.llmStatusPanel.textContent = `${result.message} Provider=${result.provider} Model=${result.model}`;
    dom.statusBanner.textContent = "模型连接测试成功。";
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    dom.llmStatusPanel.textContent = `连接失败：${message}`;
    dom.statusBanner.textContent = `模型连接测试失败：${message}`;
  } finally {
    review.setReviewDisabledState(false);
  }
}

async function loadTemplates() {
  try {
    const payload = await api.getTemplates();
    state.availableTemplates = payload.templates || [];
    review.renderTemplateOptions(dom.templateSelect.value);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    state.availableTemplates = [];
    review.renderTemplateOptions("");
    dom.statusBanner.textContent = `模板列表加载失败：${message}。当前仍可继续审阅，但暂时无法在页面内切换模板。`;
  }
}

async function loadProjects(options = {}) {
  const { preserveBanner = false } = options;
  if (!preserveBanner) {
    dom.statusBanner.textContent = "正在同步项目工作区数据...";
  }
  dom.refreshButton.disabled = true;
  try {
    const payload = await api.getProjects();
    state.dashboardItems = payload.projects || [];
    syncIntakeProjectOptions(state.currentProjectId);
    const requestedId = state.currentProjectId || getRequestedProjectId() || (state.dashboardItems[0] && state.dashboardItems[0].project.id) || "";
    if (requestedId) {
      const exists = state.dashboardItems.some((item) => item.project.id === requestedId);
      if (exists) {
        await loadProjectDetail(requestedId, { preserveBanner: true });
      } else {
        review.resetReviewPanel("当前筛选条件下未找到该项目，请调整筛选条件或重新选择项目。");
      }
    } else {
      review.resetReviewPanel();
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    state.dashboardItems = [];
    review.resetReviewPanel(`当前无法获取项目列表：${message}`);
    intake.renderProjectOptions([], "");
    intake.renderProjectFiles([]);
    dom.statusBanner.textContent = `加载失败：${message}。请确认 API 已在 ${getApiBase()} 启动，并允许跨域访问。`;
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
    await loadProjects({ preserveBanner: true });
    await loadProjectDetail(state.currentProjectId, { preserveBanner: true });
    dom.statusBanner.textContent = successMessage;
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    dom.statusBanner.textContent = `提交失败：${message}`;
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
    await loadProjects({ preserveBanner: true });
    await loadProjectDetail(state.currentProjectId, { preserveBanner: true });
    dom.statusBanner.textContent = successMessage;
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    dom.statusBanner.textContent = `重生成失败：${message}`;
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
    await loadProjects({ preserveBanner: true });
    await loadProjectDetail(state.currentProjectId, { preserveBanner: true });
    dom.statusBanner.textContent = successMessage;
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    dom.statusBanner.textContent = `导出失败：${message}`;
    review.setReviewDisabledState(false);
  }
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
    state.currentProjectId = response.project.id;
    window.history.replaceState({}, "", `./workspace.html?project=${encodeURIComponent(response.project.id)}`);
    await loadProjects({ preserveBanner: true });
    await loadProjectDetail(response.project.id, { preserveBanner: true });
    dom.statusBanner.textContent = `项目 ${response.project.name} 已创建，可继续上传材料。`;
  } finally {
    intake.setBusyState(false);
  }
}, "创建项目时发生运行时错误"));

dom.intakeProjectSelect.addEventListener("change", wrapEvent(async () => {
  const projectId = dom.intakeProjectSelect.value;
  if (!projectId) {
    intake.renderProjectFiles([]);
    review.resetReviewPanel();
    return;
  }
  state.currentProjectId = projectId;
  window.history.replaceState({}, "", `./workspace.html?project=${encodeURIComponent(projectId)}`);
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
    await loadProjects({ preserveBanner: true });
    await loadProjectDetail(projectId, { preserveBanner: true });
    dom.statusBanner.textContent = `文件 ${response.file.file_name} 上传完成。`;
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
    await loadProjects({ preserveBanner: true });
    await loadProjectDetail(projectId, { preserveBanner: true });
    dom.statusBanner.textContent = "文件解析完成，可继续生成 Brief。";
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
  dom.statusBanner.textContent = "正在生成 Brief...";
  try {
    const response = await api.generateBrief(projectId, intake.getBriefGenerationPayload(buildUserIntentPayload()));
    intake.pushEvent(`Brief 已生成：${response.brief.presentation_goal || "未命名目标"}`);
    await loadProjects({ preserveBanner: true });
    await loadProjectDetail(projectId, { preserveBanner: true });
    dom.statusBanner.textContent = "Brief 生成完成。";
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
  intake.setBusyState(true);
  dom.statusBanner.textContent = "正在生成 Outline...";
  try {
    const briefId = state.currentProjectDetail && state.currentProjectDetail.latest_brief ? state.currentProjectDetail.latest_brief.id : null;
    const response = await api.generateOutline(projectId, intake.getOutlineGenerationPayload(briefId));
    intake.pushEvent(`Outline 已生成：${response.outline.title || "未命名大纲"}`);
    await loadProjects({ preserveBanner: true });
    await loadProjectDetail(projectId, { preserveBanner: true });
    dom.statusBanner.textContent = "Outline 生成完成。";
  } finally {
    intake.setBusyState(false);
  }
}, "生成 Outline 时发生运行时错误"));

dom.saveLlmSettingsButton.addEventListener("click", wrapEvent(async () => {
  await saveProjectLlmSettings();
}, "保存模型设置时发生运行时错误"));

dom.testLlmSettingsButton.addEventListener("click", wrapEvent(async () => {
  await testProjectLlmSettings();
}, "测试模型连接时发生运行时错误"));

dom.saveBriefButton.addEventListener("click", wrapEvent(async () => {
  await saveReviewSection("brief", {
    presentation_goal: dom.briefGoal.value.trim(),
    target_audience: dom.briefAudience.value.trim(),
    core_message: dom.briefCoreMessage.value.trim(),
    storyline: dom.briefStoryline.value.trim(),
    tone: dom.briefTone.value.trim(),
    recommended_page_count: dom.briefPageCount.value ? Number(dom.briefPageCount.value) : null,
    style_preferences: splitCommaSeparated(dom.briefStylePreferences.value),
    risks: splitLineSeparated(dom.briefRisks.value),
    assumptions: splitLineSeparated(dom.briefAssumptions.value),
  }, "Brief 已更新。");
}, "保存 Brief 时发生运行时错误"));

dom.saveOutlineButton.addEventListener("click", wrapEvent(async () => {
  await saveReviewSection("outline", {
    title: dom.outlineTitle.value.trim(),
    executive_summary: dom.outlineSummary.value.trim(),
    chapters: parseOutlineChapters(dom.outlineChapters.value),
  }, "Outline 已更新。");
}, "保存 Outline 时发生运行时错误"));

dom.saveSlidePlanButton.addEventListener("click", wrapEvent(async () => {
  await saveReviewSection("slide-plan", {
    narrative_direction: dom.slidePlanDirection.value.trim(),
    page_count: dom.slidePlanPageCount.value ? Number(dom.slidePlanPageCount.value) : null,
    slides: parseSlideEntries(dom.slidePlanSlides.value),
  }, "Slide Plan 已更新。");
}, "保存 Slide Plan 时发生运行时错误"));

dom.rerunSlidePlanButton.addEventListener("click", wrapEvent(async () => {
  const outlineId = state.currentProjectDetail && state.currentProjectDetail.latest_outline ? state.currentProjectDetail.latest_outline.id : null;
  await triggerGeneration("slide-plan:generate", { outline_id: outlineId, force_regenerate: true }, "Slide Plan 已重新生成。");
}, "重生成 Slide Plan 时发生运行时错误"));

dom.rerenderArtifactButton.addEventListener("click", wrapEvent(async () => {
  const slidePlanId = state.currentProjectDetail && state.currentProjectDetail.latest_slide_plan ? state.currentProjectDetail.latest_slide_plan.id : null;
  await triggerGeneration("artifact:generate", { slide_plan_id: slidePlanId, template_id: dom.templateSelect.value || null }, "Artifact 生成请求已提交。");
}, "生成 Artifact 时发生运行时错误"));

dom.runExportButton.addEventListener("click", wrapEvent(async () => {
  await triggerExport({ artifact_id: dom.exportArtifactId.value.trim() || null, export_format: dom.exportFormatSelect.value || "pptx" }, "导出任务已提交。");
}, "执行导出时发生运行时错误"));

[dom.templateScenarioFilter, dom.templateStyleFilter, dom.templateDensityFilter, dom.templateIndustryFilter].forEach((element) => {
  element.addEventListener("input", () => {
    review.renderTemplateOptions(dom.templateSelect.value);
  });
  element.addEventListener("change", () => {
    review.renderTemplateOptions(dom.templateSelect.value);
  });
});

dom.templateSelect.addEventListener("change", () => {
  review.renderTemplateOptions(dom.templateSelect.value);
});

dom.refreshButton.addEventListener("click", wrapEvent(async () => {
  await loadProjects();
  await loadTemplates();
}, "刷新工作区时发生运行时错误"));

dom.statusFilter.addEventListener("change", () => {
  syncIntakeProjectOptions(state.currentProjectId);
});

dom.searchInput.addEventListener("input", () => {
  syncIntakeProjectOptions(state.currentProjectId);
});

dom.apiBaseInput.addEventListener("change", wrapEvent(async () => {
  await loadProjects();
  await loadTemplates();
}, "切换 API Base 时发生运行时错误"));

await loadProjects();
await loadTemplates();