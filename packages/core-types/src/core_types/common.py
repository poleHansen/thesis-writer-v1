from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict


JsonDict = dict[str, Any]


class CoreModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, use_enum_values=True)


class TimestampedModel(CoreModel):
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class IdentifiedModel(TimestampedModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
