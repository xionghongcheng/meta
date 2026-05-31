#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
剪映Agent配置文件
"""

import os
import json

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    tomllib = None


def _load_dotenv():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(base_dir, ".env")
    if not os.path.exists(env_path):
        return

    with open(env_path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


_load_dotenv()


def _resolve_path(value: str, *, base_dir: str) -> str:
    expanded = os.path.expandvars(os.path.expanduser(value))
    if os.path.isabs(expanded):
        return expanded
    return os.path.join(base_dir, expanded)


def _load_codex_config():
    codex_home = os.path.join(os.path.expanduser("~"), ".codex")
    config_path = os.path.join(codex_home, "config.toml")
    auth_path = os.path.join(codex_home, "auth.json")
    config = {}
    auth = {}

    if tomllib and os.path.exists(config_path):
        with open(config_path, "rb") as handle:
            config = tomllib.load(handle)

    if os.path.exists(auth_path):
        with open(auth_path, "r", encoding="utf-8") as handle:
            auth = json.load(handle)

    provider_name = config.get("model_provider", "OpenAI")
    provider = config.get("model_providers", {}).get(provider_name, {})
    base_url = str(provider.get("base_url", "https://api.openai.com")).rstrip("/")
    if base_url.endswith("/responses"):
        responses_url = base_url
    elif base_url.endswith("/v1"):
        responses_url = f"{base_url}/responses"
    else:
        responses_url = f"{base_url}/v1/responses"

    return {
        "api_key": auth.get("OPENAI_API_KEY", ""),
        "responses_url": responses_url,
        "model": config.get("model") or provider.get("model") or "gpt-5.2-codex",
        "reasoning_effort": provider.get("model_reasoning_effort") or "medium",
    }


_CODEX_CONFIG = _load_codex_config()

class Config:
    """全局配置"""

    # 路径配置
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    INPUT_DIR = _resolve_path(os.getenv("JIANYING_INPUT_DIR", "input"), base_dir=BASE_DIR)
    OUTPUT_DIR = _resolve_path(os.getenv("JIANYING_OUTPUT_DIR", "output"), base_dir=BASE_DIR)
    TEMP_DIR = _resolve_path(os.getenv("JIANYING_TEMP_DIR", "temp"), base_dir=BASE_DIR)

    # FFmpeg配置
    FFMPEG_PATH = _resolve_path(os.getenv("FFMPEG_PATH", "D:/soft/ffmpeg/bin/ffmpeg.exe"), base_dir=BASE_DIR)
    FFPROBE_PATH = _resolve_path(os.getenv("FFPROBE_PATH", "D:/soft/ffmpeg/bin/ffprobe.exe"), base_dir=BASE_DIR)

    # Whisper配置
    WHISPER_MODEL = "base"  # 可选: tiny, base, small, medium, large-v3
    WHISPER_LANGUAGE = "zh"
    WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")  # cpu / cuda / auto
    WHISPER_BATCH_SIZE = 24     # 调优默认值（被 auto_tune 覆盖）
    WHISPER_CHUNK_LENGTH = 20
    WHISPER_NUM_WORKERS = 4

    # Codex LLM provider. Codex models use OpenAI's Responses API.
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", _CODEX_CONFIG["api_key"])
    OPENAI_RESPONSES_URL = os.getenv("OPENAI_RESPONSES_URL", _CODEX_CONFIG["responses_url"])
    CODEX_MODEL = os.getenv("CODEX_MODEL", _CODEX_CONFIG["model"])
    CODEX_REASONING_EFFORT = os.getenv("CODEX_REASONING_EFFORT", _CODEX_CONFIG["reasoning_effort"])
    CODEX_TIMEOUT_SECONDS = int(os.getenv("CODEX_TIMEOUT_SECONDS", "300"))

    # 画幅配置（9:16 竖屏）
    CANVAS_WIDTH = 1080
    CANVAS_HEIGHT = 1920

    # 输出配置
    OUTPUT_VIDEO_CODEC = "libx264"
    OUTPUT_AUDIO_CODEC = "aac"
    OUTPUT_FORMAT = "mp4"

    # Proxy / keyframe 配置
    PROXY_WIDTH = 640
    PROXY_FPS = 8
    PROXY_CRF = 30
    PROXY_AUDIO_BITRATE = "48k"

    # 剪映草稿配置
    JIAN_YING_PROJECT_DIR = os.getenv(
        "JIAN_YING_PROJECT_DIR",
        os.path.expanduser("~/Documents/JianyingPro/User Data/Projects"),
    )
    JIAN_YING_PROJECT_DIR = _resolve_path(JIAN_YING_PROJECT_DIR, base_dir=BASE_DIR)

    @classmethod
    def init_dirs(cls):
        """初始化必要的目录"""
        for dir_path in [cls.INPUT_DIR, cls.OUTPUT_DIR, cls.TEMP_DIR]:
            os.makedirs(dir_path, exist_ok=True)

# 初始化配置
Config.init_dirs()
