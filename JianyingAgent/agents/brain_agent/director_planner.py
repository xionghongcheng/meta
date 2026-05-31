#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build a machine-executable director plan from a human-facing script."""

from __future__ import annotations

import re
from typing import Dict, List

from contracts import DirectorBeat, DirectorPlan, TopicBrief


class DirectorPlanner:
    def build(self, script: str, brief: TopicBrief) -> DirectorPlan:
        sections = self._parse_sections(script)
        target_duration = self._extract_target_duration(script)
        hook = self._first_paragraph(sections.get("开头钩子", []))
        summary = self._join_paragraphs(sections.get("故事梗概", []))
        visuals = self._bullet_lines(sections.get("必拍画面", []))
        dialogue = self._bullet_lines(sections.get("必收对白", []))
        editing_rules = self._bullet_lines(sections.get("粗剪提示", []))
        voiceover_outline = self._numbered_lines(sections.get("配音大纲", []))

        beats = self._build_beats(
            voiceover_outline=voiceover_outline,
            summary=summary,
            visuals=visuals,
            dialogue=dialogue,
            editing_rules=editing_rules,
            target_duration=target_duration,
        )

        return DirectorPlan(
            source_script=script,
            target_duration_seconds=target_duration,
            opening_hook=hook,
            story_summary=summary,
            story_lines=list(brief.story_lines),
            focus_characters=list(brief.focus_characters),
            min_segment_count=max(4, min(8, round(target_duration / 20))) if target_duration else 6,
            beats=beats,
            must_capture_visuals=visuals,
            must_capture_dialogue=dialogue,
            editing_rules=editing_rules,
        )

    @staticmethod
    def _parse_sections(script: str) -> Dict[str, List[str]]:
        sections: Dict[str, List[str]] = {}
        current = "root"
        sections[current] = []

        for raw_line in script.splitlines():
            line = raw_line.rstrip()
            heading = re.match(r"^##\s+(.+?)\s*$", line)
            if heading:
                current = heading.group(1).strip()
                sections.setdefault(current, [])
                continue
            sections.setdefault(current, []).append(line)
        return sections

    @staticmethod
    def _extract_target_duration(script: str) -> float:
        explicit_seconds = re.search(r"目标时长[：:\s]*约?\s*(\d+(?:\.\d+)?)\s*秒", script)
        explicit_minutes = re.search(r"目标时长[：:\s]*约?\s*(\d+(?:\.\d+)?)\s*分钟", script)
        if explicit_seconds:
            return float(explicit_seconds.group(1))
        if explicit_minutes:
            return float(explicit_minutes.group(1)) * 60
        minutes = re.search(r"(\d+(?:\.\d+)?)\s*分钟", script)
        if minutes:
            return float(minutes.group(1)) * 60
        seconds = re.search(r"(\d+(?:\.\d+)?)\s*秒", script)
        if seconds:
            return float(seconds.group(1))
        return 180.0

    @staticmethod
    def _first_paragraph(lines: List[str]) -> str:
        return DirectorPlanner._join_paragraphs(lines).split("\n\n")[0].strip() if lines else ""

    @staticmethod
    def _join_paragraphs(lines: List[str]) -> str:
        cleaned = [line.strip() for line in lines if line.strip()]
        return "\n".join(cleaned).strip()

    @staticmethod
    def _bullet_lines(lines: List[str]) -> List[str]:
        result = []
        for raw in lines:
            line = raw.strip()
            if not line:
                continue
            if line.startswith("- "):
                result.append(line[2:].strip())
            elif line.startswith("→"):
                result.append(line[1:].strip())
        return result

    @staticmethod
    def _numbered_lines(lines: List[str]) -> List[str]:
        result = []
        for raw in lines:
            line = raw.strip()
            if not line:
                continue
            line = re.sub(r"^\d+\.\s*", "", line)
            if line:
                result.append(line)
        return result

    def _build_beats(
        self,
        *,
        voiceover_outline: List[str],
        summary: str,
        visuals: List[str],
        dialogue: List[str],
        editing_rules: List[str],
        target_duration: float,
    ) -> List[DirectorBeat]:
        beat_sources = voiceover_outline or self._summary_beats(summary)
        if not beat_sources:
            beat_sources = ["开场交代", "中段推进", "情绪收尾"]

        preferred = max(10.0, min(24.0, target_duration / max(len(beat_sources), 1)))
        beats: List[DirectorBeat] = []

        for order, source in enumerate(beat_sources, start=1):
            title = self._beat_title(source, order)
            keywords = self._extract_keywords(f"{title} {source}")
            matched_visuals = [item for item in visuals if self._line_matches(item, keywords)]
            matched_dialogue = [item for item in dialogue if self._line_matches(item, keywords)]
            matched_rules = [item for item in editing_rules if self._line_matches(item, keywords)]

            if not matched_visuals and order == 1 and visuals:
                matched_visuals = visuals[:2]
            if not matched_dialogue and order == len(beat_sources) and dialogue:
                matched_dialogue = dialogue[-2:]
            reference_ids = self._extract_reference_file_ids(matched_visuals + matched_dialogue + matched_rules)

            beats.append(
                DirectorBeat(
                    beat_id=f"beat_{order:02d}",
                    title=title,
                    objective=source,
                    order=order,
                    priority=self._beat_priority(source, order, len(beat_sources)),
                    preferred_duration_seconds=round(preferred, 1),
                    keywords=keywords,
                    required_visuals=matched_visuals,
                    required_dialogue=matched_dialogue,
                    editing_notes=matched_rules,
                    reference_file_ids=reference_ids,
                )
            )

        return beats

    @staticmethod
    def _summary_beats(summary: str) -> List[str]:
        if not summary:
            return []
        parts = [part.strip() for part in re.split(r"\n+", summary) if part.strip()]
        return parts[:6]

    @staticmethod
    def _beat_title(source: str, order: int) -> str:
        if "：" in source:
            return source.split("：", 1)[0].strip()[:16]
        if ":" in source:
            return source.split(":", 1)[0].strip()[:16]
        compact = re.sub(r"[\"“”。，、；：！？]", " ", source)
        compact = re.sub(r"\s+", " ", compact).strip()
        return compact[:16] or f"段落{order}"

    @staticmethod
    def _beat_priority(source: str, order: int, total: int) -> str:
        if order in {1, total}:
            return "anchor"
        if any(token in source for token in ["核心", "打赌", "妈妈", "爆笑", "结尾"]):
            return "core"
        return "normal"

    @staticmethod
    def _extract_keywords(text: str) -> List[str]:
        stop_words = {
            "我们", "今天", "然后", "最后", "一句", "旁白", "原声", "保留", "开头",
            "结尾", "段落", "故事", "画面", "这句", "一个", "一下", "不要", "可用",
        }
        tokens = re.split(r"[，。！？；：,\s\-\(\)\"“”]+", text)
        keywords = []
        for token in tokens:
            token = token.strip()
            if len(token) < 2 or token in stop_words:
                continue
            if token not in keywords:
                keywords.append(token)
            if len(token) >= 4:
                for fragment in {token[:2], token[-2:], token[:3], token[-3:]}:
                    fragment = fragment.strip()
                    if len(fragment) >= 2 and fragment not in stop_words and fragment not in keywords:
                        keywords.append(fragment)
        return keywords[:10]

    @staticmethod
    def _line_matches(line: str, keywords: List[str]) -> bool:
        if not keywords:
            return False
        return any(keyword in line for keyword in keywords)

    @staticmethod
    def _extract_reference_file_ids(lines: List[str]) -> List[str]:
        refs = []
        for line in lines:
            for match in re.findall(r"(IMG_\d+)", line):
                if match not in refs:
                    refs.append(match)
        return refs
