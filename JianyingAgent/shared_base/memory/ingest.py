#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Helpers for building and loading the shared story memory."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from shared_base.paths import default_memory_path

from .story_index import ContentMemory


def ingest_story_files(files: Sequence[str], output_path: str | None = None) -> str:
    memory = ContentMemory.from_files(files)
    target = Path(output_path) if output_path else default_memory_path()
    return memory.save(target)


def load_default_memory() -> ContentMemory:
    path = default_memory_path()
    if path.exists():
        return ContentMemory.load(path)
    return ContentMemory()
