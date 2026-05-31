#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Canon helpers and structured character data."""

from shared_base.paths import CANON_DIR, LEGACY_CANON_DIR

from .character_profiles import (
    CHARACTER_PROFILES,
    CharacterProfile,
    infer_focus_characters,
    relationship_guidance,
)

__all__ = [
    "CANON_DIR",
    "LEGACY_CANON_DIR",
    "CHARACTER_PROFILES",
    "CharacterProfile",
    "infer_focus_characters",
    "relationship_guidance",
]
