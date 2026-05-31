#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build a voice-over plan from a director plan."""

from __future__ import annotations

import re
from typing import List

from contracts import DirectorPlan, VoiceoverLine, VoiceoverPlan


class VoiceoverPlanner:
    def build(self, director_plan: DirectorPlan) -> VoiceoverPlan:
        lines: List[VoiceoverLine] = []
        for beat in director_plan.beats:
            text = self._extract_spoken_text(beat.objective)
            if not text:
                continue
            lines.append(
                VoiceoverLine(
                    beat_id=beat.beat_id,
                    beat_title=beat.title,
                    text=text,
                    order=beat.order,
                )
            )

        return VoiceoverPlan(
            source_text=director_plan.source_script,
            lines=lines,
        )

    @staticmethod
    def _extract_spoken_text(objective: str) -> str:
        quoted = re.findall(r"[\"“](.*?)[\"”]", objective)
        if quoted:
            return " ".join(item.strip() for item in quoted if item.strip())

        text = objective
        for marker in ["：", ":"]:
            if marker in text:
                text = text.split(marker, 1)[1].strip()
                break

        text = text.replace("旁白轻带——", "").replace("旁白一句话——", "")
        text = text.replace("配音退后，让原声主导。最后补一句——", "")
        text = text.replace("少说话，让画面和原声推。", "")
        text = re.sub(r"\s+", " ", text).strip(" .。")
        if any(flag in text for flag in ["保留现场音", "让画面", "原声主导"]) and len(text) <= 14:
            return ""
        return text.strip()
