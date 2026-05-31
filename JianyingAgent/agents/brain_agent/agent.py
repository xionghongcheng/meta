#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Top-level context and routing agent."""

from __future__ import annotations

from contracts import DirectorPlan, RoughcutJob, TopicBrief, VoiceoverPlan
from orchestrator.task_types import TaskType
from shared_base.canon.character_profiles import infer_focus_characters

from .context_builder import BrainContextBuilder
from .director_planner import DirectorPlanner
from .selectors import detect_task_type
from .voiceover_planner import VoiceoverPlanner


class ContentBrainAgent:
    def __init__(self, memory_path: str | None = None):
        self.context_builder = BrainContextBuilder(memory_path=memory_path)
        self.director_planner = DirectorPlanner()
        self.voiceover_planner = VoiceoverPlanner()

    def route_request(self, source_dir: str | None = None, explicit_task: str | None = None) -> TaskType:
        return detect_task_type(source_dir=source_dir, explicit_task=explicit_task)

    def create_topic_brief(self, idea: str) -> TopicBrief:
        memory = self.context_builder.load_memory()
        story_lines = memory.related_story_lines(idea)
        focus = [profile.key for profile in infer_focus_characters(idea, story_lines)]
        similar = memory.search(idea, limit=3)
        duplication_risk = self._duplication_risk(similar)
        similar_story_ids = [item["story"].id for item in similar]
        return TopicBrief(
            idea=idea,
            story_lines=story_lines,
            focus_characters=focus,
            duplication_risk=duplication_risk,
            similar_story_ids=similar_story_ids,
        )

    def build_roughcut_job(
        self,
        script: str,
        source_dir: str,
        project_name: str,
        export_jcc: bool = True,
        **kwargs,
    ) -> RoughcutJob:
        brief = self.create_topic_brief(script)
        director_plan = self.build_director_plan(script, brief=brief)
        auto_voiceover = bool(kwargs.get("auto_voiceover", False))
        voiceover_plan = self.build_voiceover_plan(director_plan) if auto_voiceover else None
        return RoughcutJob(
            script=script,
            source_dir=source_dir,
            project_name=project_name,
            export_jcc=export_jcc,
            subtitle_srt=kwargs.get("subtitle_srt"),
            bgm_audio=kwargs.get("bgm_audio"),
            voiceover_audio=kwargs.get("voiceover_audio"),
            video_width=kwargs.get("video_width"),
            video_height=kwargs.get("video_height"),
            fps=kwargs.get("fps", 30),
            story_lines=brief.story_lines,
            focus_characters=brief.focus_characters,
            director_plan=director_plan,
            auto_voiceover=auto_voiceover,
            voiceover_plan=voiceover_plan,
        )

    def build_director_plan(self, script: str, brief: TopicBrief | None = None) -> DirectorPlan:
        brief = brief or self.create_topic_brief(script)
        return self.director_planner.build(script, brief)

    def build_voiceover_plan(self, director_plan: DirectorPlan) -> VoiceoverPlan:
        return self.voiceover_planner.build(director_plan)

    @staticmethod
    def _duplication_risk(similar: list[dict]) -> str:
        if not similar:
            return "低：历史库里没有明显相似故事。"
        top_score = float(similar[0]["score"])
        if top_score >= 0.45:
            return "高：和历史高相似故事过近，建议先换角度。"
        if top_score >= 0.28:
            return "中：题材相近，仍需要明确新的推进点。"
        return "低：可以拍，但仍要接上长期故事线。"
