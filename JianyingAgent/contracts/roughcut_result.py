#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Output contract for roughcut execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .director_plan import DirectorPlan
from .voiceover_plan import VoiceoverPlan


@dataclass
class RoughcutResult:
    status: str
    project_name: str
    jcc_project: str = ""
    final_video: Optional[str] = None
    segments: List[Dict] = field(default_factory=list)
    message: str = ""
    workspace_dir: str = ""
    keyframe_manifest: List[Dict] = field(default_factory=list)
    timeline_sort: str = ""
    director_plan: Optional[DirectorPlan] = None
    voiceover_plan: Optional[VoiceoverPlan] = None
