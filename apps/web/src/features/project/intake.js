import { splitCommaSeparated } from "../../lib/formatters.js";

function readFileAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = typeof reader.result === "string" ? reader.result : "";
      const [, base64 = ""] = result.split(",");
      resolve(base64);
    };
    reader.onerror = () => reject(new Error("无法读取本地文件"));
    reader.readAsDataURL(file);
  });
}

function encodeInlineContent(value) {
  return btoa(unescape(encodeURIComponent(value)));
}

function inferMimeType(fileType, localFile) {
  if (localFile && localFile.type) {
    return localFile.type;
  }

  const mimeMap = {
    pdf: "application/pdf",
    docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    markdown: "text/markdown",
    txt: "text/plain",
    url: "text/uri-list",
    image: "image/*",
  };
  return mimeMap[fileType] || "application/octet-stream";
}

export function createIntakeController(dom, state) {
  function setBusyState(isBusy) {
    [
      dom.intakeProjectName,
      dom.intakeSourceMode,
      dom.intakeProjectDescription,
      dom.intakeProjectTags,
      dom.createProjectButton,
      dom.intakeProjectSelect,
      dom.intakeFileType,
      dom.intakeLocalFile,
      dom.intakeInlineContent,
      dom.intakeInlineFileName,
      dom.intakeMimeType,
      dom.uploadFileButton,
      dom.intakeFileSelect,
      dom.intakeUserIntent,
      dom.intakeRebuildBundle,
      dom.intakeForceBrief,
      dom.intakeForceOutline,
      dom.parseFilesButton,
      dom.generateBriefButton,
      dom.generateOutlineButton,
    ].forEach((element) => {
      element.disabled = isBusy;
    });
  }

  function renderProjectOptions(items, selectedProjectId = "") {
    dom.intakeProjectSelect.innerHTML = "";
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = items.length ? "选择一个项目继续 intake" : "先创建或选择一个项目";
    dom.intakeProjectSelect.appendChild(placeholder);

    items.forEach((item) => {
      const option = document.createElement("option");
      option.value = item.project.id;
      option.textContent = `${item.project.name} (${item.project.status})`;
      dom.intakeProjectSelect.appendChild(option);
    });

    dom.intakeProjectSelect.value = selectedProjectId || "";
  }

  function renderProjectFiles(files) {
    dom.intakeFileSelect.innerHTML = "";

    if (!files.length) {
      const option = document.createElement("option");
      option.value = "";
      option.textContent = "当前项目暂无已上传文件";
      dom.intakeFileSelect.appendChild(option);
      return;
    }

    files.forEach((file) => {
      const option = document.createElement("option");
      option.value = file.id;
      option.textContent = `${file.file_name} · ${file.file_type} · ${file.parse_status || "pending"}`;
      dom.intakeFileSelect.appendChild(option);
    });
  }

  function pushEvent(message) {
    const event = document.createElement("div");
    event.className = "intake-event";
    event.textContent = message;
    dom.intakeStream.prepend(event);
    while (dom.intakeStream.children.length > 6) {
      dom.intakeStream.removeChild(dom.intakeStream.lastElementChild);
    }
  }

  function getCreateProjectPayload() {
    const name = dom.intakeProjectName.value.trim();
    if (!name) {
      return null;
    }

    return {
      name,
      description: dom.intakeProjectDescription.value.trim() || null,
      source_mode: dom.intakeSourceMode.value || "mixed",
      tags: splitCommaSeparated(dom.intakeProjectTags.value),
    };
  }

  async function getUploadPayload() {
    const localFile = dom.intakeLocalFile.files && dom.intakeLocalFile.files[0] ? dom.intakeLocalFile.files[0] : null;
    const inlineContent = dom.intakeInlineContent.value.trim();
    const fileType = dom.intakeFileType.value || "auto_detected";
    const mimeType = dom.intakeMimeType.value.trim() || inferMimeType(fileType, localFile);

    if (localFile) {
      return {
        file_name: localFile.name,
        content_base64: await readFileAsBase64(localFile),
        file_type: fileType,
        mime_type: mimeType,
        metadata: {
          source: "browser_file_upload",
          size_bytes: localFile.size,
        },
      };
    }

    if (!inlineContent) {
      return null;
    }

    return {
      file_name: dom.intakeInlineFileName.value.trim() || (fileType === "url" ? "source.url" : "source.md"),
      content_base64: encodeInlineContent(inlineContent),
      file_type: fileType,
      mime_type: mimeType,
      metadata: {
        source: "browser_inline_content",
      },
    };
  }

  function getSelectedFileIds() {
    return Array.from(dom.intakeFileSelect.selectedOptions)
      .map((option) => option.value)
      .filter(Boolean);
  }

  function getParsePayload(userIntent) {
    const fileIds = getSelectedFileIds();
    return {
      file_ids: fileIds.length ? fileIds : null,
      rebuild_bundle: dom.intakeRebuildBundle.checked,
      user_intent: userIntent,
    };
  }

  function getBriefGenerationPayload(userIntent) {
    return {
      force_regenerate: dom.intakeForceBrief.checked,
      user_intent_override: userIntent,
    };
  }

  function getOutlineGenerationPayload(briefId) {
    return {
      brief_id: briefId || null,
      force_regenerate: dom.intakeForceOutline.checked,
    };
  }

  return {
    setBusyState,
    renderProjectOptions,
    renderProjectFiles,
    pushEvent,
    getCreateProjectPayload,
    getUploadPayload,
    getParsePayload,
    getBriefGenerationPayload,
    getOutlineGenerationPayload,
  };
}