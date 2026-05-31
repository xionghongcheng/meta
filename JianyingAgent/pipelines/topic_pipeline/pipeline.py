#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Small pipeline for topic planning and script generation."""

from __future__ import annotations

from agents.brain_agent.agent import ContentBrainAgent
from agents.topic_writer_agent.agent import TopicWriterAgent


class TopicPipeline:
    def __init__(self, memory_path: str | None = None):
        self.brain = ContentBrainAgent(memory_path=memory_path)
        self.writer = TopicWriterAgent(memory_path=memory_path)

    def process(self, idea: str) -> dict:
        topic_brief = self.brain.create_topic_brief(idea)
        package = self.writer.create_script_package(idea)
        review = self.writer.review_script(package.markdown)
        return {
            "topic_brief": topic_brief,
            "script_package": package,
            "review": review,
        }
