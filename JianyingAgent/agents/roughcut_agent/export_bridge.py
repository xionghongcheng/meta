#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Bridge roughcut results to exporter outputs."""

from __future__ import annotations


class ExportBridge:
    @staticmethod
    def select_output(project_path: str, final_video: str | None = None) -> str:
        return project_path or (final_video or "")
