#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Per-project workspace layout under the source material directory."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AgentWorkspace:
    source_dir: Path
    root_dir: Path
    proxy_dir: Path
    transcripts_dir: Path
    keyframes_dir: Path
    frame_index_dir: Path
    analysis_dir: Path
    scripts_dir: Path
    roughcut_dir: Path
    logs_dir: Path
    cache_dir: Path
    audio_cache_dir: Path
    segment_cache_dir: Path

    @classmethod
    def from_source_dir(cls, source_dir: str | Path) -> "AgentWorkspace":
        source = Path(source_dir).resolve()
        root = source / "agent_workspace"

        proxy_dir = root / "01_proxy"
        transcripts_dir = root / "02_transcripts"
        keyframes_dir = root / "03_keyframes"
        frame_index_dir = root / "04_frame_index"
        analysis_dir = root / "05_analysis"
        scripts_dir = root / "06_scripts"
        roughcut_dir = root / "07_roughcut"
        logs_dir = root / "08_logs"
        cache_dir = root / "_cache"
        audio_cache_dir = cache_dir / "audio"
        segment_cache_dir = cache_dir / "segments"

        for path in [
            root,
            proxy_dir,
            transcripts_dir,
            keyframes_dir,
            frame_index_dir,
            analysis_dir,
            scripts_dir,
            roughcut_dir,
            logs_dir,
            cache_dir,
            audio_cache_dir,
            segment_cache_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)

        return cls(
            source_dir=source,
            root_dir=root,
            proxy_dir=proxy_dir,
            transcripts_dir=transcripts_dir,
            keyframes_dir=keyframes_dir,
            frame_index_dir=frame_index_dir,
            analysis_dir=analysis_dir,
            scripts_dir=scripts_dir,
            roughcut_dir=roughcut_dir,
            logs_dir=logs_dir,
            cache_dir=cache_dir,
            audio_cache_dir=audio_cache_dir,
            segment_cache_dir=segment_cache_dir,
        )

    def frame_index_path(self, stem: str) -> Path:
        return self.frame_index_dir / f"{stem}.json"

    def keyframe_dir(self, stem: str) -> Path:
        path = self.keyframes_dir / stem
        path.mkdir(parents=True, exist_ok=True)
        return path

    def proxy_path(self, stem: str) -> Path:
        return self.proxy_dir / f"{stem}_proxy.mp4"

    def audio_cache_path(self, stem: str) -> Path:
        return self.audio_cache_dir / f"{stem}.m4a"

    def roughcut_info_path(self, project_name: str) -> Path:
        return self.roughcut_dir / f"{project_name}.jcc"

    def manifest_path(self) -> Path:
        return self.frame_index_dir / "manifest.json"
