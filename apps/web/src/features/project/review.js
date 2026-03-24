import {
  formatDate,
  formatPathBasename,
  formatOutlineChapters,
  formatPreviewLabel,
  formatSlideEntries,
  joinLineSeparated,
  parseOutlineChapters,
  parseSlideEntries,
  splitCommaSeparated,
  splitLineSeparated,
} from "../../lib/formatters.js";

export function createReviewController(dom, state) {
  function normalizePreviewPath(pathValue) {
    if (!pathValue || typeof pathValue !== "string") {
      return "";
    }
    if (pathValue.startsWith("builtin://templates/")) {
      return pathValue.replace("builtin://templates/", "./templates/builtin/");
    }
    return pathValue;
  }

  function getTemplateFilterOptions(key) {
    const values = new Set();
    state.availableTemplates.forEach((templateItem) => {
      const source = key === "density"
        ? [templateItem.density_range]
        : key === "industry"
          ? [
              ...(templateItem.metadata && Array.isArray(templateItem.metadata.default_for) ? templateItem.metadata.default_for : []),
              ...(templateItem.metadata && templateItem.metadata.visual_direction ? [templateItem.metadata.visual_direction] : []),
            ]
          : key === "scenario"
            ? templateItem.scenario_tags || []
            : templateItem.style_tags || [];
      source.forEach((value) => {
        if (typeof value === "string" && value.trim()) {
          values.add(value.trim());
        }
      });
    });
    return Array.from(values).sort((left, right) => left.localeCompare(right));
  }

  function renderTemplateFilterOptions() {
    const filterDefinitions = [
      [dom.templateScenarioFilter, "scenario", "全部场景"],
      [dom.templateStyleFilter, "style", "全部风格"],
      [dom.templateDensityFilter, "density", "全部密度"],
    ];

    filterDefinitions.forEach(([element, key, defaultLabel]) => {
      const currentValue = element.value;
      element.innerHTML = "";
      const defaultOption = document.createElement("option");
      defaultOption.value = "";
      defaultOption.textContent = defaultLabel;
      element.appendChild(defaultOption);

      getTemplateFilterOptions(key).forEach((value) => {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value;
        element.appendChild(option);
      });

      element.value = currentValue || "";
    });
  }

  function filterTemplates() {
    const scenario = dom.templateScenarioFilter.value.trim().toLowerCase();
    const style = dom.templateStyleFilter.value.trim().toLowerCase();
    const density = dom.templateDensityFilter.value.trim().toLowerCase();
    const industry = dom.templateIndustryFilter.value.trim().toLowerCase();

    return state.availableTemplates.filter((templateItem) => {
      const scenarioTokens = (templateItem.scenario_tags || []).map((item) => item.toLowerCase());
      const styleTokens = (templateItem.style_tags || []).map((item) => item.toLowerCase());
      const densityValue = (templateItem.density_range || "").toLowerCase();
      const industryTokens = [
        ...(templateItem.metadata && Array.isArray(templateItem.metadata.default_for) ? templateItem.metadata.default_for : []),
        ...(templateItem.metadata && templateItem.metadata.visual_direction ? [templateItem.metadata.visual_direction] : []),
        templateItem.template_id,
        templateItem.name,
      ].map((item) => String(item).toLowerCase());

      if (scenario && !scenarioTokens.includes(scenario)) {
        return false;
      }
      if (style && !styleTokens.includes(style)) {
        return false;
      }
      if (density && densityValue !== density) {
        return false;
      }
      if (industry && !industryTokens.some((token) => token.includes(industry))) {
        return false;
      }
      return true;
    });
  }

  function renderTemplatePreviewCards(filteredTemplates, selectedTemplateId) {
    dom.templatePreviewGrid.innerHTML = "";

    if (!filteredTemplates.length) {
      const empty = document.createElement("p");
      empty.className = "empty-line template-preview-empty";
      empty.textContent = "当前筛选条件下暂无模板预览。";
      dom.templatePreviewGrid.appendChild(empty);
      return;
    }

    filteredTemplates.forEach((templateItem) => {
      const card = document.createElement("button");
      card.type = "button";
      card.className = "template-preview-card";
      if (templateItem.template_id === selectedTemplateId) {
        card.dataset.selected = "true";
      }
      card.addEventListener("click", () => {
        dom.templateSelect.value = templateItem.template_id;
        renderTemplatePreviewCards(filteredTemplates, templateItem.template_id);
      });

      const visual = document.createElement("div");
      visual.className = "template-preview-visual";
      const previewPath = normalizePreviewPath(templateItem.preview_image_path);
      if (previewPath) {
        const image = document.createElement("img");
        image.className = "template-preview-image";
        image.src = previewPath;
        image.alt = `${templateItem.name} 模板预览`;
        visual.appendChild(image);
      } else {
        const fallback = document.createElement("div");
        fallback.className = "template-preview-fallback";
        fallback.textContent = "无预览图";
        visual.appendChild(fallback);
      }
      card.appendChild(visual);

      const body = document.createElement("div");
      body.className = "template-preview-body";

      const header = document.createElement("div");
      header.className = "template-preview-header";
      header.innerHTML = `<strong>${templateItem.name}</strong><span>${templateItem.template_id}</span>`;
      body.appendChild(header);

      const description = document.createElement("p");
      description.textContent = (templateItem.metadata && templateItem.metadata.visual_direction) || templateItem.density_range || "未标注视觉方向";
      body.appendChild(description);

      const tags = document.createElement("div");
      tags.className = "template-preview-tags";
      [...(templateItem.scenario_tags || []), ...(templateItem.style_tags || [])].slice(0, 4).forEach((value) => {
        const tag = document.createElement("span");
        tag.textContent = value;
        tags.appendChild(tag);
      });
      body.appendChild(tags);

      card.appendChild(body);
      dom.templatePreviewGrid.appendChild(card);
    });
  }

  function updateTemplateFilterHint(filteredTemplates) {
    if (!state.availableTemplates.length) {
      dom.templateFilterHint.textContent = "暂无可用模板。";
      return;
    }
    if (!filteredTemplates.length) {
      dom.templateFilterHint.textContent = "当前筛选条件下没有匹配模板，请放宽筛选条件。";
      return;
    }

    const activeFilters = [
      dom.templateScenarioFilter.value,
      dom.templateStyleFilter.value,
      dom.templateDensityFilter.value,
      dom.templateIndustryFilter.value.trim(),
    ].filter(Boolean);

    if (!activeFilters.length) {
      dom.templateFilterHint.textContent = `当前显示全部模板，共 ${filteredTemplates.length} 个。`;
      return;
    }

    dom.templateFilterHint.textContent = `当前命中 ${filteredTemplates.length} 个模板，筛选条件：${activeFilters.join(" / ")}。`;
  }

  function setReviewDisabledState(disabled) {
    [
      dom.briefGoal,
      dom.briefAudience,
      dom.briefCoreMessage,
      dom.briefStoryline,
      dom.briefTone,
      dom.briefPageCount,
      dom.briefStylePreferences,
      dom.briefRisks,
      dom.briefAssumptions,
      dom.outlineTitle,
      dom.outlineSummary,
      dom.outlineChapters,
      dom.slidePlanDirection,
      dom.slidePlanPageCount,
      dom.slidePlanSlides,
      dom.templateScenarioFilter,
      dom.templateStyleFilter,
      dom.templateDensityFilter,
      dom.templateIndustryFilter,
      dom.templateSelect,
      dom.exportFormatSelect,
      dom.exportArtifactId,
      dom.saveBriefButton,
      dom.saveOutlineButton,
      dom.saveSlidePlanButton,
      dom.rerunSlidePlanButton,
      dom.rerenderArtifactButton,
      dom.runExportButton,
    ].forEach((element) => {
      element.disabled = disabled;
    });
  }

  function renderTemplateOptions(selectedTemplateId) {
    renderTemplateFilterOptions();
    const filteredTemplates = filterTemplates();
    dom.templateSelect.innerHTML = "";

    const autoOption = document.createElement("option");
    autoOption.value = "";
    autoOption.textContent = "自动选择模板";
    dom.templateSelect.appendChild(autoOption);

    filteredTemplates.forEach((templateItem) => {
      const option = document.createElement("option");
      option.value = templateItem.template_id;
      option.textContent = `${templateItem.name} (${templateItem.template_id})`;
      dom.templateSelect.appendChild(option);
    });

    const hasSelectedTemplate = filteredTemplates.some((templateItem) => templateItem.template_id === selectedTemplateId);
    dom.templateSelect.value = hasSelectedTemplate ? selectedTemplateId || "" : "";
    updateTemplateFilterHint(filteredTemplates);
    renderTemplatePreviewCards(filteredTemplates, dom.templateSelect.value);
  }

  function clearReviewFields() {
    [
      dom.briefGoal,
      dom.briefAudience,
      dom.briefCoreMessage,
      dom.briefStoryline,
      dom.briefTone,
      dom.briefPageCount,
      dom.briefStylePreferences,
      dom.briefRisks,
      dom.briefAssumptions,
      dom.outlineTitle,
      dom.outlineSummary,
      dom.outlineChapters,
      dom.slidePlanDirection,
      dom.slidePlanPageCount,
      dom.slidePlanSlides,
      dom.templateIndustryFilter,
      dom.exportArtifactId,
    ].forEach((element) => {
      element.value = "";
    });
    dom.templateScenarioFilter.value = "";
    dom.templateStyleFilter.value = "";
    dom.templateDensityFilter.value = "";
    dom.templatePreviewGrid.innerHTML = "";
    dom.exportFormatSelect.value = "pptx";
  }

  function setReviewMode(hasSelection) {
    dom.reviewEmptyState.hidden = hasSelection;
    dom.reviewContent.hidden = !hasSelection;
  }

  function renderMetaChips(detail) {
    dom.reviewMeta.innerHTML = "";
    const chipValues = [
      ["Source Mode", detail.project.source_mode],
      ["Updated", formatDate(detail.project.updated_at)],
      ["Tags", (detail.project.tags || []).join(" / ") || "-"],
      ["Preview PDF", detail.latest_artifact && detail.latest_artifact.preview_pdf_path ? detail.latest_artifact.preview_pdf_path : "-"],
    ];
    chipValues.forEach(([label, value]) => {
      const chip = document.createElement("div");
      chip.className = "meta-chip";
      chip.innerHTML = `<span>${label}</span><strong>${value || "-"}</strong>`;
      dom.reviewMeta.appendChild(chip);
    });
  }

  function renderArtifactSummary(artifact, exportJob) {
    dom.artifactSummary.innerHTML = "";
    const items = [];
    if (artifact) {
      items.push(["Render Status", artifact.render_status || "-"]);
      items.push(["Template", artifact.metadata && artifact.metadata.template_name ? artifact.metadata.template_name : artifact.template_id || "-"]);
      items.push(["Preview PDF", artifact.preview_pdf_path || "-"]);
      items.push(["SVG Files", Array.isArray(artifact.generated_svg_files) ? String(artifact.generated_svg_files.length) : "0"]);
      items.push(["Validation", artifact.validation_summary ? JSON.stringify(artifact.validation_summary) : "-"]);
      items.push(["Finalization", artifact.finalization_summary ? JSON.stringify(artifact.finalization_summary) : "-"]);
    }
    if (exportJob) {
      items.push(["Export Status", `${exportJob.status || "-"} / ${exportJob.export_format || "-"}`]);
      items.push(["Export File", exportJob.output_path || "-"]);
    }

    if (!items.length) {
      const empty = document.createElement("p");
      empty.className = "empty-line";
      empty.textContent = "尚未生成 artifact 或 export，可先在后端流水线中完成渲染。";
      dom.artifactSummary.appendChild(empty);
      return;
    }

    items.forEach(([label, value]) => {
      const row = document.createElement("div");
      row.className = "artifact-row";
      row.innerHTML = `<span>${label}</span><strong>${value}</strong>`;
      dom.artifactSummary.appendChild(row);
    });

    if (exportJob && exportJob.output_path) {
      const links = document.createElement("div");
      links.className = "artifact-link-group";

      const outputLink = document.createElement("a");
      outputLink.className = "artifact-link";
      outputLink.href = exportJob.output_path;
      outputLink.target = "_blank";
      outputLink.rel = "noreferrer";
      outputLink.textContent = `打开导出文件: ${formatPathBasename(exportJob.output_path)}`;
      links.appendChild(outputLink);

      const archiveManifestPath = exportJob.metadata && exportJob.metadata.archive_manifest_path;
      if (archiveManifestPath) {
        const manifestLink = document.createElement("a");
        manifestLink.className = "artifact-link";
        manifestLink.href = archiveManifestPath;
        manifestLink.target = "_blank";
        manifestLink.rel = "noreferrer";
        manifestLink.textContent = `归档清单: ${formatPathBasename(archiveManifestPath)}`;
        links.appendChild(manifestLink);
      }

      const exportLogPath = exportJob.metadata && exportJob.metadata.export_log_path;
      if (exportLogPath) {
        const logLink = document.createElement("a");
        logLink.className = "artifact-link";
        logLink.href = exportLogPath;
        logLink.target = "_blank";
        logLink.rel = "noreferrer";
        logLink.textContent = `导出日志: ${formatPathBasename(exportLogPath)}`;
        links.appendChild(logLink);
      }

      dom.artifactSummary.appendChild(links);
    }

    if (exportJob && exportJob.run_id) {
      const exportMeta = document.createElement("div");
      exportMeta.className = "artifact-export-meta";
      exportMeta.innerHTML = `
        <span>Export Run</span>
        <strong>${exportJob.run_id}</strong>
        <span>Updated</span>
        <strong>${formatDate(exportJob.updated_at || exportJob.created_at)}</strong>
      `;
      dom.artifactSummary.appendChild(exportMeta);
    }
  }

  function renderArtifactPreview(artifact) {
    dom.artifactPreviewGrid.innerHTML = "";

    if (!artifact) {
      const empty = document.createElement("p");
      empty.className = "empty-line";
      empty.textContent = "暂无可预览的 artifact。";
      dom.artifactPreviewGrid.appendChild(empty);
      return;
    }

    const previewPaths = [];
    if (Array.isArray(artifact.preview_image_paths) && artifact.preview_image_paths.length) {
      previewPaths.push(...artifact.preview_image_paths);
    } else if (Array.isArray(artifact.generated_svg_files) && artifact.generated_svg_files.length) {
      previewPaths.push(...artifact.generated_svg_files);
    } else if (artifact.metadata && Array.isArray(artifact.metadata.generated_svg_files)) {
      previewPaths.push(...artifact.metadata.generated_svg_files);
    }

    if (!previewPaths.length) {
      const empty = document.createElement("p");
      empty.className = "empty-line";
      empty.textContent = "当前 artifact 尚未暴露页级预览文件。";
      dom.artifactPreviewGrid.appendChild(empty);
      return;
    }

    previewPaths.forEach((pathValue, index) => {
      const card = document.createElement("a");
      card.className = "artifact-preview-card";
      card.href = pathValue;
      card.target = "_blank";
      card.rel = "noreferrer";

      const frame = document.createElement("div");
      frame.className = "artifact-preview-frame";

      const previewObject = document.createElement("object");
      previewObject.className = "artifact-preview-object";
      previewObject.data = pathValue;
      previewObject.type = "image/svg+xml";
      previewObject.setAttribute("aria-label", `SVG preview ${index + 1}`);

      const fallback = document.createElement("span");
      fallback.className = "artifact-preview-fallback";
      fallback.textContent = "预览加载失败，点击卡片打开原文件。";
      previewObject.appendChild(fallback);
      frame.appendChild(previewObject);
      card.appendChild(frame);

      const meta = document.createElement("div");
      meta.className = "artifact-preview-meta";
      meta.innerHTML = `<strong>${formatPreviewLabel(pathValue, index + 1)}</strong><span>${formatPathBasename(pathValue)}</span>`;
      card.appendChild(meta);

      dom.artifactPreviewGrid.appendChild(card);
    });
  }

  function renderExportDelta(selectedExport, latestExport) {
    dom.exportDelta.innerHTML = "";

    if (!selectedExport) {
      const empty = document.createElement("p");
      empty.className = "empty-line";
      empty.textContent = "暂无可比较的导出版本。";
      dom.exportDelta.appendChild(empty);
      return;
    }

    if (!latestExport || latestExport.id === selectedExport.id) {
      const same = document.createElement("p");
      same.className = "empty-line";
      same.textContent = "当前查看的是最新导出版本。";
      dom.exportDelta.appendChild(same);
      return;
    }

    const rows = [
      ["Compared To", latestExport.run_id || "-"],
      ["Format", selectedExport.export_format === latestExport.export_format ? `无变化 (${selectedExport.export_format || "-"})` : `${latestExport.export_format || "-"} -> ${selectedExport.export_format || "-"}`],
      ["Status", selectedExport.status === latestExport.status ? `无变化 (${selectedExport.status || "-"})` : `${latestExport.status || "-"} -> ${selectedExport.status || "-"}`],
      ["Selected Time", formatDate(selectedExport.updated_at || selectedExport.created_at)],
      ["Latest Time", formatDate(latestExport.updated_at || latestExport.created_at)],
    ];

    const selectedOutput = selectedExport.output_path ? formatPathBasename(selectedExport.output_path) : "-";
    const latestOutput = latestExport.output_path ? formatPathBasename(latestExport.output_path) : "-";
    rows.push(["Output", selectedOutput === latestOutput ? selectedOutput : `${latestOutput} -> ${selectedOutput}`]);

    rows.forEach(([label, value]) => {
      const row = document.createElement("div");
      row.className = "artifact-row";
      row.innerHTML = `<span>${label}</span><strong>${value}</strong>`;
      dom.exportDelta.appendChild(row);
    });
  }

  function renderExportHistory(exports, options = {}) {
    const { selectedExportId = "", onSelectExport = null } = options;
    dom.exportHistory.innerHTML = "";

    if (!exports || !exports.length) {
      const empty = document.createElement("p");
      empty.className = "empty-line";
      empty.textContent = "暂无导出历史。";
      dom.exportHistory.appendChild(empty);
      return;
    }

    exports.forEach((exportJob) => {
      const item = document.createElement("button");
      item.type = "button";
      item.className = "export-history-item";
      if (selectedExportId && exportJob.id === selectedExportId) {
        item.dataset.selected = "true";
      }
      if (typeof onSelectExport === "function") {
        item.addEventListener("click", () => onSelectExport(exportJob.id));
      }

      const header = document.createElement("div");
      header.className = "export-history-header";
      header.innerHTML = `<strong>${exportJob.run_id || "-"}</strong><span>${exportJob.export_format || "-"} / ${exportJob.status || "-"}</span>`;
      item.appendChild(header);

      const meta = document.createElement("div");
      meta.className = "export-history-meta";
      meta.innerHTML = `<span>更新时间</span><strong>${formatDate(exportJob.updated_at || exportJob.created_at)}</strong>`;
      item.appendChild(meta);

      const links = document.createElement("div");
      links.className = "artifact-link-group";

      if (exportJob.output_path) {
        const outputLink = document.createElement("a");
        outputLink.className = "artifact-link";
        outputLink.href = exportJob.output_path;
        outputLink.target = "_blank";
        outputLink.rel = "noreferrer";
        outputLink.textContent = formatPathBasename(exportJob.output_path);
        outputLink.addEventListener("click", (event) => event.stopPropagation());
        links.appendChild(outputLink);
      }

      const archiveManifestPath = exportJob.metadata && exportJob.metadata.archive_manifest_path;
      if (archiveManifestPath) {
        const manifestLink = document.createElement("a");
        manifestLink.className = "artifact-link";
        manifestLink.href = archiveManifestPath;
        manifestLink.target = "_blank";
        manifestLink.rel = "noreferrer";
        manifestLink.textContent = formatPathBasename(archiveManifestPath);
        manifestLink.addEventListener("click", (event) => event.stopPropagation());
        links.appendChild(manifestLink);
      }

      const exportLogPath = exportJob.metadata && exportJob.metadata.export_log_path;
      if (exportLogPath) {
        const logLink = document.createElement("a");
        logLink.className = "artifact-link";
        logLink.href = exportLogPath;
        logLink.target = "_blank";
        logLink.rel = "noreferrer";
        logLink.textContent = formatPathBasename(exportLogPath);
        logLink.addEventListener("click", (event) => event.stopPropagation());
        links.appendChild(logLink);
      }

      item.appendChild(links);
      dom.exportHistory.appendChild(item);
    });
  }

  function populateReview(detail) {
    state.currentProjectDetail = detail;
    state.currentProjectId = detail.project.id;
    setReviewMode(true);
    dom.reviewKicker.textContent = `Project ${detail.project.id}`;
    dom.reviewTitle.textContent = detail.project.name;
    dom.reviewStatus.textContent = detail.project.status;
    dom.reviewStatus.dataset.status = detail.project.status;
    dom.reviewDescription.textContent = detail.project.description || "暂无项目描述。";
    renderMetaChips(detail);

    const brief = detail.latest_brief;
    dom.briefGoal.value = brief ? brief.presentation_goal || "" : "";
    dom.briefAudience.value = brief ? brief.target_audience || "" : "";
    dom.briefCoreMessage.value = brief ? brief.core_message || "" : "";
    dom.briefStoryline.value = brief ? brief.storyline || "" : "";
    dom.briefTone.value = brief ? brief.tone || "" : "";
    dom.briefPageCount.value = brief && brief.recommended_page_count ? String(brief.recommended_page_count) : "";
    dom.briefStylePreferences.value = brief && Array.isArray(brief.style_preferences) ? brief.style_preferences.join(", ") : "";
    dom.briefRisks.value = brief ? joinLineSeparated(brief.risks) : "";
    dom.briefAssumptions.value = brief ? joinLineSeparated(brief.assumptions) : "";

    const outline = detail.latest_outline;
    dom.outlineTitle.value = outline ? outline.title || "" : "";
    dom.outlineSummary.value = outline ? outline.summary || "" : "";
    dom.outlineChapters.value = outline ? formatOutlineChapters(outline.chapters) : "";

    const slidePlan = detail.latest_slide_plan;
    dom.slidePlanDirection.value = slidePlan ? slidePlan.design_direction || "" : "";
    dom.slidePlanPageCount.value = slidePlan && typeof slidePlan.page_count === "number" ? String(slidePlan.page_count) : "";
    dom.slidePlanSlides.value = slidePlan ? formatSlideEntries(slidePlan.slides) : "";

    const activeTemplateId = detail.latest_artifact
      ? detail.latest_artifact.metadata && detail.latest_artifact.metadata.template_id
        ? detail.latest_artifact.metadata.template_id
        : detail.latest_artifact.template_id || ""
      : slidePlan && slidePlan.metadata
        ? slidePlan.metadata.preferred_template_id || ""
        : "";
    renderTemplateOptions(activeTemplateId);

    renderArtifactSummary(detail.latest_artifact, detail.latest_export);
    renderArtifactPreview(detail.latest_artifact);
    renderExportDelta(detail.latest_export, detail.latest_export);
    dom.exportArtifactId.value = detail.latest_artifact ? detail.latest_artifact.id || "" : "";
    dom.exportFormatSelect.value = detail.latest_export && detail.latest_export.export_format ? detail.latest_export.export_format : "pptx";
    setReviewDisabledState(false);
  }

  function resetReviewPanel(message) {
    state.currentProjectDetail = null;
    state.currentProjectId = "";
    state.selectedExportId = "";
    clearReviewFields();
    dom.reviewMeta.innerHTML = "";
    dom.artifactSummary.innerHTML = "";
    dom.artifactPreviewGrid.innerHTML = "";
    dom.exportDelta.innerHTML = "";
    dom.exportHistory.innerHTML = "";
    setReviewMode(false);
    if (message) {
      dom.reviewEmptyMessage.textContent = message;
    }
    setReviewDisabledState(true);
  }

  function getBriefPayload() {
    const briefId = state.currentProjectDetail && state.currentProjectDetail.latest_brief ? state.currentProjectDetail.latest_brief.id : null;
    return {
      brief_id: briefId,
      presentation_goal: dom.briefGoal.value.trim() || null,
      target_audience: dom.briefAudience.value.trim() || null,
      core_message: dom.briefCoreMessage.value.trim() || null,
      storyline: dom.briefStoryline.value.trim() || null,
      tone: dom.briefTone.value.trim() || null,
      recommended_page_count: dom.briefPageCount.value ? Number(dom.briefPageCount.value) : null,
      style_preferences: splitCommaSeparated(dom.briefStylePreferences.value),
      risks: splitLineSeparated(dom.briefRisks.value),
      assumptions: splitLineSeparated(dom.briefAssumptions.value),
    };
  }

  function getOutlinePayload() {
    const outlineId = state.currentProjectDetail && state.currentProjectDetail.latest_outline ? state.currentProjectDetail.latest_outline.id : null;
    return {
      outline_id: outlineId,
      title: dom.outlineTitle.value.trim() || null,
      summary: dom.outlineSummary.value.trim() || null,
      chapters: parseOutlineChapters(dom.outlineChapters.value),
    };
  }

  function getSlidePlanPayload() {
    const slidePlanId = state.currentProjectDetail && state.currentProjectDetail.latest_slide_plan ? state.currentProjectDetail.latest_slide_plan.id : null;
    return {
      slide_plan_id: slidePlanId,
      design_direction: dom.slidePlanDirection.value.trim() || null,
      page_count: dom.slidePlanPageCount.value ? Number(dom.slidePlanPageCount.value) : null,
      slides: parseSlideEntries(dom.slidePlanSlides.value),
    };
  }

  function getRegenerateSlidePlanPayload() {
    const outlineId = state.currentProjectDetail && state.currentProjectDetail.latest_outline ? state.currentProjectDetail.latest_outline.id : null;
    return {
      outline_id: outlineId,
      preferred_template_id: dom.templateSelect.value || null,
      force_regenerate: true,
    };
  }

  function getRerenderArtifactPayload() {
    const slidePlanId = state.currentProjectDetail && state.currentProjectDetail.latest_slide_plan ? state.currentProjectDetail.latest_slide_plan.id : null;
    return {
      slide_plan_id: slidePlanId,
      template_id: dom.templateSelect.value || null,
    };
  }

  function getExportPayload() {
    return {
      artifact_id: dom.exportArtifactId.value.trim() || null,
      export_format: dom.exportFormatSelect.value || "pptx",
    };
  }

  return {
    setReviewDisabledState,
    renderTemplateOptions,
    populateReview,
    renderArtifactSummary,
    renderArtifactPreview,
    renderExportDelta,
    resetReviewPanel,
    renderExportHistory,
    renderTemplateFilterOptions,
    getBriefPayload,
    getOutlinePayload,
    getSlidePlanPayload,
    getRegenerateSlidePlanPayload,
    getRerenderArtifactPayload,
    getExportPayload,
  };
}