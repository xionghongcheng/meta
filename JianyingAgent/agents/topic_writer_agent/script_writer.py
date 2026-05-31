#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate reusable topic/script packages."""

from __future__ import annotations

from pathlib import Path

from contracts import ScriptPackage
from shared_base.memory import ContentMemory
from shared_base.paths import default_memory_path

from .topic_planner import TopicScriptAssistant


class ScriptWriter:
    def __init__(self, memory_path: str | None = None):
        self.memory_path = Path(memory_path) if memory_path else default_memory_path()

    def _load_memory(self) -> ContentMemory:
        if self.memory_path.exists():
            return ContentMemory.load(self.memory_path)
        return ContentMemory()

    def create_brief(self, idea: str):
        assistant = TopicScriptAssistant(self._load_memory())
        return assistant.create_brief(idea)

    def create_script_package(self, idea: str) -> ScriptPackage:
        brief = self.create_brief(idea)
        return ScriptPackage(
            idea=idea,
            markdown=brief.to_markdown(),
            shooting_list=brief.shooting_list,
            must_capture_dialogue=brief.must_capture_dialogue,
            voiceover_outline=brief.voiceover_outline,
            editing_notes=brief.editing_notes,
        )
