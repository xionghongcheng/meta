#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Compatibility facade over the V2 orchestrator.

New code should prefer `orchestrator.JianyingOrchestrator`.
"""

from __future__ import annotations

from datetime import datetime

from infra import Config, create_project_logger
from orchestrator import JianyingOrchestrator


class JianyingAgent:
    """Legacy public API kept stable while the internal architecture moves to V2."""

    def __init__(self):
        self.config = Config
        self.logger = create_project_logger(self.config.OUTPUT_DIR, __name__)
        self.orchestrator = JianyingOrchestrator(config=self.config, logger=self.logger)
        self.project_name = None
        self.selected_segments = []
        self.jcc_project = None
        self.logger.info("剪映Agent初始化完成（V2 facade）")

    def load_skills(self):
        self.orchestrator.load_agents()
        self.logger.info("V2 Agent 和粗剪流水线已加载")

    def process(self, script: str, source_dir: str = None, project_name: str = None, export_jcc: bool = True, **kwargs):
        try:
            self.project_name = project_name or f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            result = self.orchestrator.process_roughcut(
                script=script,
                source_dir=source_dir or self.config.INPUT_DIR,
                project_name=self.project_name,
                export_jcc=export_jcc,
                **kwargs,
            )
            self.selected_segments = result.segments
            self.jcc_project = result.jcc_project
            return {
                "status": result.status,
                "jcc_project": result.jcc_project,
                "segments": result.segments,
                "project_name": result.project_name,
                "message": result.message,
                "final_video": result.final_video,
            }
        except Exception as exc:
            self.logger.error(f"处理失败: {exc}", exc_info=True)
            return {
                "status": "error",
                "message": str(exc),
            }

    def quick_process(self, user_input: str, **kwargs):
        if "脚本" in user_input or "script" in user_input.lower():
            script = user_input.split("脚本")[-1].split("script")[-1].strip("：: \n")
        else:
            script = user_input
        self.logger.info(f"提取到的脚本: {script}")
        return self.process(script, **kwargs)
