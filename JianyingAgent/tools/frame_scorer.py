#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Lightweight visual scoring for extracted keyframes."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import numpy as np
from PIL import Image, ImageFilter


class FrameScorer:
    """Compute cheap image metrics to reduce later model cost."""

    def score_frame(self, image_path: str | Path) -> Dict:
        path = Path(image_path)
        with Image.open(path) as image:
            rgb = image.convert("RGB")
            gray = rgb.convert("L")

            rgb_small = rgb.resize((160, max(90, int(rgb.height * 160 / max(rgb.width, 1)))), Image.Resampling.BILINEAR)
            gray_small = gray.resize((160, max(90, int(gray.height * 160 / max(gray.width, 1)))), Image.Resampling.BILINEAR)

            rgb_np = np.asarray(rgb_small, dtype=np.float32)
            gray_np = np.asarray(gray_small, dtype=np.float32)

            brightness = float(gray_np.mean())
            contrast = float(gray_np.std())
            edge_image = gray_small.filter(ImageFilter.FIND_EDGES)
            edge_np = np.asarray(edge_image, dtype=np.float32)
            sharpness = float(edge_np.mean())
            saturation = float((rgb_np.max(axis=2) - rgb_np.min(axis=2)).mean())

            metrics = {
                "brightness": round(brightness, 3),
                "contrast": round(contrast, 3),
                "sharpness": round(sharpness, 3),
                "saturation": round(saturation, 3),
            }
            metrics["quality_score"] = round(self._quality_score(metrics), 3)
            return metrics

    def summarize_clip(self, frames: List[Dict]) -> Dict:
        if not frames:
            return {
                "quality_score": 0.0,
                "best_frame_index": None,
                "best_frame_path": "",
                "frame_count": 0,
                "metrics": [],
            }

        scored = []
        for item in frames:
            metrics = self.score_frame(item["path"])
            scored.append(
                {
                    **item,
                    "metrics": metrics,
                }
            )

        best = max(scored, key=lambda item: item["metrics"]["quality_score"])

        diversity = self._diversity_score(scored)
        clip_quality = (sum(item["metrics"]["quality_score"] for item in scored) / len(scored)) * 0.75 + diversity * 0.25

        return {
            "quality_score": round(clip_quality, 3),
            "best_frame_index": best["index"],
            "best_frame_path": best["path"],
            "diversity_score": round(diversity, 3),
            "frame_count": len(scored),
            "metrics": scored,
        }

    @staticmethod
    def _quality_score(metrics: Dict) -> float:
        brightness = metrics["brightness"]
        contrast = metrics["contrast"]
        sharpness = metrics["sharpness"]
        saturation = metrics["saturation"]

        # Prefer mid-range exposure, enough contrast and enough edge detail.
        exposure_score = max(0.0, 1.0 - abs(brightness - 128.0) / 128.0)
        contrast_score = min(1.0, contrast / 64.0)
        sharpness_score = min(1.0, sharpness / 48.0)
        saturation_score = min(1.0, saturation / 72.0)

        return exposure_score * 0.25 + contrast_score * 0.25 + sharpness_score * 0.35 + saturation_score * 0.15

    @staticmethod
    def _diversity_score(scored_frames: List[Dict]) -> float:
        if len(scored_frames) <= 1:
            return 0.5

        arrays = []
        for item in scored_frames:
            with Image.open(item["path"]) as image:
                gray = image.convert("L").resize((64, 36), Image.Resampling.BILINEAR)
                arrays.append(np.asarray(gray, dtype=np.float32).flatten())

        distances = []
        for left, right in zip(arrays, arrays[1:]):
            diff = np.abs(left - right).mean() / 255.0
            distances.append(diff)
        if not distances:
            return 0.5
        return min(1.0, float(sum(distances) / len(distances)) * 2.0)
