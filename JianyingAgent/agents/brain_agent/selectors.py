#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Simple routing heuristics for the content brain."""

from __future__ import annotations

from orchestrator.task_types import TaskType


def detect_task_type(source_dir: str | None = None, explicit_task: str | None = None) -> TaskType:
    if explicit_task == TaskType.TOPIC.value:
        return TaskType.TOPIC
    if explicit_task == TaskType.ROUGHCUT.value:
        return TaskType.ROUGHCUT
    if source_dir:
        return TaskType.ROUGHCUT
    return TaskType.TOPIC
