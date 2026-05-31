#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Unified V2 CLI."""

from __future__ import annotations

from entrypoints.apps.roughcut_cli import main as roughcut_main
from entrypoints.apps.topic_cli import main as topic_main
from entrypoints.webui.server import main as web_main


TOPIC_COMMANDS = {"topic", "ingest", "profile", "suggest"}
ROUGHCUT_COMMANDS = {"roughcut"}
WEB_COMMANDS = {"web", "ui"}


def print_help() -> None:
    print("用法:")
    print("  python -m apps [suggest|profile|ingest|roughcut|web] ...")
    print()
    print("常用命令:")
    print('  python -m apps suggest "带妈妈逛街买衣服，让她自己选一身喜欢的"')
    print("  python -m apps profile --memory shared_base\\memory\\stories.json")
    print('  python -m apps roughcut --source "E:\\素材\\采茶" --script "带妈妈体验采茶制茶，目标时长约180秒。" --name "采茶_小熊"')
    print("  python -m apps web --open")


def main(argv: list[str] | None = None) -> None:
    import sys

    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print_help()
        return

    command = argv.pop(0)

    if command in TOPIC_COMMANDS:
        if command != "topic":
            argv.insert(0, command)
        topic_main(argv)
        return

    if command in ROUGHCUT_COMMANDS:
        roughcut_main(argv)
        return

    if command in WEB_COMMANDS:
        web_main(argv)
        return

    if command.startswith("-"):
        argv.insert(0, command)
        roughcut_main(argv)
        return

    print(f"未知命令: {command}")
    print()
    print_help()
