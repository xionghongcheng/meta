#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
技能1: 批量素材拆分萃取
- 批量导入多段长视频
- 自动拆分片段、单独提取音频
- 输出标准化音视频文件
"""

import os
import shutil
from typing import List, Dict
from pathlib import Path

from utils import get_video_files, get_video_duration, ensure_dir, run_ffmpeg, ProgressTracker


class Skill1Extractor:
    """批量素材拆分萃取技能"""

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.temp_dir = ensure_dir(os.path.join(config.TEMP_DIR, "extracted"))

    def extract(self, source_dir: str, *, audio_cache_dir: str | None = None, proxy_dir: str | None = None) -> List[Dict]:
        """
        批量提取素材

        Args:
            source_dir: 素材目录路径

        Returns:
            List[Dict]: 提取的素材信息列表
        """
        self.logger.info(f"开始扫描素材目录: {source_dir}")

        # 扫描视频文件
        video_files = get_video_files(source_dir, ignore_dirs=["agent_workspace", "__pycache__"])
        self.logger.info(f"找到 {len(video_files)} 个视频文件")

        if not video_files:
            self.logger.warning("未找到任何视频文件")
            return []

        # 批量处理
        results = []
        total = len(video_files)

        for i, video_file in enumerate(video_files):
            try:
                result = self._process_video(
                    video_file,
                    audio_cache_dir=audio_cache_dir,
                    proxy_dir=proxy_dir,
                )
                if result:
                    results.append(result)
                print(f"  音频 [{i+1}/{total}] {result['filename']}: {result['duration']:.1f}s", flush=True)
            except Exception as e:
                self.logger.error(f"处理文件失败 {video_file}: {str(e)}")

        print(f"  === 音频提取完成: {len(results)}/{total} ===", flush=True)
        self.logger.info(f"成功提取 {len(results)} 个素材")

        return results

    def _process_video(self, video_path: str, *, audio_cache_dir: str | None = None, proxy_dir: str | None = None) -> Dict:
        """
        处理单个视频文件

        Args:
            video_path: 视频文件路径

        Returns:
            Dict: 处理结果
        """
        filename = os.path.basename(video_path)
        name_without_ext = os.path.splitext(filename)[0]

        # 瞬间提取音频（直接复制音频流，不重编码）
        output_dir = ensure_dir(audio_cache_dir or self.temp_dir)
        output_audio = os.path.join(output_dir, f"{name_without_ext}.m4a")

        analysis_path = video_path
        proxy_path = ""
        if proxy_dir:
            ensure_dir(proxy_dir)
            proxy_path = os.path.join(proxy_dir, f"{name_without_ext}_proxy.mp4")
            self._create_proxy(video_path, proxy_path)
            analysis_path = proxy_path

        self._extract_audio_instant(analysis_path, output_audio)

        # 获取视频信息
        duration = get_video_duration(video_path)

        file_size = os.path.getsize(video_path)
        self.logger.info(f"  - {filename}: {duration:.2f}秒 ({file_size/1024/1024:.1f}MB)")

        return {
            "id": name_without_ext,
            "original_path": video_path,
            "video_path": video_path,  # 最终剪辑仍使用原始路径
            "analysis_path": analysis_path,
            "proxy_path": proxy_path,
            "audio_path": output_audio,
            "duration": duration,
            "file_size": file_size,
            "filename": filename
        }

    def _create_proxy(self, input_path: str, output_path: str) -> bool:
        if (
            os.path.exists(output_path)
            and os.path.getsize(output_path) > 0
            and os.path.getmtime(output_path) >= os.path.getmtime(input_path)
        ):
            return True

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
        return run_ffmpeg(args, input_path, output_path)

    def _extract_audio_instant(self, input_path: str, output_path: str) -> bool:
        """
        瞬间提取音频（直接复制音频流，不重新编码）
        faster-whisper 内部用 ffmpeg 自动处理格式转换。

        Args:
            input_path: 输入视频路径
            output_path: 输出音频路径

        Returns:
            bool: 是否成功
        """
        args = [
            "-vn",           # 不处理视频
            "-acodec", "copy",  # 直接复制音频流
            "-y"             # 覆盖输出文件
        ]

        return run_ffmpeg(args, input_path, output_path)

    def _extract_audio(self, input_path: str, output_path: str) -> bool:
        """
        提取音频（WAV重编码模式，兼容性好但慢）

        Args:
            input_path: 输入视频路径
            output_path: 输出音频路径

        Returns:
            bool: 是否成功
        """
        args = [
            "-vn",  # 不处理视频
            "-acodec", "pcm_s16le",  # 音频编码
            "-ar", "16000",  # 采样率16kHz（Whisper推荐）
            "-ac", "1",  # 单声道
            "-y"  # 覆盖输出文件
        ]

        return run_ffmpeg(args, input_path, output_path)

    def extract_segment(self, video_path: str, start_time: float, end_time: float, output_path: str) -> bool:
        """
        提取视频片段

        Args:
            video_path: 输入视频路径
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）
            output_path: 输出路径

        Returns:
            bool: 是否成功
        """
        args = [
            "-ss", str(start_time),  # 开始时间
            "-t", str(end_time - start_time),  # 持续时间
            "-c", "copy",  # 复制编码，不重新编码
            "-y"  # 覆盖输出文件
        ]

        return run_ffmpeg(args, video_path, output_path)
