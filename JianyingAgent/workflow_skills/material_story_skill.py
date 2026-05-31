#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Skill for the material-first story extraction workflow."""

from __future__ import annotations

import os
from collections import Counter
from typing import Any

from agents.brain_agent.agent import ContentBrainAgent
from infra import Config, create_project_logger
from pipelines.roughcut_pipeline.pipeline import RoughcutPipeline
from tools.agent_workspace import AgentWorkspace


class MaterialStorySkill:
    def __init__(self, config=None, logger=None, memory_path: str | None = None):
        self.config = config or Config
        self.logger = logger or create_project_logger(self.config.OUTPUT_DIR, __name__)
        self.brain_agent = ContentBrainAgent(memory_path=memory_path)
        self.pipeline = RoughcutPipeline(self.config, self.logger)

    def run(self, payload: dict[str, Any]) -> dict:
        source_dir = str(payload.get("source_dir", "")).strip()
        notes = str(payload.get("notes", "")).strip()
        project_name = str(payload.get("project_name", "")).strip() or os.path.basename(source_dir.rstrip("\\/"))

        if not source_dir:
            raise ValueError("请填写素材目录")
        if not os.path.isdir(source_dir):
            raise ValueError(f"素材目录不存在: {source_dir}")

        workspace = AgentWorkspace.from_source_dir(source_dir)
        source_files = self.pipeline.extractor.extract(
            source_dir,
            audio_cache_dir=str(workspace.audio_cache_dir),
            proxy_dir=str(workspace.proxy_dir),
        )
        if not source_files:
            raise ValueError("未找到可处理的视频素材")

        transcripts = self.pipeline.transcriber.transcribe(
            source_files,
            output_dir=str(workspace.transcripts_dir),
        )
        if not transcripts:
            raise ValueError("转写未产出有效结果")

        source_map = {item["id"]: item for item in source_files}
        for file_id, transcript in transcripts.items():
            if file_id in source_map:
                transcript["video_path"] = source_map[file_id].get("original_path", "")

        keyframe_manifest = self.pipeline.keyframe_extractor.prepare(source_files, workspace)
        summary = self._build_summary(project_name, source_files, transcripts, keyframe_manifest)
        intent_seed = notes or summary["combined_text"] or project_name
        topic_brief = self.brain_agent.create_topic_brief(intent_seed)
        directions = self._build_candidate_directions(summary, topic_brief, notes)

        return {
            "workflow": "material_first",
            "project_name": project_name,
            "workspace_dir": str(workspace.root_dir),
            "summary": summary,
            "topic_brief": topic_brief,
            "keyframe_manifest": keyframe_manifest,
            "directions": directions,
            "next_step_suggestion": self._build_next_step(directions),
        }

    def _build_summary(
        self,
        project_name: str,
        source_files: list[dict],
        transcripts: dict[str, dict],
        keyframe_manifest: list[dict],
    ) -> dict:
        total_duration = sum(float(item.get("duration", 0.0)) for item in source_files)
        combined_segments = []
        combined_text_parts = []

        for file_id, transcript in transcripts.items():
            full_text = str(transcript.get("full_text", "")).strip()
            if full_text:
                combined_text_parts.append(full_text)
            for segment in transcript.get("segments", []):
                text = str(segment.get("text", "")).strip()
                if not text:
                    continue
                combined_segments.append(
                    {
                        "file_id": file_id,
                        "start": float(segment["start"]),
                        "end": float(segment["end"]),
                        "text": text,
                    }
                )

        combined_segments.sort(key=lambda item: (item["file_id"], item["start"]))
        highlights = sorted(combined_segments, key=lambda item: len(item["text"]), reverse=True)[:8]
        combined_text = " ".join(combined_text_parts).strip()

        word_counts = Counter()
        for text in combined_text_parts:
            normalized = text.replace("，", " ").replace("。", " ").replace("、", " ")
            for chunk in normalized.split():
                chunk = chunk.strip()
                if len(chunk) >= 2:
                    word_counts[chunk] += 1

        visual_rank = sorted(
            keyframe_manifest,
            key=lambda item: item.get("visual_summary", {}).get("quality_score", 0.0),
            reverse=True,
        )[:6]
        top_visual_clips = [
            {
                "id": item["id"],
                "quality_score": item.get("visual_summary", {}).get("quality_score", 0.0),
                "best_frame_path": item.get("visual_summary", {}).get("best_frame_path", ""),
                "diversity_score": item.get("visual_summary", {}).get("diversity_score", 0.0),
            }
            for item in visual_rank
        ]

        return {
            "project_name": project_name,
            "file_count": len(source_files),
            "total_duration_seconds": round(total_duration, 2),
            "transcript_file_count": len(transcripts),
            "combined_text": combined_text[:1200],
            "highlights": highlights,
            "top_phrases": [item for item in word_counts.most_common(10)],
            "top_visual_clips": top_visual_clips,
        }

    def _build_candidate_directions(self, summary: dict, topic_brief, notes: str) -> list[dict]:
        story_lines = topic_brief.story_lines or ["家庭重建", "照护者成长线"]
        focus = topic_brief.focus_characters or ["me", "mom", "dad", "girlfriend"]
        highlight_texts = [item["text"] for item in summary["highlights"][:3]]
        top_phrases = [item[0] for item in summary["top_phrases"][:3]]
        top_visual = [item["id"] for item in summary.get("top_visual_clips", [])[:3]]

        anchor = "；".join(highlight_texts) if highlight_texts else "素材里优先找最有反应的画面"
        phrase_anchor = "、".join(top_phrases) if top_phrases else "真实反应"
        visual_anchor = "、".join(top_visual) if top_visual else "当前视觉最强镜头"

        directions = []
        for index, line in enumerate(story_lines[:3], start=1):
            directions.append(
                {
                    "id": f"direction_{index}",
                    "story_line": line,
                    "focus_characters": focus[:2],
                    "title": f"{line}方向 {index}",
                    "angle": self._angle_for_story_line(line),
                    "why": f"结合当前素材转写和内容大脑，这批素材更适合从“{line}”切入。文本重点参考：{phrase_anchor}。",
                    "visual_focus": f"优先检查这些视觉质量更高的镜头：{visual_anchor}。",
                    "voiceover_seed": f"如果这期走“{line}”，可以围绕这些瞬间写配音：{anchor}",
                    "notes": notes or "",
                }
            )
        return directions

    @staticmethod
    def _angle_for_story_line(story_line: str) -> str:
        mapping = {
            "妈妈恢复线": "重点讲她今天有没有重新获得选择和生活感。",
            "爸爸适应线": "重点讲他有没有少闯一点祸，或者露出一点笨拙温柔。",
            "女朋友共建线": "重点讲她如何把混乱场面变得更能生活。",
            "照护者成长线": "重点讲你怎么从现场混乱里找到这一期真正要讲的东西。",
            "家庭重建": "重点讲这件普通事如何让家更像一个家。",
        }
        return mapping.get(story_line, "重点从发生过的真实瞬间里提炼这一期最能成立的主线。")

    @staticmethod
    def _build_next_step(directions: list[dict]) -> str:
        if not directions:
            return "先补充素材说明，再继续提炼故事方向。"
        first = directions[0]
        return (
            f"建议先选择“{first['title']}”，把它改写成正式配音稿，"
            "再进入配音驱动画面匹配或自动粗剪。"
        )
