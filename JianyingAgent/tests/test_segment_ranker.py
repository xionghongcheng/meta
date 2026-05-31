#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Unit tests for visual timeline ordering."""

from __future__ import annotations

import unittest

from tools.segment_ranker import SegmentRanker


class SegmentRankerTimelineSortTest(unittest.TestCase):
    def test_annotate_uses_segment_range_keyframes_before_clip_average(self) -> None:
        segments = [
            {"file_id": "clip_a", "start": 0, "end": 3, "duration": 3, "reason": ""},
            {"file_id": "clip_a", "start": 10, "end": 13, "duration": 3, "reason": ""},
        ]
        manifest = [
            {
                "id": "clip_a",
                "visual_summary": {
                    "quality_score": 0.50,
                    "diversity_score": 0.20,
                    "metrics": [
                        {
                            "index": 1,
                            "timestamp": 1.0,
                            "path": "low.jpg",
                            "metrics": {"quality_score": 0.20},
                        },
                        {
                            "index": 2,
                            "timestamp": 11.0,
                            "path": "high.jpg",
                            "metrics": {"quality_score": 0.90},
                        },
                    ],
                },
            }
        ]

        annotated = SegmentRanker().annotate(segments, manifest, script="")

        self.assertEqual(annotated[0]["visual_score"], 0.20)
        self.assertEqual(annotated[0]["best_frame_path"], "low.jpg")
        self.assertEqual(annotated[0]["visual_summary"]["score_scope"], "segment_range")
        self.assertEqual(annotated[1]["visual_score"], 0.90)
        self.assertEqual(annotated[1]["best_frame_path"], "high.jpg")

    def test_visual_sort_orders_high_priority_segments_first(self) -> None:
        segments = [
            {
                "file_id": "clip_a",
                "start": 0,
                "duration": 9,
                "priority_score": 0.42,
                "visual_score": 0.62,
                "visual_diversity": 0.30,
                "visual_frame_count": 3,
            },
            {
                "file_id": "clip_b",
                "start": 0,
                "duration": 7,
                "priority_score": 0.88,
                "visual_score": 0.72,
                "visual_diversity": 0.40,
                "visual_frame_count": 3,
            },
            {
                "file_id": "clip_c",
                "start": 0,
                "duration": 5,
                "priority_score": 0.88,
                "visual_score": 0.69,
                "visual_diversity": 0.65,
                "visual_frame_count": 3,
            },
        ]

        ordered = SegmentRanker().sort_for_roughcut(segments)

        self.assertEqual([item["file_id"] for item in ordered], ["clip_b", "clip_c", "clip_a"])
        self.assertEqual([item["timeline_order"] for item in ordered], [1, 2, 3])
        self.assertEqual({item["timeline_sort_mode"] for item in ordered}, {"visual_priority"})

    def test_sort_preserves_source_order_without_visual_signal(self) -> None:
        segments = [
            {"file_id": "clip_a", "start": 0, "duration": 9, "priority_score": 0.10},
            {"file_id": "clip_b", "start": 0, "duration": 7, "priority_score": 0.90},
        ]

        ordered = SegmentRanker().sort_for_roughcut(segments)

        self.assertEqual([item["file_id"] for item in ordered], ["clip_a", "clip_b"])
        self.assertEqual([item["timeline_order"] for item in ordered], [1, 2])
        self.assertEqual({item["timeline_sort_mode"] for item in ordered}, {"source_order"})

    def test_trim_uses_dynamic_minimum_for_two_minute_cut(self) -> None:
        segments = [
            {"file_id": f"clip_{index}", "start": 0, "duration": 30, "priority_score": 1.0 - index * 0.05}
            for index in range(8)
        ]

        kept = SegmentRanker().trim_to_target(
            segments,
            script="开头3秒用高光画面，目标时长：约120秒",
            min_segments=3,
        )

        self.assertGreaterEqual(len(kept), 6)

    def test_cap_long_segments_uses_best_visual_frame_window(self) -> None:
        segments = [
            {
                "file_id": "clip_a",
                "start": 0,
                "end": 100,
                "duration": 100,
                "best_frame_timestamp": 80,
            }
        ]

        capped = SegmentRanker().cap_long_segments(segments, script="目标时长：约120秒")

        self.assertEqual(len(capped), 1)
        self.assertLessEqual(capped[0]["duration"], 23.0)
        self.assertEqual(capped[0]["trimmed_by"], "best_visual_frame_window")
        self.assertGreaterEqual(capped[0]["start"], 68.0)
        self.assertLessEqual(capped[0]["end"], 92.0)

    def test_story_then_visual_sort_respects_beat_order(self) -> None:
        segments = [
            {
                "file_id": "late_better_visual",
                "beat_id": "beat_02",
                "beat_index": 2,
                "priority_score": 0.9,
                "visual_score": 0.9,
                "selection_order": 2,
            },
            {
                "file_id": "early_lower_visual",
                "beat_id": "beat_01",
                "beat_index": 1,
                "priority_score": 0.4,
                "visual_score": 0.4,
                "selection_order": 1,
            },
        ]

        ordered = SegmentRanker().sort_for_roughcut(segments, director_plan=object())

        self.assertEqual([item["file_id"] for item in ordered], ["early_lower_visual", "late_better_visual"])
        self.assertEqual({item["timeline_sort_mode"] for item in ordered}, {"story_then_visual"})

    def test_trim_keeps_anchor_beats_when_target_is_tight(self) -> None:
        segments = [
            {"file_id": "anchor", "duration": 15, "priority_score": 0.2, "beat_priority": "anchor"},
            {"file_id": "core", "duration": 15, "priority_score": 0.3, "beat_priority": "core"},
            {"file_id": "normal_1", "duration": 15, "priority_score": 0.1, "beat_priority": "normal"},
            {"file_id": "normal_2", "duration": 15, "priority_score": 0.05, "beat_priority": "normal"},
            {"file_id": "normal_3", "duration": 15, "priority_score": 0.04, "beat_priority": "normal"},
            {"file_id": "normal_4", "duration": 15, "priority_score": 0.03, "beat_priority": "normal"},
        ]

        kept = SegmentRanker().trim_to_target(segments, script="目标时长：约60秒", min_segments=3)

        kept_ids = {item["file_id"] for item in kept}
        self.assertIn("anchor", kept_ids)
        self.assertIn("core", kept_ids)

    def test_trim_removes_duplicate_beat_before_unique_beat(self) -> None:
        segments = [
            {"file_id": "beat1_a", "duration": 20, "priority_score": 0.2, "beat_id": "beat_01", "beat_priority": "anchor"},
            {"file_id": "beat2_a", "duration": 20, "priority_score": 0.3, "beat_id": "beat_02", "beat_priority": "normal"},
            {"file_id": "beat2_b", "duration": 20, "priority_score": 0.1, "beat_id": "beat_02", "beat_priority": "normal"},
            {"file_id": "beat3_a", "duration": 20, "priority_score": 0.4, "beat_id": "beat_03", "beat_priority": "core"},
            {"file_id": "beat4_a", "duration": 20, "priority_score": 0.5, "beat_id": "beat_04", "beat_priority": "normal"},
            {"file_id": "beat5_a", "duration": 20, "priority_score": 0.6, "beat_id": "beat_05", "beat_priority": "normal"},
        ]

        kept = SegmentRanker().trim_to_target(segments, script="目标时长：约90秒", min_segments=3)

        kept_ids = {item["file_id"] for item in kept}
        self.assertNotIn("beat2_b", kept_ids)
        self.assertIn("beat1_a", kept_ids)
        self.assertIn("beat3_a", kept_ids)


if __name__ == "__main__":
    unittest.main()
