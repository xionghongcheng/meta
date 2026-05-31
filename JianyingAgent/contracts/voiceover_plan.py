#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Contracts for automatic voice-over generation and alignment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class VoiceoverLine:
    beat_id: str
    beat_title: str
    text: str
    order: int
    preferred_start_seconds: float = 0.0
    audio_path: str = ""
    duration_seconds: float = 0.0
    enabled: bool = True


@dataclass
class VoiceoverPlan:
    source_text: str
    voice_name: str = "Microsoft Huihui Desktop"
    rate: int = 0
    volume: int = 100
    lines: List[VoiceoverLine] = field(default_factory=list)
    backend: str = "windows_sapi"
    status: str = "planned"
    error: Optional[str] = None
