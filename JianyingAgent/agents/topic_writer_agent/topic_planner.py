#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Rule-based topic and script assistant built on top of ContentMemory."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from shared_base.canon.character_profiles import (
    CharacterProfile,
    infer_focus_characters,
    relationship_guidance,
)
from shared_base.memory.story_index import ContentMemory, ContentStory


HEAVY_CONTEXT = "一个精神状态特殊的妈妈，一个糊涂爱闯祸的爸爸"
CURRENT_THEME = "这个家正在从被拯救，走向重新学习普通生活"


@dataclass
class ScriptBrief:
    idea: str
    story_lines: List[str]
    character_plan: List[str]
    relationship_plan: List[str]
    duplication_risk: str
    similar_stories: List[Dict[str, object]]
    angles: List[str]
    hooks: List[str]
    synopsis: str
    shooting_list: List[str]
    must_capture_dialogue: List[str]
    voiceover_outline: List[str]
    editing_notes: List[str]

    def to_markdown(self) -> str:
        lines = [
            f"# 选题脚本建议：{self.idea}",
            "",
            f"- 故事线：{'、'.join(self.story_lines)}",
            f"- 重复风险：{self.duplication_risk}",
            "",
            "## 人物使用",
        ]
        for value in self.character_plan:
            lines.append(f"- {value}")
        lines.extend(["", "## 关系张力"])
        for value in self.relationship_plan:
            lines.append(f"- {value}")
        lines.extend([
            "",
            "## 相似历史故事",
        ])
        for item in self.similar_stories:
            story = item["story"]
            lines.append(f"- {story.title or story.category}（相似度 {item['score']}）：{story.hook}")

        sections = [
            ("## 新角度", self.angles),
            ("## 开头钩子", self.hooks),
            ("## 故事梗概", [self.synopsis]),
            ("## 必拍画面", self.shooting_list),
            ("## 必收对白", self.must_capture_dialogue),
            ("## 配音大纲", self.voiceover_outline),
            ("## 粗剪提示", self.editing_notes),
        ]
        for title, values in sections:
            lines.extend(["", title])
            for value in values:
                lines.append(f"- {value}")
        return "\n".join(lines) + "\n"


