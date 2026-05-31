#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Skill for the script-first planning flow."""

from __future__ import annotations

from agents.brain_agent.agent import ContentBrainAgent
from agents.topic_writer_agent.agent import TopicWriterAgent


class TopicScriptSkill:
    def __init__(self, memory_path: str | None = None):
        self.brain_agent = ContentBrainAgent(memory_path=memory_path)
        self.topic_writer_agent = TopicWriterAgent(memory_path=memory_path)

    def run(self, idea: str) -> dict:
        if not idea.strip():
            raise ValueError("请输入选题想法")

        topic_brief = self.brain_agent.create_topic_brief(idea.strip())
        script_package = self.topic_writer_agent.create_script_package(idea.strip())
        review = self.topic_writer_agent.review_script(script_package.markdown)
        return {
            "workflow": "script_first",
            "topic_brief": topic_brief,
            "script_package": script_package,
            "review": review,
        }
