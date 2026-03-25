import { createApiClient } from "../../lib/api.js";
import { renderDashboard } from "../../features/project/dashboard.js";
import { createAppState } from "../../features/project/state.js";

const dom = {
  dashboardGrid: document.getElementById("dashboard-grid"),
  statusBanner: document.getElementById("status-banner"),
  runtimeBanner: document.getElementById("runtime-banner"),
  refreshButton: document.getElementById("refresh-button"),
  apiBaseInput: document.getElementById("api-base"),
  statusFilter: document.getElementById("status-filter"),
  searchInput: document.getElementById("search-input"),
  template: document.getElementById("project-card-template"),
  metricProjects: document.getElementById("metric-projects"),
  metricExports: document.getElementById("metric-exports"),
  metricRisks: document.getElementById("metric-risks"),
};

const state = createAppState();

function getApiBase() {
  return dom.apiBaseInput.value.trim().replace(/\/$/, "");
}

const api = createApiClient(getApiBase);

function showRuntimeError(message) {
  dom.runtimeBanner.hidden = false;
  dom.runtimeBanner.textContent = message;
}

function clearRuntimeError() {
  dom.runtimeBanner.hidden = true;
  dom.runtimeBanner.textContent = "";
}

async function loadDashboard() {
  dom.statusBanner.textContent = "正在同步 PPT 项目摘要...";
  dom.refreshButton.disabled = true;
  clearRuntimeError();

  try {
    const payload = await api.getProjects();
    state.dashboardItems = payload.projects || [];
    renderDashboard(state.dashboardItems, dom);
  } catch (error) {
    dom.dashboardGrid.innerHTML = "";
    dom.metricProjects.textContent = "0";
    dom.metricExports.textContent = "0";
    dom.metricRisks.textContent = "0";
    const message = error instanceof Error ? error.message : String(error);
    dom.statusBanner.textContent = `加载失败：${message}。请确认 API 已在 ${getApiBase()} 启动，并允许跨域访问。`;
    showRuntimeError(`项目列表加载失败：${message}`);
  } finally {
    dom.refreshButton.disabled = false;
  }
}

dom.refreshButton.addEventListener("click", () => {
  loadDashboard();
});

dom.statusFilter.addEventListener("change", () => {
  renderDashboard(state.dashboardItems, dom);
});

dom.searchInput.addEventListener("input", () => {
  renderDashboard(state.dashboardItems, dom);
});

dom.apiBaseInput.addEventListener("change", () => {
  loadDashboard();
});

loadDashboard();