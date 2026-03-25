from __future__ import annotations

import json

import httpx
from pydantic import BaseModel, Field


class LlmGatewayError(RuntimeError):
    pass


class LlmGatewaySettings(BaseModel):
    provider: str = Field(default="openai_compatible")
    base_url: str = Field(min_length=1)
    api_key: str = Field(min_length=1)
    model: str = Field(min_length=1)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4000, ge=256, le=16000)


class LlmGateway:
    def __init__(self, settings: LlmGatewaySettings) -> None:
        self._settings = settings

    def test_connection(self) -> dict[str, object]:
        payload = self.generate_json(
            system_prompt="You are a connectivity probe. Return a tiny JSON object.",
            user_prompt="Return JSON with keys ok, provider, model.",
            response_schema={
                "type": "object",
                "properties": {
                    "ok": {"type": "boolean"},
                    "provider": {"type": "string"},
                    "model": {"type": "string"},
                },
                "required": ["ok", "provider", "model"],
            },
        )
        return payload

    def generate_json(self, *, system_prompt: str, user_prompt: str, response_schema: dict[str, object]) -> dict[str, object]:
        base_url = self._settings.base_url.rstrip("/")
        endpoint = f"{base_url}/chat/completions"
        request_payload = {
            "model": self._settings.model,
            "temperature": self._settings.temperature,
            "max_tokens": self._settings.max_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "structured_response",
                    "schema": response_schema,
                },
            },
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        headers = {
            "Authorization": f"Bearer {self._settings.api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=45.0) as client:
                response = client.post(endpoint, headers=headers, json=request_payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LlmGatewayError(f"LLM request failed: {exc}") from exc

        try:
            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
            if isinstance(content, list):
                content = "".join(item.get("text", "") for item in content if isinstance(item, dict))
            if not isinstance(content, str) or not content.strip():
                raise ValueError("empty content")
            parsed = json.loads(content)
        except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise LlmGatewayError(f"LLM response parsing failed: {exc}") from exc

        if not isinstance(parsed, dict):
            raise LlmGatewayError("LLM response is not a JSON object")
        return parsed