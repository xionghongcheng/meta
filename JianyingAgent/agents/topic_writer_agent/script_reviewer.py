#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Very small structural reviewer for generated script packages."""

from __future__ import annotations


class ScriptReviewer:
    REQUIRED_SECTIONS = (
        "## 开头钩子",
        "## 故事梗概",
        "## 必拍画面",
        "## 必收对白",
        "## 配音大纲",
        "## 粗剪提示",
    )

    def review_markdown(self, markdown: str) -> dict:
        missing = [section for section in self.REQUIRED_SECTIONS if section not in markdown]
        return {
            "verdict": "通过" if not missing else "小改",
            "missing_sections": missing,
        }
