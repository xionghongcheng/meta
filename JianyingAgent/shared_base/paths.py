#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Path helpers for the shared knowledge base."""

from __future__ import annotations

from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
CANON_DIR = PROJECT_DIR / "shared_base" / "canon"
LEGACY_CANON_DIR = PROJECT_DIR / "content_brain"
LEGACY_MEMORY_PATH = PROJECT_DIR / "temp" / "content_memory" / "stories.json"
SHARED_MEMORY_PATH = PROJECT_DIR / "shared_base" / "memory" / "stories.json"


def default_memory_path() -> Path:
    """Return the preferred story-memory file, falling back to the legacy path."""
    if SHARED_MEMORY_PATH.exists():
        return SHARED_MEMORY_PATH
    return LEGACY_MEMORY_PATH


def default_canon_dir() -> Path:
    """Return the canonical content-asset directory for V2."""
    return CANON_DIR
