from __future__ import annotations

from pydantic import Field

from core_types.common import CoreModel, IdentifiedModel, JsonDict
from core_types.enums import BundleStatus, SourceMode


class UserIntent(CoreModel):
    audience: str | None = None
    scenario: str | None = None
    purpose: str | None = None
    desired_page_count: int | None = None
    style_preferences: list[str] = Field(default_factory=list)
    emphasize_points: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


class SourceChunk(CoreModel):
    chunk_id: str
    page_number: int | None = None
    heading_path: list[str] = Field(default_factory=list)
    content: str
    token_count: int = 0
    chunk_type: str = "paragraph"


class ExtractedAsset(CoreModel):
    asset_id: str
    asset_type: str
    source_file_id: str | None = None
    page_number: int | None = None
    title: str | None = None
    description: str | None = None
    storage_path: str | None = None
    metadata: JsonDict = Field(default_factory=dict)


class SourceBundle(IdentifiedModel):
    project_id: str
    source_file_ids: list[str] = Field(default_factory=list)
    source_mode: SourceMode = SourceMode.MIXED
    user_intent: UserIntent | None = None
    raw_markdown: str | None = None
    normalized_markdown: str | None = None
    page_chunks: list[SourceChunk] = Field(default_factory=list)
    tables: list[ExtractedAsset] = Field(default_factory=list)
    images: list[ExtractedAsset] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    language: str = "zh-CN"
    status: BundleStatus = BundleStatus.READY
    metadata: JsonDict = Field(default_factory=dict)
