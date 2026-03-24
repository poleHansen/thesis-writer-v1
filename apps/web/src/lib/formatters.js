export function formatDate(value) {
  if (!value) {
    return "-";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function splitCommaSeparated(value) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function splitLineSeparated(value) {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function joinLineSeparated(items) {
  return (items || []).filter(Boolean).join("\n");
}

export function formatOutlineChapters(chapters) {
  return (chapters || [])
    .map((chapter) => {
      const title = chapter.title || chapter.heading || "Untitled Chapter";
      const objective = chapter.objective || chapter.goal || "";
      const keyPoints = Array.isArray(chapter.key_points) ? chapter.key_points.join(", ") : "";
      return [title, objective, keyPoints].filter(Boolean).join(" | ");
    })
    .join("\n");
}

export function parseOutlineChapters(value) {
  return splitLineSeparated(value).map((line, index) => {
    const [title, objective, keyPoints] = line.split("|").map((part) => part.trim());
    return {
      sequence: index + 1,
      title: title || `Chapter ${index + 1}`,
      objective: objective || "",
      key_points: keyPoints ? keyPoints.split(",").map((item) => item.trim()).filter(Boolean) : [],
    };
  });
}

export function formatSlideEntries(slides) {
  return (slides || [])
    .map((slide, index) => {
      const title = slide.title || `Slide ${index + 1}`;
      const intent = slide.intent || slide.objective || "";
      const layout = slide.layout || slide.layout_hint || slide.slide_type || "";
      return [title, intent, layout].filter(Boolean).join(" | ");
    })
    .join("\n");
}

export function parseSlideEntries(value) {
  return splitLineSeparated(value).map((line, index) => {
    const [title, intent, layout] = line.split("|").map((part) => part.trim());
    return {
      sequence: index + 1,
      title: title || `Slide ${index + 1}`,
      intent: intent || "",
      layout: layout || "",
    };
  });
}

export function formatPathBasename(value) {
  if (!value) {
    return "-";
  }

  const normalized = String(value).replace(/\\/g, "/");
  const segments = normalized.split("/").filter(Boolean);
  return segments.length ? segments[segments.length - 1] : normalized;
}

export function formatPreviewLabel(value, index) {
  const baseName = formatPathBasename(value);
  const matched = /slide-(\d+)/i.exec(baseName);
  if (matched) {
    return `Slide ${matched[1]}`;
  }
  return `Preview ${index}`;
}