from __future__ import annotations

import re
from dataclasses import dataclass, field

from ingestion.models import ParsedDocument


@dataclass
class NormalizedDocument:
    normalized_markdown: str
    deduplicated_sections: list[str] = field(default_factory=list)
    removed_sections: list[str] = field(default_factory=list)


class DocumentNormalizer:
    _noise_patterns = [
        re.compile(pattern, flags=re.IGNORECASE)
        for pattern in [
            r'^navigation$',
            r'^menu$',
            r'^table of contents$',
            r'^copyright.*$',
            r'^all rights reserved.*$',
            r'^page\s+\d+(\s+of\s+\d+)?$',
            r'^第\s*\d+\s*页$',
        ]
    ]

    def normalize_documents(self, documents: list[ParsedDocument]) -> NormalizedDocument:
        sections: list[str] = []
        deduplicated_sections: list[str] = []
        removed_sections: list[str] = []
        seen_blocks: set[str] = set()

        for document in documents:
            title = self._clean_text(document.title or "Untitled")
            body = self._normalize_body(document.markdown, removed_sections, seen_blocks, deduplicated_sections)
            if not body:
                continue
            asset_blocks = self._build_asset_blocks(document)
            section_parts = [f"# {title}", body]
            if asset_blocks:
                section_parts.append(asset_blocks)
            sections.append("\n\n".join(part for part in section_parts if part))

        return NormalizedDocument(
            normalized_markdown="\n\n".join(sections),
            deduplicated_sections=deduplicated_sections,
            removed_sections=removed_sections,
        )

    def _normalize_body(
        self,
        markdown: str,
        removed_sections: list[str],
        seen_blocks: set[str],
        deduplicated_sections: list[str],
    ) -> str:
        cleaned = self._clean_text(markdown)
        normalized_lines: list[str] = []

        for raw_block in cleaned.split("\n\n"):
            block = self._normalize_heading_levels(raw_block.strip())
            if not block:
                continue
            if self._is_noise(block):
                removed_sections.append(block)
                continue
            canonical = re.sub(r"\s+", " ", block).strip().lower()
            if canonical in seen_blocks:
                deduplicated_sections.append(block)
                continue
            seen_blocks.add(canonical)
            normalized_lines.append(block)

        return "\n\n".join(normalized_lines)

    def _build_asset_blocks(self, document: ParsedDocument) -> str:
        blocks: list[str] = []
        for image in document.images:
            label = self._clean_text(image.title or image.asset_id)
            description = self._clean_text(image.description or "")
            body = f"[IMAGE] {label}"
            if description:
                body = f"{body}: {description}"
            blocks.append(body)

        for table in document.tables:
            label = self._clean_text(table.title or table.asset_id)
            table_markdown = self._clean_text(table.markdown or "")
            body = f"[TABLE] {label}"
            if table_markdown:
                body = f"{body}\n{table_markdown}"
            blocks.append(body)

        return "\n\n".join(blocks)

    def _normalize_heading_levels(self, text: str) -> str:
        if not text.startswith("#"):
            return text
        match = re.match(r'^(#+)\s*(.*)$', text)
        if not match:
            return text
        level = min(len(match.group(1)), 6)
        title = self._clean_text(match.group(2))
        return f"{'#' * level} {title}".strip()

    def _is_noise(self, text: str) -> bool:
        normalized = self._clean_text(text).lower()
        if not normalized:
            return True
        return any(pattern.match(normalized) for pattern in self._noise_patterns)

    def _clean_text(self, text: str) -> str:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)
        normalized = re.sub(r"[ \t]+\n", "\n", normalized)
        return normalized.strip()