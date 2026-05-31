#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Smoke test for the dad-VR project using the V2 orchestrator."""

from __future__ import annotations

import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from orchestrator import JianyingOrchestrator


def main() -> None:
    print("=" * 60)
    print("JianyingAgent V2 - 测试：爸爸看大佛")
    print("=" * 60)
    print()

    orchestrator = JianyingOrchestrator()
    orchestrator.load_agents()

    script = "爸爸用VR看大佛，包括：戴上VR眼镜、看VR中的反应、看完后讲感想，目标时长约60秒。"
    source_dir = r"C:\Users\Administrator\Desktop\临时\plugins\新建文件夹"

    print(f"脚本: {script}")
    print(f"素材目录: {source_dir}")
    print()

    if os.path.isdir(source_dir):
        files = [name for name in os.listdir(source_dir) if name.lower().endswith(".mov")]
        print("找到素材:")
        for index, name in enumerate(files, 1):
            print(f"  {index}. {name}")
        print()

    try:
        result = orchestrator.process_roughcut(
            script=script,
            source_dir=source_dir,
            project_name="爸爸看大佛",
            export_jcc=True,
        )

        if result.status == "success":
            print("[SUCCESS] 处理成功")
            print(f"剪映草稿: {result.jcc_project}")
            print(f"选中片段: {len(result.segments)} 个")
            for index, segment in enumerate(result.segments, 1):
                print(
                    f"  {index}. {segment['file_id']} - "
                    f"{segment['start']:.2f}s ~ {segment['end']:.2f}s"
                )
                if segment.get("reason"):
                    print(f"     理由: {segment['reason']}")
        else:
            print("[ERROR] 处理失败")
            print(result.message)

    except Exception as exc:
        print("[ERROR] 处理异常")
        print(exc)
        traceback.print_exc()


if __name__ == "__main__":
    main()
