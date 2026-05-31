#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Smoke test for the roughcut chain on the tea-picking project."""

from __future__ import annotations

import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from orchestrator import JianyingOrchestrator


def main() -> None:
    print("=" * 60)
    print("JianyingAgent V2 - 测试：采茶项目（目标 3 分钟）")
    print("=" * 60)
    print()

    orchestrator = JianyingOrchestrator()
    orchestrator.load_agents()

    script_text = """
    和女友带爸妈旅居全国第一站·乐山。
    halo大家好我是小熊，今天打算带妈妈去体验一次采茶制茶。
    这是我们仨第一次去茶园，很是激动。
    难得朱总一大早就起来收拾自己了。
    女友化妆，擦防晒。
    妈，我们等哈儿去摘茶叶喔。
    出发去茶园的路上，妈妈全程都很安静，藏不住眼里的好奇。
    到达茶园，教妈妈摘茶叶，只摘最嫩的那一小片。
    妈妈学得很慢，动作笨拙，但没有不耐烦，一直很认真的尝试。
    妈，好闻不？是不是香香的？
    揉茶的时候，妈妈格外认真。
    炒茶品茶等体验。
    这是妈妈第一次体验采茶制茶，这一袋茶叶，是她今天的全部成就。
    她一定会记得，今天在这个陌生的地方找到的，属于她的快乐。
    我们不奢求她能记住每一个瞬间，只愿在这些鲜活的时刻里，她依然能笑得像个孩子一样纯粹。
    目标时长：约180秒（3分钟）。
    """

    source_dir = r"C:\Users\Administrator\Desktop\临时\plugins\采茶\4.9采茶"
    print(f"素材目录: {source_dir}")
    print("目标时长: 3 分钟")
    print()

    try:
        result = orchestrator.process_roughcut(
            script=script_text,
            source_dir=source_dir,
            project_name="采茶_小熊",
            export_jcc=True,
        )

        if result.status == "success":
            print("[SUCCESS]")
            print(f"草稿: {result.jcc_project}")
            print(f"片段: {len(result.segments)} 个")
            total = sum(float(segment["duration"]) for segment in result.segments)
            print(f"总时长: {total:.1f}s ({total/60:.1f}min)")
        else:
            print(f"[ERROR] {result.message}")

    except Exception as exc:
        print(f"[ERROR] {exc}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
