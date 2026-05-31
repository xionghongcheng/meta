#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Facade for topic planning and script generation."""

from __future__ import annotations

from .script_reviewer import ScriptReviewer
from .script_writer import ScriptWriter


class TopicWriterAgent:
    def __init__(self, memory_path: str | None = None):
        self.writer = ScriptWriter(memory_path=memory_path)
        self.reviewer = ScriptReviewer()

    def create_brief(self, idea: str):
        return self.writer.create_brief(idea)

    def create_script_package(self, idea: str):
        return self.writer.create_script_package(idea)

    def review_script(self, markdown: str) -> dict:
        return self.reviewer.review_markdown(markdown)
