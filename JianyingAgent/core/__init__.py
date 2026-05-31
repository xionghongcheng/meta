#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Legacy compatibility exports.

V2 的主入口已经迁到 `orchestrator/`、`agents/` 和 `apps/`。
这里保留对 `from core import ...` 的兼容支持，供旧脚本继续运行。
"""

from .agent import JianyingAgent
from .character_profiles import CHARACTER_PROFILES, CharacterProfile
from .content_memory import ContentMemory, ContentStory
from .script_assistant import TopicScriptAssistant

__all__ = [
    'JianyingAgent',
    'CHARACTER_PROFILES',
    'CharacterProfile',
    'ContentMemory',
    'ContentStory',
    'TopicScriptAssistant',
]
