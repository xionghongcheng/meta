#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Skill wrapper for the roughcut workflow."""

from __future__ import annotations

from agents.brain_agent.agent import ContentBrainAgent
from agents.roughcut_agent.agent import RoughcutAgent
from infra import Config, create_project_logger


class RoughcutSkill:
    def __init__(self, config=None, logger=None, memory_path: str | None = None):
        self.config = config or Config
        self.logger = logger or create_project_logger(self.config.OUTPUT_DIR, __name__)
        self.memory_path = memory_path
        self.brain_agent = ContentBrainAgent(memory_path=memory_path)
        self.roughcut_agent = RoughcutAgent(config=self.config, logger=self.logger)

    def run(self, payload: dict) -> dict:
        script = str(payload.get("script", "")).strip()
        source_dir = str(payload.get("source_dir", "")).strip()
        project_name = str(payload.get("project_name", "")).strip()
        export_jcc = bool(payload.get("export_jcc", True))

        if not script:
            raise ValueError("请填写剪辑脚本")
        if not source_dir:
            raise ValueError("请填写素材目录")
        if not project_name:
            raise ValueError("请填写项目名称")

        self.roughcut_agent.load_pipeline()
        job = self.brain_agent.build_roughcut_job(
            script=script,
            source_dir=source_dir,
            project_name=project_name,
            export_jcc=export_jcc,
            auto_voiceover=bool(payload.get("auto_voiceover", False)),
            subtitle_srt=(payload.get("subtitle_srt") or None),
            bgm_audio=(payload.get("bgm_audio") or None),
            voiceover_audio=(payload.get("voiceover_audio") or None),
            video_width=self._maybe_int(payload.get("video_width")),
            video_height=self._maybe_int(payload.get("video_height")),
        )
        result = self.roughcut_agent.process_job(job)
        return {
            "workflow": "roughcut",
            "result": result,
        }

    @staticmethod
    def _maybe_int(value):
        if value in (None, "", "null"):
            return None
        try:
            return int(value)
        except Exception:
            return None
