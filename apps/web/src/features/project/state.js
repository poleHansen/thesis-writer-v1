export function createAppState() {
  return {
    dashboardItems: [],
    currentProjectDetail: null,
    currentProjectId: "",
    availableTemplates: [],
  };
}

export function getProjectHash(projectId) {
  return `#project-${encodeURIComponent(projectId)}`;
}

export function getActiveProjectId() {
  const match = window.location.hash.match(/^#project-(.+)$/);
  return match ? decodeURIComponent(match[1]) : "";
}