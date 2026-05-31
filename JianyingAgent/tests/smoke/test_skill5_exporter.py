#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Smoke test for pyJianYingDraft exporter behavior."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pyJianYingDraft import DraftFolder, SEC, Timerange, TrackType, VideoSegment


def test_create_draft() -> None:
    print("=" * 60)
    print("测试 pyJianYingDraft 创建剪映草稿")
    print("=" * 60)

    src_dir = r"C:\Users\Administrator\Desktop\临时\plugins\新建文件夹"
    files = sorted([name for name in os.listdir(src_dir) if name.endswith(".MOV")])

    print(f"找到 {len(files)} 个视频文件:")
    for name in files:
        fpath = os.path.join(src_dir, name)
        size_mb = os.path.getsize(fpath) / 1024 / 1024
        print(f"  {name} ({size_mb:.1f} MB)")

    print()
    print("正在创建剪映草稿...")
    draft_folder = DraftFolder("E:/JianyingPro Drafts")

    project_name = "爸爸看大佛_pyJianYingDraft测试"
    script = draft_folder.create_draft(
        project_name,
        1920,
        1080,
        30,
        allow_replace=True,
    )

    script.add_track(TrackType.video, "video")

    cur_pos_sec = 0.0
    for name in files:
        fpath = os.path.join(src_dir, name)
        print(f"  添加片段: {name}")

        clip_dur = 10.0
        target_us = int(cur_pos_sec * SEC)
        dur_us = int(clip_dur * SEC)

        vseg = VideoSegment(
            fpath,
            Timerange(target_us, dur_us),
            source_timerange=Timerange(0, dur_us),
        )
        script.add_segment(vseg, "video")
        cur_pos_sec += clip_dur

    script.save()

    draft_dir = os.path.join("E:/JianyingPro Drafts", project_name)
    print()
    print("[OK] 草稿生成完成!")
    print(f"  草稿目录: {draft_dir}")

    draft_content = os.path.join(draft_dir, "draft_content.json")
    if os.path.exists(draft_content):
        size = os.path.getsize(draft_content)
        print(f"  draft_content.json: {size / 1024:.1f} KB")

    draft_meta = os.path.join(draft_dir, "draft_meta_info.json")
    if os.path.exists(draft_meta):
        print("  draft_meta_info.json: 存在")

    print()
    print("请重启剪映，在草稿列表中确认新项目是否出现。")


if __name__ == "__main__":
    test_create_draft()
