#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Small Codex client for JSON-producing LLM decisions."""

from __future__ import annotations

import json
from typing import Any

import requests


class CodexClient:
    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger

    @property
    def available(self) -> bool:
        return bool(getattr(self.config, "OPENAI_API_KEY", ""))

    def request_json(self, prompt: str, *, max_output_tokens: int, timeout: int | None = None) -> dict[str, Any] | None:
        if not self.available:
            return None

        payload: dict[str, Any] = {
            "model": getattr(self.config, "CODEX_MODEL", "gpt-5.2-codex"),
            "input": prompt,
            "reasoning": {
                "effort": getattr(self.config, "CODEX_REASONING_EFFORT", "medium"),
            },
            "max_output_tokens": max_output_tokens,
        }

        try:
            response = requests.post(
                getattr(self.config, "OPENAI_RESPONSES_URL", "https://api.openai.com/v1/responses"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {getattr(self.config, 'OPENAI_API_KEY', '')}",
                },
                json=payload,
                timeout=timeout or int(getattr(self.config, "CODEX_TIMEOUT_SECONDS", 120)),
            )
            response.raise_for_status()
            content = self._extract_text(response.json())
            return self._parse_json_content(content)
        except Exception as exc:
            if self.logger:
                self.logger.warning("Codex LLM fallback: %s", exc)
            return None

    @staticmethod
    def _extract_text(result: dict[str, Any]) -> str:
        if result.get("output_text"):
            return str(result["output_text"])

        text_parts: list[str] = []
        for item in result.get("output", []):
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"}:
                    text_parts.append(str(content.get("text", "")))
        return "\n".join(part for part in text_parts if part).strip()

    @staticmethod
    def _parse_json_content(content: str) -> dict[str, Any]:
        content = (content or "").strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return json.loads(content.strip())
