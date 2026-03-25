from __future__ import annotations

import json
from pathlib import Path
from typing import Literal, TypedDict


class SampleBriefMetadata(TypedDict):
    audience: str
    goal: str
    style: str


class SampleSourceAsset(TypedDict):
    kind: Literal["inline-markdown", "prompt-markdown"]
    path: str


class SampleCatalogEntry(TypedDict):
    sample_id: str
    category: str
    project_name: str
    source_mode: Literal["chat", "file", "hybrid"]
    source_asset: SampleSourceAsset
    recommended_template_id: str
    summary: str
    brief: SampleBriefMetadata


class SampleCatalogService:
    def __init__(self, repo_root: Path | None = None) -> None:
        self._repo_root = repo_root or Path(__file__).resolve().parents[5]
        self._registry_path = self._repo_root / "storage/projects/sample-registry.json"

    def list_samples(self) -> list[SampleCatalogEntry]:
        payload = json.loads(self._registry_path.read_text(encoding="utf-8"))
        return payload["samples"]

    def get_sample(self, sample_id: str) -> SampleCatalogEntry:
        for sample in self.list_samples():
            if sample["sample_id"] == sample_id:
                return sample
        raise KeyError(sample_id)

    def read_source_text(self, sample: SampleCatalogEntry) -> str:
        source_path = self._repo_root / sample["source_asset"]["path"]
        return source_path.read_text(encoding="utf-8")