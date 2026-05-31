#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Quick-start helper that uses the V2 orchestrator directly."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import JianyingOrchestrator


def quick_start() -> None:
    print("=" * 60)
    print("JianyingAgent V2 - Quick Start")
    print("=" * 60)
    print()

    orchestrator = JianyingOrchestrator()
    orchestrator.load_agents()

    example_dir = r"C:\Users\Administrator\Desktop\临时\plugins\新建文件夹"
    if not os.path.exists(example_dir):
        print("未找到示例素材目录。")
        print("你可以这样开始：")
        print('1. 准备素材目录，例如 E:\\素材\\项目A')
        print('2. 运行: python -m apps roughcut --source "E:\\素材\\项目A" --script "你的剪辑目标" --name "项目A"')
        print('3. 或运行: python -m apps suggest "你的选题想法"')
        return

    print(f"检测到示例素材目录: {example_dir}")
    print()
    script = "爸爸用VR看大佛，从戴上到看完讲感想，目标时长约60秒。"
    print(f"示例脚本: {script}")
    print()

    choice = input("是否开始处理？(y/n): ").strip().lower()
    if choice != "y":
        print("已取消。")
        return

    result = orchestrator.process_roughcut(
        script=script,
        source_dir=example_dir,
        project_name="quick_start_demo",
        export_jcc=True,
    )

    print()
    if result.status == "success":
        print("[SUCCESS] 处理完成")
        print(f"剪映草稿: {result.jcc_project}")
        print(f"选中片段: {len(result.segments)} 个")
    else:
        print("[ERROR] 处理失败")
        print(result.message)


if __name__ == "__main__":
    quick_start()
