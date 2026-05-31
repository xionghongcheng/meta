#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Request router."""

from __future__ import annotations

from .task_types import TaskRequest, TaskType


class TaskRouter:
    def route(self, request: TaskRequest) -> TaskType:
        if request.task_type == TaskType.TOPIC.value:
            return TaskType.TOPIC
        if request.task_type == TaskType.ROUGHCUT.value:
            return TaskType.ROUGHCUT
        if request.source_dir:
            return TaskType.ROUGHCUT
        return TaskType.TOPIC
