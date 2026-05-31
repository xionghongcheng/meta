#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""剪映工程文件导出（pyJianYingDraft 版）。"""

from __future__ import annotations

import json
import os
from typing import Dict, List

from pyJianYingDraft import AudioSegment, DraftFolder, SEC, Timerange, TrackType, VideoSegment

from utils import ensure_dir, get_video_duration


JIANYING_DRAFT_ROOT = os.path.expandvars(os.path.expanduser(os.getenv("JIANYING_DRAFT_ROOT", "F:/Media/02_剪映草稿")))


class Skill5Exporter:
    """剪映工程文件导出技能。"""

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.export_dir = ensure_dir(os.path.join(config.OUTPUT_DIR, "jianying_projects"))

    def export(self, video_segments: List[Dict], project_name: str, **kwargs) -> str:
        self.logger.info(f"开始生成剪映草稿: {project_name}")

        subtitle_srt = kwargs.get("subtitle_srt")
        bgm_audio = kwargs.get("bgm_audio")
        voiceover_audio = kwargs.get("voiceover_audio")
        voiceover_plan = kwargs.get("voiceover_plan")
        video_width = kwargs.get("video_width", self.config.CANVAS_WIDTH)
        video_height = kwargs.get("video_height", self.config.CANVAS_HEIGHT)
        fps = kwargs.get("fps", 30)

        draft_folder = DraftFolder(JIANYING_DRAFT_ROOT)
        script = draft_folder.create_draft(
            project_name,
            video_width,
            video_height,
            fps,
            allow_replace=True,
        )

        script.add_track(TrackType.video, "video")

        cur_pos_us = 0
        last_end_us = 0
        exported_segments = []

        for seg in video_segments:
            video_path = seg.get("video_path", "")
            if not video_path or not os.path.exists(video_path):
                self.logger.warning(f"跳过无效路径: {video_path}")
                continue

            src_start = float(seg.get("start", 0))
            src_end = float(seg.get("end", src_start + seg.get("duration", 0)))
            clip_dur = src_end - src_start
            if clip_dur < 0.5:
                continue

            source_start_us = round(src_start * SEC)
            source_dur_us = round(clip_dur * SEC)
            target_start_us = max(cur_pos_us, last_end_us)

            target_range = Timerange(target_start_us, source_dur_us)
            source_range = Timerange(source_start_us, source_dur_us)

            vseg = self._build_video_segment(video_path, target_range, source_range)
            if vseg is None:
                continue

            vseg.add_background_filling("blur", blur=0.0625)

            try:
                script.add_segment(vseg, "video")
            except Exception as exc:
                if "overlaps" not in str(exc):
                    raise

                safe_start_us = last_end_us
                self.logger.warning(
                    "检测到时间轴重叠，自动平移片段: %s -> %.3fs",
                    os.path.basename(video_path),
                    safe_start_us / SEC,
                )
                vseg.target_timerange.start = safe_start_us
                script.add_segment(vseg, "video")

            actual_source_start = vseg.source_timerange.start / SEC
            actual_source_end = (vseg.source_timerange.start + vseg.source_timerange.duration) / SEC
            actual_timeline_start = vseg.target_timerange.start / SEC
            actual_timeline_end = (vseg.target_timerange.start + vseg.target_timerange.duration) / SEC
            exported_segment = dict(seg)
            exported_segment["actual_source_start"] = round(actual_source_start, 3)
            exported_segment["actual_source_end"] = round(actual_source_end, 3)
            exported_segment["actual_timeline_start"] = round(actual_timeline_start, 3)
            exported_segment["actual_timeline_end"] = round(actual_timeline_end, 3)
            exported_segment["actual_duration"] = round(actual_timeline_end - actual_timeline_start, 3)
            exported_segments.append(exported_segment)

            cur_pos_us = vseg.end
            last_end_us = vseg.end

        if voiceover_audio and os.path.exists(voiceover_audio) and cur_pos_us > 0:
            self.logger.info(f"添加配音音轨: {voiceover_audio}")
            script.add_track(TrackType.audio, "voiceover")
            voiceover_dur_us = round(max(0.0, get_video_duration(voiceover_audio)) * SEC)
            if voiceover_dur_us > 0:
                voiceover_target = Timerange(0, min(cur_pos_us, voiceover_dur_us))
                aseg = self._build_audio_segment(voiceover_audio, voiceover_target, volume=1.0)
                if aseg is not None:
                    script.add_segment(aseg, "voiceover")

        if voiceover_plan and getattr(voiceover_plan, "lines", None) and cur_pos_us > 0:
            line_segments = [item for item in voiceover_plan.lines if item.audio_path and item.duration_seconds > 0]
            if line_segments:
                self.logger.info("添加自动配音分句音轨")
                script.add_track(TrackType.audio, "voiceover_auto")
                for line in line_segments:
                    start_us = round(float(line.preferred_start_seconds or 0.0) * SEC)
                    duration_us = round(float(line.duration_seconds or 0.0) * SEC)
                    if duration_us <= 0:
                        continue
                    target = Timerange(start_us, duration_us)
                    aseg = self._build_audio_segment(line.audio_path, target, volume=1.0)
                    if aseg is not None:
                        script.add_segment(aseg, "voiceover_auto")

        if bgm_audio and os.path.exists(bgm_audio) and cur_pos_us > 0:
            self.logger.info(f"添加背景音乐: {bgm_audio}")
            script.add_track(TrackType.audio, "bgm")
            bgm_target = Timerange(0, cur_pos_us)
            bgm_volume = 0.12 if (voiceover_audio or (voiceover_plan and getattr(voiceover_plan, "lines", None))) else 0.3
            aseg = AudioSegment(bgm_audio, bgm_target, volume=bgm_volume)
            script.add_segment(aseg, "bgm")

        if subtitle_srt and os.path.exists(subtitle_srt):
            self.logger.info(f"导入字幕: {subtitle_srt}")
            script.import_srt(subtitle_srt, "subtitle")

        script.save()

        total_dur_sec = cur_pos_us / SEC
        draft_dir = os.path.join(JIANYING_DRAFT_ROOT, project_name)
        self.logger.info(f"[OK] 剪映草稿生成完成: {draft_dir}")
        self.logger.info(f"  视频片段: {len(exported_segments)} 个")
        self.logger.info(f"  总时长: {total_dur_sec:.1f} 秒")
        self.logger.info("  请重启剪映以加载新项目")

        self._export_jcc_info(
            exported_segments,
            project_name,
            total_dur_sec,
            export_dir=kwargs.get("export_dir", self.export_dir),
            has_voiceover_audio=bool(voiceover_audio and os.path.exists(voiceover_audio)),
            has_auto_voiceover=bool(voiceover_plan and getattr(voiceover_plan, "lines", None)),
        )
        return draft_dir

    def _build_video_segment(self, video_path: str, target_range: Timerange, source_range: Timerange) -> VideoSegment | None:
        try:
            return VideoSegment(video_path, target_range, source_timerange=source_range)
        except ValueError:
            from pyJianYingDraft.local_materials import VideoMaterial

            material = VideoMaterial(video_path)
            max_end = material.duration
            if source_range.start >= max_end:
                return None

            actual_dur = min(source_range.end, max_end) - source_range.start
            if actual_dur < 500000:
                return None

            safe_source_range = Timerange(source_range.start, actual_dur)
            safe_target_range = Timerange(target_range.start, actual_dur)
            return VideoSegment(video_path, safe_target_range, source_timerange=safe_source_range)

    def _build_audio_segment(self, audio_path: str, target_range: Timerange, volume: float) -> AudioSegment | None:
        try:
            return AudioSegment(audio_path, target_range, volume=volume)
        except ValueError:
            from pyJianYingDraft.local_materials import AudioMaterial

            material = AudioMaterial(audio_path)
            actual_dur = min(target_range.duration, material.duration)
            if actual_dur < 500000:
                return None
            safe_target_range = Timerange(target_range.start, actual_dur)
            return AudioSegment(audio_path, safe_target_range, volume=volume)

    def _export_jcc_info(
        self,
        video_segments: List[Dict],
        project_name: str,
        total_duration: float,
        *,
        export_dir: str,
        has_voiceover_audio: bool = False,
        has_auto_voiceover: bool = False,
    ):
        jcc_data = {
            "name": project_name,
            "total_duration": round(total_duration, 2),
            "clip_count": len(video_segments),
            "has_voiceover_audio": has_voiceover_audio,
            "has_auto_voiceover": has_auto_voiceover,
            "clips": [],
        }

        cur_pos = 0.0
        for seg in video_segments:
            src_start = float(seg.get("actual_source_start", seg.get("start", 0)))
            src_end = float(seg.get("actual_source_end", seg.get("end", src_start + seg.get("duration", 0))))
            timeline_start = float(seg.get("actual_timeline_start", cur_pos))
            timeline_end = float(seg.get("actual_timeline_end", timeline_start + max(0.0, src_end - src_start)))
            duration = max(0.0, timeline_end - timeline_start)
            jcc_data["clips"].append(
                {
                    "src": seg.get("video_path", ""),
                    "source_start": round(src_start, 3),
                    "source_end": round(src_end, 3),
                    "timeline_start": round(timeline_start, 3),
                    "timeline_end": round(timeline_end, 3),
                    "timeline_order": seg.get("timeline_order"),
                    "timeline_sort_mode": seg.get("timeline_sort_mode", ""),
                    "beat_id": seg.get("beat_id", ""),
                    "beat_title": seg.get("beat_title", ""),
                    "beat_index": seg.get("beat_index"),
                    "priority_score": seg.get("priority_score"),
                    "visual_score": seg.get("visual_score"),
                    "visual_diversity": seg.get("visual_diversity"),
                    "best_frame_path": seg.get("best_frame_path", ""),
                    "best_frame_timestamp": seg.get("best_frame_timestamp"),
                    "original_start": seg.get("original_start"),
                    "original_end": seg.get("original_end"),
                    "trimmed_by": seg.get("trimmed_by", ""),
                    "reason": seg.get("reason", ""),
                }
            )
            cur_pos = timeline_end

        ensure_dir(export_dir)
        jcc_path = os.path.join(export_dir, f"{project_name}.jcc")
        with open(jcc_path, "w", encoding="utf-8") as handle:
            json.dump(jcc_data, handle, ensure_ascii=False, indent=2)

        self.logger.info(f"  JCC信息文件: {jcc_path}")

    def install_to_jianying(self, jcc_path: str, project_name: str) -> str:
        draft_dir = os.path.join(JIANYING_DRAFT_ROOT, project_name)
        if os.path.exists(draft_dir):
            self.logger.info(f"草稿已存在于: {draft_dir}")
            return draft_dir
        self.logger.warning("草稿目录不存在，请先运行 export()")
        return ""

    def export_simple(self, final_video: str, project_name: str) -> str:
        self.logger.info(f"开始导出简化版项目: {project_name}")

        if not final_video or not os.path.exists(final_video):
            self.logger.warning("未找到成片，无法导出简化版草稿")
            return ""

        from pyJianYingDraft.local_materials import VideoMaterial

        draft_folder = DraftFolder(JIANYING_DRAFT_ROOT)
        script = draft_folder.create_draft(
            project_name,
            self.config.CANVAS_WIDTH,
            self.config.CANVAS_HEIGHT,
            30,
            allow_replace=True,
        )

        material = VideoMaterial(final_video)

        script.add_track(TrackType.video, "video")
        vseg = VideoSegment(final_video, Timerange(0, material.duration))
        vseg.add_background_filling("blur", blur=0.0625)
        script.add_segment(vseg, "video")
        script.save()

        draft_dir = os.path.join(JIANYING_DRAFT_ROOT, project_name)
        self.logger.info(f"[OK] 简化版草稿生成完成: {draft_dir}")
        return draft_dir
