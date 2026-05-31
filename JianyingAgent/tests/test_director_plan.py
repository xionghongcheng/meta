#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Unit tests for director plan generation."""

from __future__ import annotations

import unittest

from agents.brain_agent.director_planner import DirectorPlanner
from contracts import DirectorBeat, TopicBrief
from pipelines.roughcut_pipeline.analyzer import Skill3Analyzer


class DirectorPlanTest(unittest.TestCase):
    def test_build_plan_from_markdown_script(self) -> None:
        script = """
## 开头钩子
我们家出门喂个鸽子，跟别人不太一样。

## 故事梗概
爸爸先去买鸽粮，妈妈后来慢慢伸手喂鸽子。
后面爸爸和女朋友因为下雨打赌吵了起来。

## 必拍画面
- 爸爸买鸽粮/撒鸽粮的镜头
- 妈妈伸手→缩手→再伸手→转头笑
- 打赌三连：爸爸宣布打赌→飘雨→争论小雨算不算→女朋友笑蹲下

## 必收对白
- 爸爸买鸽粮："来，请买吧..."（IMG_1431）
- 爸爸宣布打赌："今晚要下雨"（IMG_1474）

## 配音大纲
1. 开头一句交代今天带爸妈喂鸽子
2. 妈妈喂鸽子：少说话，让画面推
3. 打赌段落：让原声主导

## 粗剪提示
- 打赌三连是核心叙事段落
- 目标时长：约120秒
""".strip()

        brief = TopicBrief(
            idea="喂鸽子",
            story_lines=["妈妈恢复线", "爸爸适应线"],
            focus_characters=["mom", "dad"],
        )

        plan = DirectorPlanner().build(script, brief)

        self.assertEqual(plan.target_duration_seconds, 120.0)
        self.assertEqual(plan.ordering_policy, "story_first_then_visual")
        self.assertGreaterEqual(len(plan.beats), 3)
        self.assertEqual(plan.beats[0].order, 1)
        self.assertIn("IMG_1474", plan.beats[-1].reference_file_ids)
        self.assertEqual(plan.beats[-1].priority, "anchor")
        self.assertIn("打赌三连是核心叙事段落", plan.editing_rules)

    def test_analyzer_clamps_segment_bounds(self) -> None:
        start, end = Skill3Analyzer._clamp_segment_bounds(71, 94, 28.24)
        self.assertEqual(start, 28.24)
        self.assertEqual(end, 28.24)

    def test_director_candidate_scoring_prefers_opening_position_and_dialogue(self) -> None:
        beat = DirectorBeat(
            beat_id="beat_01",
            title="开头一句交代",
            objective="开头一句交代",
            order=1,
            priority="anchor",
            preferred_duration_seconds=20.0,
            keywords=["开头", "喂鸽子"],
            required_dialogue=["今天带爸妈来公园喂鸽子"],
            reference_file_ids=["IMG_1431"],
        )
        transcript = {
            "duration": 120.0,
            "full_text": "今天带爸妈来公园喂鸽子，爸爸一直在念叨。",
            "segments": [{"text": "今天带爸妈来公园喂鸽子"}],
        }
        better = {
            "file_id": "IMG_1431",
            "start": 0.0,
            "end": 18.0,
            "duration": 18.0,
            "transcript": transcript,
        }
        worse = {
            "file_id": "IMG_1452",
            "start": 70.0,
            "end": 88.0,
            "duration": 18.0,
            "transcript": transcript,
        }

        analyzer = Skill3Analyzer.__new__(Skill3Analyzer)
        score_better = analyzer._score_director_candidate(
            better,
            beat=beat,
            transcript=transcript,
            transcript_position=9.0,
        )
        score_worse = analyzer._score_director_candidate(
            worse,
            beat=beat,
            transcript=transcript,
            transcript_position=79.0,
        )

        self.assertGreater(score_better, score_worse)


if __name__ == "__main__":
    unittest.main()
