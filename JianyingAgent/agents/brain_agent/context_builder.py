#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build shared context for other agents."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from shared_base.memory import ContentMemory
from shared_base.paths import CANON_DIR, default_memory_path


class BrainContextBuilder:
    def __init__(self, memory_path: str | None = None):
        self.memory_path = Path(memory_path) if memory_path else default_memory_path()

    def load_memory(self) -> ContentMemory:
        if self.memory_path.exists():
            return ContentMemory.load(self.memory_path)
        return ContentMemory()

    def build(self) -> Dict[str, object]:
        memory = self.load_memory()
        return {
            "canon_dir": str(CANON_DIR),
            "memory_path": str(self.memory_path),
            "story_count": len(memory.stories),
        }
