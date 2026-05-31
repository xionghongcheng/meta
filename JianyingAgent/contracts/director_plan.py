#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Structured director plan for roughcut execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class DirectorBeat:
    beat_id: str
    title: str
    objective: str
    order: int
    priority: str = "normal"
    preferred_duration_seconds: float = 18.0
    keywords: List[str] = field(default_factory=list)
    required_visuals: List[str] = field(default_factory=list)
    required_dialogue: List[str] = field(default_factory=list)
    editing_notes: List[str] = field(default_factory=list)
    reference_file_ids: List[str] = field(default_factory=list)


@dataclass
class DirectorPlan:
    source_script: str
    target_duration_seconds: float = 180.0
    opening_hook: str = ""
    story_summary: str = ""
    story_lines: List[str] = field(default_factory=list)
    focus_characters: List[str] = field(default_factory=list)
    ordering_policy: str = "story_first_then_visual"
    selection_policy: str = "cover_story_beats_before_visual_polish"
    min_segment_seconds: float = 5.0
    max_segment_seconds: float = 30.0
    min_segment_count: int = 6
    beats: List[DirectorBeat] = field(default_factory=list)
    must_capture_visuals: List[str] = field(default_factory=list)
    must_capture_dialogue: List[str] = field(default_factory=list)
    editing_rules: List[str] = field(default_factory=list)
