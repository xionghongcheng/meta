#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Facade for the automatic roughcut pipeline."""

from __future__ import annotations

from contracts import RoughcutJob, RoughcutResult
from infra import Config, create_project_logger
from pipelines.roughcut_pipeline import RoughcutPipeline

from .segment_selector import SegmentSelector


class RoughcutAgent:
    def __init__(self, config=None, logger=None):
        self.config = config or Config
        self.logger = logger or create_project_logger(self.config.OUTPUT_DIR, __name__)
        self.pipeline = RoughcutPipeline(self.config, self.logger)

    def load_pipeline(self):
        return self.pipeline

    def process(self, script: str, source_dir: str, project_name: str, export_jcc: bool = True, **kwargs) -> dict:
        result = self.pipeline.process(
            script=script,
            source_dir=source_dir,
            project_name=project_name,
            export_jcc=export_jcc,
            **kwargs,
        )
        result["segments"] = SegmentSelector.normalize(result.get("segments", []))
        return result

    def process_job(self, job: RoughcutJob) -> RoughcutResult:
        result = self.process(
            script=job.script,
            source_dir=job.source_dir,
            project_name=job.project_name,
            export_jcc=job.export_jcc,
            subtitle_srt=job.subtitle_srt,
            bgm_audio=job.bgm_audio,
            voiceover_audio=job.voiceover_audio,
            video_width=job.video_width,
            video_height=job.video_height,
            fps=job.fps,
            director_plan=job.director_plan,
            auto_voiceover=job.auto_voiceover,
            voiceover_plan=job.voiceover_plan,
        )
        return RoughcutResult(
            status=result.get("status", "error"),
            project_name=result.get("project_name", job.project_name),
            jcc_project=result.get("jcc_project", ""),
            final_video=result.get("final_video"),
            segments=result.get("segments", []),
            message=result.get("message", ""),
            workspace_dir=result.get("workspace_dir", ""),
            keyframe_manifest=result.get("keyframe_manifest", []),
            timeline_sort=result.get("timeline_sort", ""),
            director_plan=result.get("director_plan"),
            voiceover_plan=result.get("voiceover_plan"),
        )
