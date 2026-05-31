#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Lazy agent exports to avoid package import cycles."""

from __future__ import annotations

__all__ = [
    "ContentBrainAgent",
    "TopicWriterAgent",
    "RoughcutAgent",
]


def __getattr__(name: str):
    if name == "ContentBrainAgent":
        from .brain_agent.agent import ContentBrainAgent

        return ContentBrainAgent
    if name == "TopicWriterAgent":
        from .topic_writer_agent.agent import TopicWriterAgent

        return TopicWriterAgent
    if name == "RoughcutAgent":
        from .roughcut_agent.agent import RoughcutAgent

        return RoughcutAgent
    raise AttributeError(name)