class TopicScriptAssistant:
    """Generate topic/script guidance using historical story memory."""

    def __init__(self, memory: ContentMemory):
        self.memory = memory

    def create_brief(self, idea: str) -> ScriptBrief:
        similar = self.memory.search(idea, limit=6)
        related_lines = self.memory.related_story_lines(idea)
        characters = infer_focus_characters(idea, related_lines)
        duplication_risk = self._duplication_risk(similar)
        angles = self._angles(idea, related_lines, similar)
        hooks = self._hooks(idea, related_lines)
        synopsis = self._synopsis(idea, related_lines)

        return ScriptBrief(
            idea=idea,
            story_lines=related_lines,
            character_plan=self._character_plan(characters),
            relationship_plan=relationship_guidance([character.key for character in characters]),
            duplication_risk=duplication_risk,
            similar_stories=similar,
            angles=angles,
            hooks=hooks,
            synopsis=synopsis,
            shooting_list=self._shooting_list(idea, related_lines),
            must_capture_dialogue=self._dialogue_prompts(idea, related_lines),
            voiceover_outline=self._voiceover_outline(idea, related_lines),
            editing_notes=self._editing_notes(idea, related_lines),
        )

    def _duplication_risk(self, similar: List[Dict[str, object]]) -> str:
        if not similar:
            return "低：历史库里没有明显相似故事。"
        top_score = float(similar[0]["score"])
        top_story: ContentStory = similar[0]["story"]
        if top_score >= 0.45:
            return f"高：和《{top_story.title or top_story.category}》接近，建议换成新的阶段变化或人物视角。"
        if top_score >= 0.28:
            return f"中：历史里有相似表达，可沿用人物关系，但要换任务目标。最接近《{top_story.title or top_story.category}》。"
        return "低：可以拍，但仍建议接上已有故事线，避免变成普通流水账。"

    def _angles(self, idea: str, story_lines: List[str], similar: List[Dict[str, object]]) -> List[str]:
        base = [
            f"不要只拍“{idea}”，要拍这件普通事让这个家重新获得了哪一种生活能力。",
            "把冲突从“爸妈有多难”转成“我如何让他们更安全、更体面、更有选择权”。",
            "中段保留真实混乱和对话，结尾落到小变化，不用强行升华到大苦难。",
        ]
        if "妈妈恢复线" in story_lines:
            base.append("妈妈线重点写“主体性”：她想要什么、愿不愿意、有没有主动表达。")
        if "爸爸适应线" in story_lines:
            base.append("爸爸线不要只写闯祸，也要捕捉他嘴硬、笨拙、偶尔心软的瞬间。")
        if "女朋友共建线" in story_lines:
            base.append("女朋友线重点写“建设能力”，不是牺牲感：审美、秩序、稳定、把家变舒服。")
        if similar:
            story = similar[0]["story"]
            base.append(f"历史参考《{story.title or story.category}》的情绪，但这次要换一个新落点。")
        return base[:6]

    def _character_plan(self, characters: List[CharacterProfile]) -> List[str]:
        plan = []
        for character in characters:
            ability = character.abilities[0]
            limit = character.limits[0]
            function = character.story_function[0]
            camera = character.camera_value[0]
            rule = character.writing_rule[0]
            plan.append(
                f"{character.name}：{character.core} 本期功能：{function} 镜头抓手：{camera} "
                f"能力：{ability} 边界：{limit} 写法：{rule}"
            )
        return plan

    def _hooks(self, idea: str, story_lines: List[str]) -> List[str]:
        hooks = [
            f"{HEAVY_CONTEXT}，今天我想带他们做一件普通家庭再普通不过的事：{idea}。",
            f"把妈妈接回家、把爸爸接进城后，我发现最难的不是照顾他们活着，而是让这个家重新学会生活。",
            f"以前我们家每天都像在救火，今天我想试试，能不能安稳地完成一件小事：{idea}。",
            f"这件事对别人可能只是日常，但对我们家来说，像一次小小的考试。",
        ]
        if "妈妈恢复线" in story_lines:
            hooks.append(f"妈妈被安排了太多年，今天我想看看她能不能自己参与决定：{idea}。")
        if "爸爸适应线" in story_lines:
            hooks.append(f"我爸糊涂又爱闯祸，但今天我还是想给他一次机会，看他能不能配合完成：{idea}。")
        if "女朋友共建线" in story_lines:
            hooks.append(f"如果不是女朋友，我可能只会把爸妈照顾到活着，但她想把这件事做得更像生活：{idea}。")
        if "照护者成长线" in story_lines:
            hooks.append(f"我性格其实比较安静，不太会把话说出口，所以很多时候只能先把事情做好，再慢慢理解这个家。")
        return hooks[:6]

    def _synopsis(self, idea: str, story_lines: List[str]) -> str:
        return (
            f"这一期围绕“{idea}”展开。开头先交代特殊家庭背景和今天的小任务，"
            "中段拍准备、执行、出状况、家人真实反应，保留爸爸妈妈的现场对白和女朋友的参与。"
            f"最后不要回到卖惨，而是落到“{CURRENT_THEME}”：今天这个家又多了一点普通生活的能力。"
        )

    def _shooting_list(self, idea: str, story_lines: List[str]) -> List[str]:
        shots = [
            "开头环境镜头：家里当天状态、爸妈正在做什么、你准备出发或开始任务。",
            "任务准备：衣服、药、水、工具、路线、食材等细节，体现照护不是临时起意。",
            "爸妈第一反应：愿不愿意、听不听懂、有没有可爱或不配合的瞬间。",
            "女朋友参与：她如何做选择、整理、提醒、安抚或给出审美判断。",
            "过程中最乱的一刻：爸爸添乱、妈妈重复、你差点发火、计划被打断。",
            "过程中最软的一刻：妈妈笑、爸爸心软、女朋友扶一把、四个人坐在一起。",
            "结尾画面：饭桌、回家路上、睡前、照片、整理好的角落，用安稳画面收住。",
        ]
        if "妈妈恢复线" in story_lines:
            shots.append("妈妈的主动表达：她指、拿、选、说想要、拒绝或珍惜某样东西。")
        if "爸爸适应线" in story_lines:
            shots.append("爸爸的规则感：他有没有记住路线、完成任务、少闯一点祸。")
        if "女朋友共建线" in story_lines:
            shots.append("女朋友的具体动作：她的活泼、话多、审美和提醒，要成为画面里的行动。")
        if "照护者成长线" in story_lines:
            shots.append("你的安静行动：准备、忍耐、调整、复盘，不要只靠旁白说自己累。")
        return shots

    def _dialogue_prompts(self, idea: str, story_lines: List[str]) -> List[str]:
        prompts = [
            f"问妈妈/爸爸：今天这个你喜不喜欢？要不要？还想不想继续？",
            "问女朋友：你觉得这样安排行不行？还有哪里要改？",
            "保留爸妈的重复回答、方言、答非所问，这是你的真实感。",
            "收一句你自己的现场反应：不是事后总结，而是当下的累、气、好笑或心软。",
        ]
        if "妈妈恢复线" in story_lines:
            prompts.append("问妈妈：你自己选还是我帮你选？让她的选择权进入视频。")
        if "爸爸适应线" in story_lines:
            prompts.append("问爸爸：你记不记得刚才我怎么说的？不要只拍错，也拍他努力理解。")
        return prompts

    def _voiceover_outline(self, idea: str, story_lines: List[str]) -> List[str]:
        return [
            "第一段：用特殊家庭设定 + 今天任务开头，不要超过两句话。",
            "第二段：交代为什么这件普通事对你家不普通，接上历史故事线。",
            "第三段：按时间顺序讲过程，多写动作和现场，不急着讲道理。",
            "第四段：写一个失控/好笑瞬间，让视频不沉重。",
            "第五段：写一个心软/变化瞬间，让观众看到这家人在变好。",
            "结尾：落到小变化，比如更主动、更安全、更体面、更像一个家。",
        ]

    def _editing_notes(self, idea: str, story_lines: List[str]) -> List[str]:
        return [
            "开头 3 秒优先用人物状态强的画面，不要只用空镜。",
            "剪辑时保留一两句爸妈原声，配音负责解释，原声负责真实。",
            "中段节奏可以乱一点，但每 15-20 秒要回到任务进度。",
            "结尾不要用宏大音乐硬煽，最好用一个生活动作收尾。",
            "粗剪时额外保留 3-5 个备选高光片段，方便剪映精修时换节奏。",
        ]
