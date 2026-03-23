from __future__ import annotations

from pydantic import BaseModel, Field


class ParsedImageAsset(BaseModel):
    asset_id: str
    title: str | None = None
    description: str | None = None
    source_path: str | None = None


class ParsedTableAsset(BaseModel):
    asset_id: str
    title: str | None = None
    markdown: str | None = None


class ParsedDocument(BaseModel):
    title: str | None = None
    raw_text: str
    markdown: str
    page_chunks: list[str] = Field(default_factory=list)
    images: list[ParsedImageAsset] = Field(default_factory=list)
    tables: list[ParsedTableAsset] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
