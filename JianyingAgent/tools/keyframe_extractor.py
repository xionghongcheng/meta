#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Minimal proxy + keyframe extraction for large footage sets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from tools.agent_workspace import AgentWorkspace
from tools.frame_scorer import FrameScorer
from utils import ensure_dir, get_video_duration, run_ffmpeg


class KeyframeExtractor:
    """Generate lightweight proxy videos and a very small frame budget per clip."""

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.frame_scorer = FrameScorer()

    def prepare(self, source_files: List[Dict], workspace: AgentWorkspace) -> List[Dict]:
        manifest = []
        for file_info in source_files:
            item = self._prepare_single(file_info, workspace)
            manifest.append(item)

        manifest_path = workspace.manifest_path()
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        self.logger.info("关键帧索引已生成: %s", manifest_path)
        return manifest

    def _prepare_single(self, file_info: Dict, workspace: AgentWorkspace) -> Dict:
        stem = file_info["id"]
        original_path = Path(file_info["original_path"])
        proxy_path = workspace.proxy_path(stem)
        self._ensure_proxy(original_path, proxy_path)

        duration = float(file_info.get("duration") or get_video_duration(str(original_path)))
        timestamps = self._select_timestamps(duration)
        frame_dir = workspace.keyframe_dir(stem)
        frames = []
        for index, ts in enumerate(timestamps, start=1):
            frame_path = frame_dir / f"{index:03d}_{ts:07.2f}.jpg"
            self._ensure_frame(proxy_path, frame_path, ts)
            frames.append(
                {
                    "index": index,
                    "timestamp": round(ts, 3),
                    "path": str(frame_path),
                }
            )

        visual_summary = self.frame_scorer.summarize_clip(frames)
        index_data = {
            "id": stem,
            "original_path": str(original_path),
            "proxy_path": str(proxy_path),
            "duration": round(duration, 3),
            "frame_budget": len(timestamps),
            "timestamps": [round(ts, 3) for ts in timestamps],
            "frames": frames,
            "visual_summary": visual_summary,
        }
        workspace.frame_index_path(stem).write_text(
            json.dumps(index_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.logger.info(
            "关键帧提取完成: %s -> %s 帧 (proxy=%s, score=%.3f)",
            original_path.name,
            len(frames),
            proxy_path.name,
            visual_summary["quality_score"],
        )
        return index_data

    def _ensure_proxy(self, original_path: Path, proxy_path: Path) -> None:
        if (
            proxy_path.exists()
            and proxy_path.stat().st_size > 0
            and proxy_path.stat().st_mtime >= original_path.stat().st_mtime
        ):
            return

        ensure_dir(str(proxy_path.parent))
        args = [
            "-vf",
            f"scale='min({self.config.PROXY_WIDTH},iw)':-2,fps={self.config.PROXY_FPS}",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            str(self.config.PROXY_CRF),
            "-c:a",
            "aac",
            "-b:a",
            self.config.PROXY_AUDIO_BITRATE,
            "-movflags",
            "+faststart",
            "-y",
        ]
        ok = run_ffmpeg(args, str(original_path), str(proxy_path))
        if not ok:
            raise RuntimeError(f"生成 proxy 失败: {original_path}")

    def _ensure_frame(self, proxy_path: Path, frame_path: Path, timestamp: float) -> None:
        if (
            frame_path.exists()
            and frame_path.stat().st_size > 0
            and frame_path.stat().st_mtime >= proxy_path.stat().st_mtime
        ):
            return

        ensure_dir(str(frame_path.parent))
        args = [
            "-ss",
            f"{timestamp:.3f}",
            "-frames:v",
            "1",
            "-q:v",
            "3",
            "-y",
        ]
        ok = run_ffmpeg(args, str(proxy_path), str(frame_path))
        if not ok:
            raise RuntimeError(f"提取关键帧失败: {proxy_path} @ {timestamp:.3f}s")

    def _select_timestamps(self, duration: float) -> List[float]:
        if duration <= 0:
            return [0.0]

        if duration <= 12:
            count = 1
        elif duration <= 30:
            count = 2
        elif duration <= 90:
            count = 3
        elif duration <= 180:
            count = 4
        elif duration <= 360:
            count = 5
        else:
            count = 6

        margin = min(1.5, max(0.4, duration * 0.06))
        usable = max(duration - margin * 2, duration * 0.4)
        step = usable / max(count - 1, 1)

        if count == 1:
            return [round(duration / 2, 3)]

        timestamps = []
        current = margin
        for _ in range(count):
            timestamps.append(round(min(current, max(duration - 0.25, 0.0)), 3))
            current += step

        deduped = []
        seen = set()
        for ts in timestamps:
            key = round(ts, 2)
            if key not in seen:
                seen.add(key)
                deduped.append(ts)
        return deduped
