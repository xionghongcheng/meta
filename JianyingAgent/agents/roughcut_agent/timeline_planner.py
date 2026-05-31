#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Timeline helpers for roughcut output."""

from __future__ import annotations

from typing import Dict, List


class TimelinePlanner:
    @staticmethod
    def total_duration(segments: List[Dict]) -> float:
        return sum(float(segment.get("duration", 0.0)) for segment in segments)
