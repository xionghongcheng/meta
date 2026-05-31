#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Task types routed by the orchestrator."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class TaskType(str, Enum):
    TOPIC = "topic"
    ROUGHCUT = "roughcut"


@dataclass
class TaskRequest:
    user_input: str = ""
    script: str = ""
    source_dir: Optional[str] = None
    project_name: Optional[str] = None
    task_type: Optional[str] = None
    export_jcc: bool = True
    extra: Dict[str, Any] = field(default_factory=dict)
