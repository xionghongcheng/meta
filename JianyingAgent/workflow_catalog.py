#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Single source of truth for workflow definitions."""

from __future__ import annotations


def list_workflows() -> list[dict]:
    return [
        {
            "id": "script_first",
            "name": "先想内容再拍",
            "description": "适合明确任务型、商单型或你提前知道要拍什么的内容。",
            "steps": ["选题", "脚本建议", "拍摄清单", "再去拍"],
            "inputs": ["idea", "memory_path"],
        },
        {
            "id": "material_first",
            "name": "先拍素材再提炼",
            "description": "适合日常生活先发生，拍完后再决定这一期到底讲什么。",
            "steps": ["读取素材", "转写", "提炼故事方向", "生成下一步建议"],
            "inputs": ["source_dir", "project_name", "notes"],
        },
        {
            "id": "roughcut",
            "name": "直接自动粗剪",
            "description": "适合你已经知道脚本和目标，只需要快速粗剪出时间线。",
            "steps": ["扫描素材", "转写", "筛片", "导出剪映草稿"],
            "inputs": ["source_dir", "script", "project_name"],
        },
    ]
