#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Skills for story-memory inspection and ingestion."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from shared_base.memory.story_index import ContentMemory
from shared_base.paths import default_memory_path


class StoryMemorySkill:
    def __init__(self, memory_path: str | None = None):
        self.memory_path = Path(memory_path) if memory_path else default_memory_path()

    def profile(self, memory_path: str | None = None) -> dict:
        path = Path(memory_path) if memory_path else self.memory_path
        if not path.exists():
            return {"exists": False, "path": str(path), "profile": None}
        memory = ContentMemory.load(path)
        return {"exists": True, "path": str(path), "profile": memory.profile()}

    def ingest(self, files: Sequence[str], out: str | None = None) -> dict:
        clean_files = [str(item).strip() for item in files if str(item).strip()]
        if not clean_files:
            raise ValueError("请提供至少一个历史配音 txt 文件路径")

        memory = ContentMemory.from_files(clean_files)
        target = Path(out) if out else self.memory_path
        saved = memory.save(target)
        return {
            "story_count": len(memory.stories),
            "output": saved,
        }
