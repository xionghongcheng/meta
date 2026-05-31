#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Legacy compatibility exports for the roughcut pipeline.

V2 的正式粗剪实现位于 `pipelines/roughcut_pipeline/`。
这里保留旧导入路径，避免历史代码直接失效。
"""

from .skill_1_extractor import Skill1Extractor
from .skill_2_transcriber import Skill2Transcriber
from .skill_3_analyzer import Skill3Analyzer
from .skill_4_editor import Skill4Editor
from .skill_5_exporter import Skill5Exporter

__all__ = [
    'Skill1Extractor',
    'Skill2Transcriber',
    'Skill3Analyzer',
    'Skill4Editor',
    'Skill5Exporter'
]
