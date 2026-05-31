#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Input contract for the roughcut chain."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .director_plan import DirectorPlan
from .voiceover_plan import VoiceoverPlan


@dataclass
class RoughcutJob:
    script: str
    source_dir: str
    project_name: str
    export_jcc: bool = True
    subtitle_srt: Optional[str] = None
    bgm_audio: Optional[str] = None
    voiceover_audio: Optional[str] = None
    video_width: Optional[int] = None
    video_height: Optional[int] = None
    fps: int = 30
    story_lines: List[str] = field(default_factory=list)
    focus_characters: List[str] = field(default_factory=list)
    director_plan: Optional[DirectorPlan] = None
    auto_voiceover: bool = False
    voiceover_plan: Optional[VoiceoverPlan] = None
