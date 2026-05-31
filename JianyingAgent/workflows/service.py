#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Workflow runner that composes lower-level skills."""

from __future__ import annotations

from infra import Config, create_project_logger
from workflow_skills import (
    MaterialStorySkill,
    RoughcutSkill,
    StoryMemorySkill,
    TopicScriptSkill,
    WorkflowAdvisorSkill,
)

from .registry import list_workflows


class WorkflowService:
    def __init__(self, config=None, logger=None, memory_path: str | None = None):
        self.config = config or Config
        self.logger = logger or create_project_logger(self.config.OUTPUT_DIR, __name__)
        self.memory_path = memory_path

        self.memory_skill = StoryMemorySkill(memory_path=memory_path)
        self.topic_script_skill = TopicScriptSkill(memory_path=memory_path)
        self.material_story_skill = MaterialStorySkill(config=self.config, logger=self.logger, memory_path=memory_path)
        self.roughcut_skill = RoughcutSkill(config=self.config, logger=self.logger, memory_path=memory_path)
        self.workflow_advisor_skill = WorkflowAdvisorSkill(config=self.config, logger=self.logger)

    def workflows(self) -> list[dict]:
        return list_workflows()

    def advise(self, message: str) -> dict:
        return self.workflow_advisor_skill.advise(message)

    def run(self, workflow_id: str, payload: dict) -> dict:
        if workflow_id == "script_first":
            return self.topic_script_skill.run(str(payload.get("idea", "")))
        if workflow_id == "material_first":
            return self.material_story_skill.run(payload)
        if workflow_id == "roughcut":
            return self.roughcut_skill.run(payload)
        raise ValueError(f"未知 workflow: {workflow_id}")

    def profile(self, memory_path: str | None = None) -> dict:
        return self.memory_skill.profile(memory_path=memory_path)

    def ingest(self, files, out: str | None = None) -> dict:
        return self.memory_skill.ingest(files=files, out=out)
