#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Execution pipeline for the automatic roughcut chain."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from .analyzer import Skill3Analyzer
from .editor import Skill4Editor
from .exporter import Skill5Exporter
from .extractor import Skill1Extractor
from .transcriber import Skill2Transcriber
from tools.agent_workspace import AgentWorkspace
from tools.keyframe_extractor import KeyframeExtractor
from tools.segment_ranker import SegmentRanker
from tools.voiceover_synthesizer import VoiceoverSynthesizer


class RoughcutPipeline:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.extractor = Skill1Extractor(config, logger)
        self.transcriber = Skill2Transcriber(config, logger)
        self.analyzer = Skill3Analyzer(config, logger)
        self.editor = Skill4Editor(config, logger)
        self.exporter = Skill5Exporter(config, logger)
        self.keyframe_extractor = KeyframeExtractor(config, logger)
        self.segment_ranker = SegmentRanker()
        self.voiceover_synthesizer = VoiceoverSynthesizer(logger)

    def process(self, script: str, source_dir: str | None = None, project_name: str | None = None, export_jcc: bool = True, **kwargs) -> Dict:
        project_name = project_name or f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        source_dir = source_dir or self.config.INPUT_DIR
        director_plan = kwargs.get("director_plan")
        workspace = AgentWorkspace.from_source_dir(source_dir) if source_dir and source_dir != self.config.INPUT_DIR else None
        source_files = self.extractor.extract(
            source_dir,
            audio_cache_dir=str(workspace.audio_cache_dir) if workspace else None,
            proxy_dir=str(workspace.proxy_dir) if workspace else None,
        )
        if not source_files:
            return {
                "status": "error",
                "jcc_project": "",
                "segments": [],
                "project_name": project_name,
                "final_video": None,
                "message": "未找到可处理的视频素材",
            }

        transcripts = self.transcriber.transcribe(
            source_files,
            output_dir=str(workspace.transcripts_dir) if workspace else None,
        )
        if not transcripts:
            return {
                "status": "error",
                "jcc_project": "",
                "segments": [],
                "project_name": project_name,
                "final_video": None,
                "message": "转写未产出有效结果",
            }

        source_map = {item["id"]: item for item in source_files}
        for file_id, transcript in transcripts.items():
            if file_id in source_map:
                transcript["video_path"] = source_map[file_id].get("original_path", "")

        keyframe_manifest = []
        if workspace:
            keyframe_manifest = self.keyframe_extractor.prepare(source_files, workspace)
            self._save_director_plan(workspace, director_plan)

        selected_segments = self.analyzer.analyze(
            script,
            transcripts,
            director_plan=director_plan,
            output_dir=str(workspace.analysis_dir) if workspace else None,
        )
        selected_segments = self.segment_ranker.annotate(
            selected_segments,
            keyframe_manifest,
            script=script,
        )
        selected_segments = self.segment_ranker.cap_long_segments(
            selected_segments,
            script=script,
        )
        selected_segments = self.segment_ranker.trim_to_target(
            selected_segments,
            script=script,
            min_segments=3,
        )
        selected_segments = self._hydrate_segment_paths(selected_segments, source_map)
        selected_segments = self._filter_invalid_segments(selected_segments)
        selected_segments = self.segment_ranker.sort_for_roughcut(selected_segments, director_plan=director_plan)
        voiceover_plan = None
        if kwargs.get("auto_voiceover"):
            voiceover_plan = self.voiceover_synthesizer.synthesize(
                kwargs.get("voiceover_plan"),
                selected_segments,
                workspace,
            )
        if not selected_segments:
            return {
                "status": "error",
                "jcc_project": "",
                "segments": [],
                "project_name": project_name,
                "final_video": None,
                "message": "没有筛选到可用片段",
            }

        final_video = None
        if not export_jcc:
            final_video = self.editor.edit(
                selected_segments,
                project_name,
                temp_dir=str(workspace.segment_cache_dir) if workspace else None,
                output_dir=str(workspace.roughcut_dir) if workspace else None,
            )

        if export_jcc:
            project_path = self.exporter.export(
                selected_segments,
                project_name,
                subtitle_srt=kwargs.get("subtitle_srt"),
                bgm_audio=kwargs.get("bgm_audio"),
                voiceover_audio=kwargs.get("voiceover_audio"),
                voiceover_plan=voiceover_plan,
                video_width=kwargs.get("video_width", self.config.CANVAS_WIDTH),
                video_height=kwargs.get("video_height", self.config.CANVAS_HEIGHT),
                fps=kwargs.get("fps", 30),
                export_dir=str(workspace.roughcut_dir) if workspace else self.exporter.export_dir,
            )
        else:
            project_path = self.exporter.export_simple(final_video, project_name) if final_video else ""

        return {
            "status": "success",
            "jcc_project": project_path,
            "segments": selected_segments,
            "project_name": project_name,
            "final_video": final_video,
            "message": "",
            "workspace_dir": str(workspace.root_dir) if workspace else "",
            "keyframe_manifest": keyframe_manifest,
            "timeline_sort": selected_segments[0].get("timeline_sort_mode", "") if selected_segments else "",
            "director_plan": director_plan,
            "voiceover_plan": voiceover_plan,
        }

    @staticmethod
    def _hydrate_segment_paths(selected_segments: List[Dict], source_map: Dict[str, Dict]) -> List[Dict]:
        for segment in selected_segments:
            file_id = segment.get("file_id", "")
            if file_id in source_map:
                segment["video_path"] = source_map[file_id].get("original_path", "")
                segment["filename"] = source_map[file_id].get("filename", "")
            segment["duration"] = float(segment.get("duration", max(0.0, segment.get("end", 0) - segment.get("start", 0))))
        return selected_segments

    @staticmethod
    def _filter_invalid_segments(selected_segments: List[Dict]) -> List[Dict]:
        cleaned = []
        for segment in selected_segments:
            if not segment.get("video_path"):
                continue
            if float(segment.get("duration", 0.0)) <= 0:
                continue
            cleaned.append(segment)
        return cleaned

    @staticmethod
    def _save_director_plan(workspace: AgentWorkspace, director_plan) -> None:
        if not director_plan:
            return
        path = Path(workspace.scripts_dir) / "director_plan.json"
        path.write_text(json.dumps(director_plan, ensure_ascii=False, indent=2, default=lambda x: x.__dict__), encoding="utf-8")
