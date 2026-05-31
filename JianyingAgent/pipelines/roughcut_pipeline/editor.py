#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
技能4: 批量自动剪辑封装
- 依据时间码生成 FFmpeg 执行指令，完成裁切、拼接、统一分辨率画幅
- 一键叠加背景音乐、基础字幕，可调音量层级
- 批量成片，无需拖拽时间轴反复剪辑
"""

import os
from typing import List, Dict

from utils import ensure_dir, run_ffmpeg, format_time, ProgressTracker


class Skill4Editor:
    """批量自动剪辑封装技能"""

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.temp_dir = ensure_dir(os.path.join(config.TEMP_DIR, "segments"))
        self.output_dir = ensure_dir(os.path.join(config.OUTPUT_DIR, "videos"))

    def edit(self, segments: List[Dict], project_name: str, *, temp_dir: str | None = None, output_dir: str | None = None) -> str:
        """
        批量剪辑并拼接

        Args:
            segments: 选中的片段列表
            project_name: 项目名称

        Returns:
            str: 最终视频路径
        """
        self.logger.info(f"开始剪辑 {len(segments)} 个片段")

        if not segments:
            self.logger.warning("没有可剪辑的片段")
            return ""

        # 第一步：提取所有片段
        temp_dir = ensure_dir(temp_dir or self.temp_dir)
        output_dir = ensure_dir(output_dir or self.output_dir)
        segment_files = self._extract_segments(segments, temp_dir=temp_dir)

        # 第二步：拼接片段
        final_video = self._concat_segments(segment_files, project_name, temp_dir=temp_dir, output_dir=output_dir)

        # 第三步：添加字幕
        video_with_subtitle = self._add_subtitle(final_video, project_name, output_dir=output_dir)

        self.logger.info(f"剪辑完成: {video_with_subtitle}")

        return video_with_subtitle

    def _extract_segments(self, segments: List[Dict], *, temp_dir: str) -> List[str]:
        """提取所有片段"""
        segment_files = []
        progress = ProgressTracker(len(segments), "提取片段")

        for i, segment in enumerate(segments):
            try:
                output_path = os.path.join(temp_dir, f"segment_{i:03d}_{segment['file_id']}.mp4")

                # 提取片段
                success = self._extract_segment(
                    segment['video_path'],
                    segment['start'],
                    segment['end'],
                    output_path
                )

                if success:
                    segment_files.append(output_path)
                else:
                    self.logger.warning(f"片段提取失败: {segment['file_id']}")

                progress.update()

            except Exception as e:
                self.logger.error(f"提取片段异常 {segment['file_id']}: {str(e)}")

        progress.complete()
        self.logger.info(f"成功提取 {len(segment_files)} 个片段")

        return segment_files

    def _extract_segment(self, input_path: str, start: float, end: float, output_path: str) -> bool:
        """提取单个片段"""
        args = [
            "-ss", str(start),  # 开始时间
            "-t", str(end - start),  # 持续时间
            "-c:v", "libx264",  # 视频编码
            "-c:a", "aac",  # 音频编码
            "-y"  # 覆盖输出文件
        ]

        return run_ffmpeg(args, input_path, output_path)

    def _concat_segments(self, segment_files: List[str], project_name: str, *, temp_dir: str, output_dir: str) -> str:
        """拼接片段"""
        if not segment_files:
            return ""

        # 创建拼接列表文件
        concat_file = os.path.join(temp_dir, f"concat_{project_name}.txt")

        with open(concat_file, 'w', encoding='utf-8') as f:
            for segment_file in segment_files:
                # 转换路径格式（Windows需要）
                abs_path = os.path.abspath(segment_file).replace('\\', '/')
                f.write(f"file '{abs_path}'\n")

        # 拼接视频
        output_path = os.path.join(output_dir, f"{project_name}_merged.mp4")

        args = [
            "-f", "concat",  # concat格式
            "-safe", "0",  # 允许不安全的路径
            "-i", concat_file,  # 输入列表文件
            "-c", "copy",  # 复制编码
            "-y"  # 覆盖输出文件
        ]

        success = run_ffmpeg(args, output_path=output_path)

        if success:
            self.logger.info(f"片段拼接完成: {output_path}")
            return output_path
        else:
            self.logger.error("片段拼接失败")
            return ""

    def _add_subtitle(self, input_video: str, project_name: str, *, output_dir: str) -> str:
        """添加硬字幕"""
        # 查找对应的字幕文件
        subtitle_file = input_video.replace('_merged.mp4', '.srt')

        if not os.path.exists(subtitle_file):
            # 如果没有字幕文件，使用第一个片段的字幕
            transcript_dir = os.path.join(self.config.OUTPUT_DIR, "transcripts")
            if os.path.exists(transcript_dir):
                srt_files = [f for f in os.listdir(transcript_dir) if f.endswith('.srt')]
                if srt_files:
                    subtitle_file = os.path.join(transcript_dir, srt_files[0])

        if not os.path.exists(subtitle_file):
            self.logger.warning("未找到字幕文件，跳过字幕添加")
            return input_video

        # 添加字幕
        output_path = os.path.join(output_dir, f"{project_name}_final.mp4")

        # 准备字幕路径（转义路径）
        subtitle_path_escaped = subtitle_file.replace('\\', '/').replace(':', '\\:')

        # 使用VF滤镜添加字幕（硬字幕）
        args = [
            "-i", input_video,  # 输入视频
            "-vf", f"subtitles='{subtitle_path_escaped}':force_style='FontSize=20,PrimaryColour=&Hffffff&'",  # 字幕样式
            "-c:a", "copy",  # 音频复制
            "-y"  # 覆盖输出文件
        ]

        success = run_ffmpeg(args, output_path=output_path)

        if success:
            self.logger.info(f"字幕添加完成: {output_path}")
            return output_path
        else:
            self.logger.warning("字幕添加失败，返回原视频")
            return input_video

    def add_background_music(self, video_path: str, music_path: str, output_path: str = None, music_volume: float = 0.3) -> str:
        """
        添加背景音乐

        Args:
            video_path: 视频路径
            music_path: 音乐路径
            output_path: 输出路径
            music_volume: 音乐音量（0-1）

        Returns:
            str: 输出路径
        """
        if output_path is None:
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            output_path = os.path.join(self.output_dir, f"{base_name}_with_music.mp4")

        # 混合音频：视频原音 + 背景音乐
        args = [
            "-i", video_path,  # 输入视频
            "-i", music_path,  # 输入音乐
            "-filter_complex", f"[0:a]volume=1.0[vo];[1:a]volume={music_volume}[vm];[vo][vm]amix=inputs=2:duration=first[a]",  # 音频混合
            "-map", "0:v",  # 使用视频的第一个流（视频）
            "-map", "[a]",  # 使用混合后的音频
            "-c:v", "copy",  # 视频复制
            "-y"  # 覆盖输出文件
        ]

        success = run_ffmpeg(args, output_path=output_path)

        if success:
            self.logger.info(f"背景音乐添加完成: {output_path}")
            return output_path
        else:
            self.logger.error("背景音乐添加失败")
            return video_path
