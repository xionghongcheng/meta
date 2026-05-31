#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script output contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class ScriptPackage:
    idea: str
    markdown: str
    shooting_list: List[str] = field(default_factory=list)
    must_capture_dialogue: List[str] = field(default_factory=list)
    voiceover_outline: List[str] = field(default_factory=list)
    editing_notes: List[str] = field(default_factory=list)
