#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Rank and trim selected segments using keyframe metadata."""

from __future__ import annotations

import re
from typing import Dict, List

from contracts import DirectorPlan


class SegmentRanker:
    """Attach visual scores and trim clips to a target duration."""

    def annotate(self, segments: List[Dict], keyframe_manifest: List[Dict], script: str = "") -> List[Dict]:
        lookup = {item["id"]: item for item in keyframe_manifest}
        script_keywords = self._extract_keywords(script)

        annotated = []
        for selection_index, segment in enumerate(segments, start=1):
            file_id = segment.get("file_id", "")
            manifest = lookup.get(file_id, {})
            visual_summary = self._segment_visual_summary(segment, manifest)
            quality = float(visual_summary.get("quality_score", 0.0))
            diversity = float(visual_summary.get("diversity_score", 0.0))
            frame_count = int(visual_summary.get("frame_count", 0))
            best_frame_path = visual_summary.get("best_frame_path", "")
            best_frame_index = visual_summary.get("best_frame_index")

            transcript_text = self._segment_text(segment)
            keyword_hits = sum(1 for word in script_keywords if word and word in transcript_text)
            keyword_score = min(1.0, keyword_hits / max(len(script_keywords), 1))
            duration_score = self._duration_score(segment)

            priority_score = (
                quality * 0.45
                + diversity * 0.15
                + keyword_score * 0.25
                + duration_score * 0.15
            )

            segment = dict(segment)
            segment["visual_summary"] = visual_summary
            segment["visual_score"] = round(quality, 3)
            segment["visual_diversity"] = round(diversity, 3)
            segment["visual_frame_count"] = frame_count
            segment["best_frame_path"] = best_frame_path
            segment["best_frame_index"] = best_frame_index
            segment["best_frame_timestamp"] = visual_summary.get("best_frame_timestamp")
            segment["keyword_score"] = round(keyword_score, 3)
            segment["priority_score"] = round(priority_score, 3)
            segment["selection_order"] = int(segment.get("selection_order", selection_index))
            annotated.append(segment)

        return annotated

    def cap_long_segments(
        self,
        segments: List[Dict],
        script: str = "",
        default_max_duration: float = 30.0,
    ) -> List[Dict]:
        if not segments:
            return []

        max_duration = default_max_duration
        target = self._extract_target_duration(script)
        if target:
            min_count = self._minimum_segments_for_target(target)
            max_duration = min(default_max_duration, max(8.0, target / max(min_count, 1) * 1.15))

        capped = []
        for segment in segments:
            item = dict(segment)
            start = float(item.get("start", 0.0) or 0.0)
            end = float(item.get("end", start + float(item.get("duration", 0.0) or 0.0)) or start)
            duration = max(0.0, end - start)
            if duration <= max_duration:
                item["duration"] = round(duration, 3)
                capped.append(item)
                continue

            anchor = item.get("best_frame_timestamp")
            if anchor is None:
                anchor = start + duration / 2
            anchor = float(anchor)
            new_start = max(start, anchor - max_duration / 2)
            new_end = new_start + max_duration
            if new_end > end:
                new_end = end
                new_start = max(start, new_end - max_duration)

            item["original_start"] = round(start, 3)
            item["original_end"] = round(end, 3)
            item["original_duration"] = round(duration, 3)
            item["start"] = round(new_start, 3)
            item["end"] = round(new_end, 3)
            item["duration"] = round(new_end - new_start, 3)
            item["duration_cap"] = round(max_duration, 3)
            item["trimmed_by"] = "best_visual_frame_window"
            capped.append(item)

        return capped

    def sort_for_roughcut(self, segments: List[Dict], director_plan: DirectorPlan | None = None) -> List[Dict]:
        """Order kept clips for the roughcut timeline by visual priority.

        If no keyframe score is available, keep the analyzer/source order. This
        avoids random-looking reordering when the run did not create a workspace.
        """
        if not segments:
            return []

        if director_plan and any(segment.get("beat_id") for segment in segments):
            return self._sort_story_then_visual(segments)

        has_visual_signal = any(
            int(segment.get("visual_frame_count", 0) or 0) > 0
            or bool(segment.get("best_frame_path"))
            for segment in segments
        )
        if not has_visual_signal:
            return self._mark_timeline_order(segments, mode="source_order")

        indexed_segments = []
        for index, segment in enumerate(segments, start=1):
            item = dict(segment)
            item["_source_order"] = int(item.get("selection_order", index))
            indexed_segments.append(item)

        ordered = sorted(
            indexed_segments,
            key=lambda item: (
                -float(item.get("priority_score", 0.0) or 0.0),
                -float(item.get("visual_score", 0.0) or 0.0),
                -float(item.get("visual_diversity", 0.0) or 0.0),
                float(item.get("duration", 0.0) or 0.0),
                item["_source_order"],
            ),
        )

        cleaned = []
        for item in ordered:
            item.pop("_source_order", None)
            cleaned.append(item)
        return self._mark_timeline_order(cleaned, mode="visual_priority")

    def trim_to_target(
        self,
        segments: List[Dict],
        script: str = "",
        min_segments: int = 3,
    ) -> List[Dict]:
        target = self._extract_target_duration(script)
        if not target or not segments:
            return segments
        min_segments = max(min_segments, self._minimum_segments_for_target(target))

        total = sum(float(segment.get("duration", 0.0)) for segment in segments)
        if total <= target * 1.08:
            return segments

        kept = list(segments)
        while True:
            if len(kept) <= min_segments:
                break
            if sum(float(item.get("duration", 0.0)) for item in kept) <= target * 1.03:
                break
            beat_counts = self._beat_counts(kept)
            ordered = sorted(
                kept,
                key=lambda item: (
                    self._duplicate_beat_trim_priority(item, beat_counts),
                    self._beat_trim_priority(item),
                    float(item.get("priority_score", 0.0)),
                    float(item.get("duration", 0.0)),
                ),
            )
            candidate = ordered[0]
            if candidate in kept:
                kept.remove(candidate)

        kept.sort(key=lambda item: (item.get("file_id", ""), float(item.get("start", 0.0))))
        return kept

    @staticmethod
    def _extract_keywords(script: str) -> List[str]:
        tokens = re.split(r"[，。！？；：,\s]+", script or "")
        keywords = []
        for token in tokens:
            token = token.strip()
            if len(token) >= 2 and token not in keywords:
                keywords.append(token)
        return keywords[:20]

    @staticmethod
    def _extract_target_duration(script: str) -> float | None:
        if not script:
            return None

        explicit_seconds = re.search(r"目标时长[：:\s]*约?\s*(\d+(?:\.\d+)?)\s*秒", script)
        explicit_minutes = re.search(r"目标时长[：:\s]*约?\s*(\d+(?:\.\d+)?)\s*分钟", script)
        if explicit_seconds:
            return float(explicit_seconds.group(1))
        if explicit_minutes:
            return float(explicit_minutes.group(1)) * 60

        minutes = re.search(r"(\d+(?:\.\d+)?)\s*分钟", script)
        seconds = re.search(r"(\d+(?:\.\d+)?)\s*秒", script)
        if minutes:
            return float(minutes.group(1)) * 60
        if seconds:
            return float(seconds.group(1))
        return None

    @staticmethod
    def _segment_text(segment: Dict) -> str:
        transcript = segment.get("transcript") or {}
        parts = [
            str(segment.get("reason", "")),
            str(transcript.get("full_text", "")),
        ]
        for sub in transcript.get("segments", [])[:5]:
            parts.append(str(sub.get("text", "")))
        return " ".join(parts).lower()

    @staticmethod
    def _duration_score(segment: Dict) -> float:
        duration = float(segment.get("duration", 0.0))
        if duration <= 0:
            return 0.0
        if duration <= 4:
            return 0.7
        if duration <= 10:
            return 1.0
        if duration <= 20:
            return 0.85
        return 0.55

    @staticmethod
    def _minimum_segments_for_target(target_duration: float) -> int:
        if target_duration <= 45:
            return 3
        if target_duration <= 90:
            return 5
        if target_duration <= 150:
            return 6
        return 8

    @staticmethod
    def _beat_trim_priority(segment: Dict) -> int:
        beat_priority = str(segment.get("beat_priority", "")).lower()
        if beat_priority == "anchor":
            return 2
        if beat_priority == "core":
            return 1
        return 0

    @staticmethod
    def _beat_counts(segments: List[Dict]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for segment in segments:
            beat_id = str(segment.get("beat_id", "") or "")
            if not beat_id:
                continue
            counts[beat_id] = counts.get(beat_id, 0) + 1
        return counts

    @staticmethod
    def _duplicate_beat_trim_priority(segment: Dict, beat_counts: Dict[str, int]) -> int:
        beat_id = str(segment.get("beat_id", "") or "")
        if beat_id and beat_counts.get(beat_id, 0) > 1:
            return 0
        return 1

    @staticmethod
    def _segment_visual_summary(segment: Dict, manifest: Dict) -> Dict:
        clip_summary = dict(manifest.get("visual_summary") or {})
        frames = list(clip_summary.get("metrics") or [])
        if not frames:
            return clip_summary

        start = float(segment.get("start", 0.0) or 0.0)
        end = float(segment.get("end", start + float(segment.get("duration", 0.0) or 0.0)) or start)
        midpoint = (start + end) / 2 if end > start else start

        in_range = []
        for frame in frames:
            timestamp = float(frame.get("timestamp", 0.0) or 0.0)
            if start <= timestamp <= end:
                in_range.append(frame)

        if in_range:
            selected_frames = in_range
            score_scope = "segment_range"
        else:
            selected_frames = [min(frames, key=lambda frame: abs(float(frame.get("timestamp", 0.0) or 0.0) - midpoint))]
            score_scope = "nearest_keyframe"

        def frame_quality(frame: Dict) -> float:
            metrics = frame.get("metrics") or {}
            return float(metrics.get("quality_score", 0.0) or 0.0)

        best = max(selected_frames, key=frame_quality)
        quality = sum(frame_quality(frame) for frame in selected_frames) / max(len(selected_frames), 1)

        return {
            "quality_score": round(quality, 3),
            "clip_quality_score": clip_summary.get("quality_score", 0.0),
            "best_frame_index": best.get("index"),
            "best_frame_timestamp": best.get("timestamp"),
            "best_frame_path": best.get("path", ""),
            "diversity_score": clip_summary.get("diversity_score", 0.0),
            "frame_count": len(selected_frames),
            "metrics": selected_frames,
            "score_scope": score_scope,
        }

    @staticmethod
    def _mark_timeline_order(segments: List[Dict], mode: str) -> List[Dict]:
        ordered = []
        for index, segment in enumerate(segments, start=1):
            item = dict(segment)
            item["timeline_order"] = index
            item["timeline_sort_mode"] = mode
            item["timeline_sort_score"] = round(float(item.get("priority_score", 0.0) or 0.0), 3)
            ordered.append(item)
        return ordered

    @staticmethod
    def _sort_story_then_visual(segments: List[Dict]) -> List[Dict]:
        ordered = sorted(
            segments,
            key=lambda item: (
                int(item.get("beat_index", 999) or 999),
                0 if item.get("beat_id") else 1,
                -float(item.get("priority_score", 0.0) or 0.0),
                -float(item.get("visual_score", 0.0) or 0.0),
                float(item.get("selection_order", 999) or 999),
            ),
        )
        return SegmentRanker._mark_timeline_order(ordered, mode="story_then_visual")
