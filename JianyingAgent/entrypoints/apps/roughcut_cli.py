#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""CLI for the V2 roughcut flow."""

from __future__ import annotations

import argparse
import os

from orchestrator import JianyingOrchestrator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="JianyingAgent V2 - 自动粗剪入口")
    parser.add_argument("--source", "-s", type=str, help="素材目录路径")
    parser.add_argument("--script", "-sc", type=str, default="", help="剪辑脚本/描述")
    parser.add_argument("--name", "-n", type=str, default=None, help="项目名称")
    parser.add_argument("--duration", "-d", type=int, default=180, help="目标时长（秒）")
    parser.add_argument("--width", type=int, default=None, help="画布宽度")
    parser.add_argument("--height", type=int, default=None, help="画布高度")
    parser.add_argument("--srt", type=str, default=None, help="字幕 SRT 文件路径")
    parser.add_argument("--bgm", type=str, default=None, help="背景音乐路径")
    parser.add_argument("--voiceover", type=str, default=None, help="配音音频路径")
    parser.add_argument("--no-jcc", action="store_true", help="不导出剪映草稿")
    return parser


def build_script(script: str, duration: int) -> str:
    if script:
        return f"{script}\n目标时长：约{duration}秒（{duration // 60}分钟）。"
    return f"请从素材中筛选精彩片段，目标时长约{duration}秒（{duration // 60}分钟）。"


def prompt_missing_args(args: argparse.Namespace) -> None:
    if not args.source:
        args.source = input("素材目录路径: ").strip().strip('"')
    if not args.script:
        args.script = input("剪辑脚本（可选）: ").strip()
    if not args.name:
        args.name = input("项目名称: ").strip()


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    prompt_missing_args(args)

    if not args.source or not os.path.isdir(args.source):
        print(f"[ERROR] 素材目录不存在: {args.source}")
        return

    if not args.name:
        args.name = os.path.basename(args.source.rstrip("\\/"))

    orchestrator = JianyingOrchestrator()
    orchestrator.load_agents()

    result = orchestrator.process_roughcut(
        script=build_script(args.script, args.duration),
        source_dir=args.source,
        project_name=args.name,
        export_jcc=not args.no_jcc,
        subtitle_srt=args.srt,
        bgm_audio=args.bgm,
        voiceover_audio=args.voiceover,
        video_width=args.width,
        video_height=args.height,
    )

    if result.status == "success":
        total = sum(float(segment["duration"]) for segment in result.segments)
        print("=" * 60)
        print("处理完成")
        print("=" * 60)
        print(f"草稿: {result.jcc_project}")
        print(f"片段: {len(result.segments)} 个")
        print(f"总时长: {total:.1f}s ({total/60:.1f}min)")
    else:
        print(f"[ERROR] {result.message}")


if __name__ == "__main__":
    main()
