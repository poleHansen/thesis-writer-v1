from enum import Enum


class ProjectStatus(str, Enum):
    CREATED = "created"
    INGESTING = "ingesting"
    PARSED = "parsed"
    ANALYZED = "analyzed"
    BRIEFING = "briefing"
    OUTLINED = "outlined"
    PLANNED = "planned"
    RENDERING = "rendering"
    FINALIZED = "finalized"
    EXPORTED = "exported"
    PARSE_FAILED = "parse_failed"
    PLAN_FAILED = "plan_failed"
    RENDER_FAILED = "render_failed"
    EXPORT_FAILED = "export_failed"


class SourceMode(str, Enum):
    CHAT = "chat"
    FILE = "file"
    MIXED = "mixed"


class ProjectFileType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    MARKDOWN = "markdown"
    URL = "url"
    IMAGE = "image"
    TXT = "txt"
    OTHER = "other"
    AUTO_DETECTED = "auto_detected"


class FileUploadStatus(str, Enum):
    UPLOADED = "uploaded"
    STORED = "stored"
    FAILED = "failed"


class ParseStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class BundleStatus(str, Enum):
    READY = "ready"
    NEEDS_REVIEW = "needs_review"
    ERROR = "error"


class ReviewStatus(str, Enum):
    DRAFT = "draft"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    REJECTED = "rejected"


class LayoutMode(str, Enum):
    COVER = "cover"
    TOC = "toc"
    SECTION = "section"
    HERO = "hero"
    TWO_COLUMN = "two_column"
    BENTO = "bento"
    CHART_FOCUS = "chart_focus"
    TIMELINE = "timeline"
    ENDING = "ending"


class RenderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"


class ExportFormat(str, Enum):
    PPTX = "pptx"
    PDF = "pdf"


class ExportStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class TaskType(str, Enum):
    INGEST = "ingest"
    PARSE = "parse"
    NORMALIZE = "normalize"
    GENERATE_BRIEF = "generate_brief"
    GENERATE_OUTLINE = "generate_outline"
    GENERATE_SLIDE_PLAN = "generate_slide_plan"
    RENDER = "render"
    FINALIZE = "finalize"
    EXPORT = "export"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
