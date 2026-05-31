#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Lazy orchestrator exports to avoid package import cycles."""

from __future__ import annotations

from .task_types import TaskRequest, TaskType

__all__ = ["JianyingOrchestrator", "TaskType", "TaskRequest"]


def __getattr__(name: str):
    if name == "JianyingOrchestrator":
        from .task_dispatcher import JianyingOrchestrator

        return JianyingOrchestrator
    raise AttributeError(name)
