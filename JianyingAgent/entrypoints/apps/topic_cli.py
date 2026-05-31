#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""CLI for the topic-planning and script-writing flow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agents.topic_writer_agent.agent import TopicWriterAgent
from shared_base.memory.story_index import ContentMemory
from shared_base.paths import default_memory_path


DEFAULT_MEMORY = default_memory_path()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="内容选题和脚本助手")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="导入历史配音汇总，生成故事记忆库")
    ingest.add_argument("files", nargs="+", help="配音汇总 txt 文件路径")
    ingest.add_argument("--out", default=str(DEFAULT_MEMORY), help="输出 stories.json 路径")

    profile = sub.add_parser("profile", help="查看故事库画像")
    profile.add_argument("--memory", default=str(DEFAULT_MEMORY), help="stories.json 路径")

    suggest = sub.add_parser("suggest", help="根据一个想法生成选题脚本建议")
    suggest.add_argument("idea", help="你的选题想法，比如：带妈妈逛街买衣服")
    suggest.add_argument("--memory", default=str(DEFAULT_MEMORY), help="stories.json 路径")
    suggest.add_argument("--out", default=None, help="可选：保存为 Markdown 文件")

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "ingest":
        memory = ContentMemory.from_files(args.files)
        out = memory.save(args.out)
        print(f"已导入 {len(memory.stories)} 条历史故事")
        print(f"故事库: {out}")
        return

    if args.command == "profile":
        memory = ContentMemory.load(args.memory)
        print(json.dumps(memory.profile(), ensure_ascii=False, indent=2))
        return

    if args.command == "suggest":
        agent = TopicWriterAgent(memory_path=args.memory)
        package = agent.create_script_package(args.idea)
        markdown = package.markdown
        if args.out:
            out = Path(args.out)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(markdown, encoding="utf-8")
            print(f"已生成: {out}")
        else:
            print(markdown)


if __name__ == "__main__":
    main()
