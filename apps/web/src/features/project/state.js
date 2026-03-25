export function createAppState() {
  return {
    dashboardItems: [],
    currentProjectDetail: null,
    currentProjectId: "",
    availableTemplates: [],
    currentProjectFiles: [],
    selectedExportId: "",
    currentLlmSettings: null,
  };
}

export function getProjectHash(projectId) {
  return `./workspace.html?project=${encodeURIComponent(projectId)}`;
}

export function getActiveProjectId() {
  const params = new URLSearchParams(window.location.search);
  return params.get("project") || "";
}