#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Topic-level planning contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class TopicBrief:
    idea: str
    story_lines: List[str] = field(default_factory=list)
    focus_characters: List[str] = field(default_factory=list)
    duplication_risk: str = "低"
    similar_story_ids: List[str] = field(default_factory=list)
