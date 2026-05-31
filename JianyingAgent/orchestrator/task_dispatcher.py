#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""High-level dispatcher across the V2 agents."""

from __future__ import annotations

from agents.brain_agent.agent import ContentBrainAgent
from agents.roughcut_agent.agent import RoughcutAgent
from agents.topic_writer_agent.agent import TopicWriterAgent
from contracts import RoughcutResult
from workflows import WorkflowService

from .router import TaskRouter
from .task_types import TaskRequest, TaskType


class JianyingOrchestrator:
    def __init__(self, config=None, logger=None, memory_path: str | None = None):
        self.router = TaskRouter()
        self.brain_agent = ContentBrainAgent(memory_path=memory_path)
        self.topic_writer_agent = TopicWriterAgent(memory_path=memory_path)
        self.roughcut_agent = RoughcutAgent(config=config, logger=logger)
        self.workflow_service = WorkflowService(config=config, logger=logger, memory_path=memory_path)

    def load_agents(self):
        self.roughcut_agent.load_pipeline()

    def dispatch(self, request: TaskRequest) -> dict:
        task_type = self.router.route(request)
        if task_type == TaskType.TOPIC:
            return self.process_topic(request.user_input or request.script)

        result = self.process_roughcut(
            script=request.script or request.user_input,
            source_dir=request.source_dir or "",
            project_name=request.project_name or "project",
            export_jcc=request.export_jcc,
            **request.extra,
        )
        return {
            "status": result.status,
            "project_name": result.project_name,
            "jcc_project": result.jcc_project,
            "final_video": result.final_video,
            "segments": result.segments,
            "message": result.message,
        }

    def process_topic(self, idea: str) -> dict:
        topic_brief = self.brain_agent.create_topic_brief(idea)
        script_package = self.topic_writer_agent.create_script_package(idea)
        review = self.topic_writer_agent.review_script(script_package.markdown)
        return {
            "topic_brief": topic_brief,
            "script_package": script_package,
            "review": review,
        }

    def process_roughcut(self, script: str, source_dir: str, project_name: str, export_jcc: bool = True, **kwargs) -> RoughcutResult:
        job = self.brain_agent.build_roughcut_job(
            script=script,
            source_dir=source_dir,
            project_name=project_name,
            export_jcc=export_jcc,
            **kwargs,
        )
        return self.roughcut_agent.process_job(job)

    def list_workflows(self) -> list[dict]:
        return self.workflow_service.workflows()

    def advise_workflow(self, message: str) -> dict:
        return self.workflow_service.advise(message)

    def run_workflow(self, workflow_id: str, payload: dict) -> dict:
        return self.workflow_service.run(workflow_id, payload)
