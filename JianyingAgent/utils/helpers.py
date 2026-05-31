#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
工具函数模块
"""

import os
import subprocess
import re
from typing import List, Dict, Any


def run_ffmpeg(args: List[str], input_path: str = None, output_path: str = None) -> bool:
    """
    运行FFmpeg命令

    Args:
        args: FFmpeg参数列表
        input_path: 输入文件路径
        output_path: 输出文件路径

    Returns:
        bool: 是否成功
    """
    from config import Config

    # FFmpeg正确顺序：ffmpeg -i input [options] output
    cmd = [Config.FFMPEG_PATH]

    if input_path:
        cmd.extend(["-i", input_path])

    cmd.extend(args)

    if output_path:
        cmd.extend([output_path])

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=3600  # 1小时超时
        )
        return result.returncode == 0
    except Exception as e:
        print(f"FFmpeg执行失败: {str(e)}")
        return False


def run_ffprobe(input_path: str, show_format: bool = True, show_streams: bool = True) -> Dict[str, Any]:
    """
    运行FFprobe获取视频信息

    Args:
        input_path: 输入文件路径
        show_format: 是否显示格式信息
        show_streams: 是否显示流信息

    Returns:
        Dict: 视频信息字典
    """
    from config import Config

    cmd = [Config.FFPROBE_PATH, "-v", "quiet"]

    if show_format:
        cmd.extend(["-show_format"])

    if show_streams:
        cmd.extend(["-show_streams"])

    cmd.extend(["-of", "json", input_path])

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60
        )

        if result.returncode == 0:
            import json
            return json.loads(result.stdout.decode('utf-8'))
        else:
            return {}

    except Exception as e:
        print(f"FFprobe执行失败: {str(e)}")
        return {}


def get_video_duration(input_path: str) -> float:
    """
    获取视频时长（秒）

    Args:
        input_path: 视频文件路径

    Returns:
        float: 时长（秒）
    """
    info = run_ffprobe(input_path, show_streams=False)

    if info and 'format' in info:
        return float(info['format'].get('duration', 0))

    return 0.0


def format_time(seconds: float) -> str:
    """
    将秒数转换为 HH:MM:SS.mmm 格式

    Args:
        seconds: 秒数

    Returns:
        str: 格式化的时间字符串
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60

    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def parse_time(time_str: str) -> float:
    """
    解析时间字符串为秒数

    支持格式:
    - HH:MM:SS
    - MM:SS
    - SS
    - HH:MM:SS.mmm

    Args:
        time_str: 时间字符串

    Returns:
        float: 秒数
    """
    # 尝试匹配 HH:MM:SS.mmm 或 HH:MM:SS
    match = re.match(r'(\d+):(\d+):(\d+(?:\.\d+)?)', time_str.strip())
    if match:
        h, m, s = match.groups()
        return int(h) * 3600 + int(m) * 60 + float(s)

    # 尝试匹配 MM:SS.mmm 或 MM:SS
    match = re.match(r'(\d+):(\d+(?:\.\d+)?)', time_str.strip())
    if match:
        m, s = match.groups()
        return int(m) * 60 + float(s)

    # 尝试直接解析为数字
    try:
        return float(time_str)
    except ValueError:
        return 0.0


def ensure_dir(path: str) -> str:
    """
    确保目录存在，不存在则创建

    Args:
        path: 目录路径

    Returns:
        str: 目录路径
    """
    os.makedirs(path, exist_ok=True)
    return path


def get_video_files(directory: str, extensions: List[str] = None, ignore_dirs: List[str] = None) -> List[str]:
    """
    获取目录中的所有视频文件

    Args:
        directory: 目录路径
        extensions: 视频扩展名列表

    Returns:
        List[str]: 视频文件路径列表
    """
    if extensions is None:
        extensions = ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.mts', '.m2ts']
    if ignore_dirs is None:
        ignore_dirs = ['agent_workspace', '__pycache__']

    video_files = []

    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            if any(file.lower().endswith(ext) for ext in extensions):
                video_files.append(os.path.join(root, file))

    return sorted(video_files)


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除非法字符

    Args:
        filename: 原始文件名

    Returns:
        str: 清理后的文件名
    """
    # 移除或替换非法字符
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')

    return filename.strip()


class ProgressTracker:
    """进度跟踪器"""

    def __init__(self, total: int, description: str = "处理中"):
        self.total = total
        self.current = 0
        self.description = description

    def update(self, step: int = 1):
        """更新进度"""
        self.current += step
        progress = (self.current / self.total) * 100
        print(f"\r{self.description}: {self.current}/{self.total} ({progress:.1f}%)", end='', flush=True)

    def complete(self):
        """完成"""
        print(f"\r{self.description}: 完成！ ({self.current}/{self.total})")
