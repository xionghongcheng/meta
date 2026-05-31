#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Segment normalization helpers."""

from __future__ import annotations

from typing import Dict, List


class SegmentSelector:
    @staticmethod
    def normalize(segments: List[Dict]) -> List[Dict]:
        normalized = []
        for segment in segments:
            start = float(segment.get("start", 0))
            end = float(segment.get("end", start))
            duration = float(segment.get("duration", max(0.0, end - start)))
            if duration <= 0:
                continue
            segment["duration"] = duration
            normalized.append(segment)
        return normalized
