export async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

export function createApiClient(getApiBase) {
  return {
    async getProjects() {
      return fetchJson(`${getApiBase()}/projects`);
    },
    async getProjectDetail(projectId) {
      return fetchJson(`${getApiBase()}/projects/${encodeURIComponent(projectId)}`);
    },
    async getProjectExports(projectId, limit = 5) {
      return fetchJson(`${getApiBase()}/projects/${encodeURIComponent(projectId)}/exports?limit=${encodeURIComponent(limit)}`);
    },
    async getProjectExport(projectId, exportId) {
      return fetchJson(`${getApiBase()}/projects/${encodeURIComponent(projectId)}/exports/${encodeURIComponent(exportId)}`);
    },
    async getTemplates() {
      return fetchJson(`${getApiBase()}/projects/templates`);
    },
    async patchReviewSection(projectId, endpoint, payload) {
      return fetchJson(`${getApiBase()}/projects/${encodeURIComponent(projectId)}/${endpoint}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
    },
    async triggerGeneration(projectId, endpoint, payload) {
      return fetchJson(`${getApiBase()}/projects/${encodeURIComponent(projectId)}/${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
    },
    async triggerExport(projectId, payload) {
      return fetchJson(`${getApiBase()}/projects/${encodeURIComponent(projectId)}/export`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
    },
  };
}