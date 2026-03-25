export async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    let detail = "";
    try {
      const payload = await response.json();
      detail = payload && typeof payload.detail === "string" ? payload.detail : "";
    } catch {
      detail = "";
    }
    throw new Error(detail ? `HTTP ${response.status}: ${detail}` : `HTTP ${response.status}`);
  }
  return response.json();
}

export function createApiClient(getApiBase) {
  return {
    async getProjects() {
      return fetchJson(`${getApiBase()}/projects`);
    },
    async createProject(payload) {
      return fetchJson(`${getApiBase()}/projects`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
    },
    async getProjectDetail(projectId) {
      return fetchJson(`${getApiBase()}/projects/${encodeURIComponent(projectId)}`);
    },
    async getProjectLlmSettings(projectId) {
      return fetchJson(`${getApiBase()}/projects/${encodeURIComponent(projectId)}/llm-settings`);
    },
    async updateProjectLlmSettings(projectId, payload) {
      return fetchJson(`${getApiBase()}/projects/${encodeURIComponent(projectId)}/llm-settings`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
    },
    async testProjectLlmSettings(projectId) {
      return fetchJson(`${getApiBase()}/projects/${encodeURIComponent(projectId)}/llm-settings:test`, {
        method: "POST",
      });
    },
    async getProjectFiles(projectId) {
      return fetchJson(`${getApiBase()}/projects/${encodeURIComponent(projectId)}/files`);
    },
    async uploadProjectFile(projectId, payload) {
      return fetchJson(`${getApiBase()}/projects/${encodeURIComponent(projectId)}/files:upload`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
    },
    async parseProjectFiles(projectId, payload) {
      return fetchJson(`${getApiBase()}/projects/${encodeURIComponent(projectId)}/files:parse`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
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
    async generateBrief(projectId, payload) {
      return fetchJson(`${getApiBase()}/projects/${encodeURIComponent(projectId)}/brief:generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
    },
    async generateOutline(projectId, payload) {
      return fetchJson(`${getApiBase()}/projects/${encodeURIComponent(projectId)}/outline:generate`, {
        method: "POST",
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