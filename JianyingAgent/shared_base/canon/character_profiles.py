#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Character profiles for the creator's long-form family story world."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class CharacterProfile:
    key: str
    name: str
    core: str
    abilities: List[str]
    limits: List[str]
    story_function: List[str]
    camera_value: List[str]
    writing_rule: List[str]
    avoid: List[str]


CHARACTER_PROFILES: Dict[str, CharacterProfile] = {
    "mom": CharacterProfile(
        key="mom",
        name="妈妈",
        core="精神状态特殊、认知和生活能力受损，但有很强的孩子气、可爱感和重新恢复主体性的空间。",
        abilities=[
            "能通过吃饭、穿衣、挑东西、笑、重复回答表达喜好。",
            "在稳定环境里会慢慢恢复主动性，比如想出门、想吃什么、珍惜新衣服新鞋。",
            "适合承载“被生活夺走的普通权利重新回来”的主题。",
        ],
        limits=[
            "理解复杂规则困难，表达可能重复、跳跃或答非所问。",
            "身体状态、牙齿、骨折、体重、睡眠等会影响拍摄安排。",
            "不能被当成单纯的笑点或病情标签。",
        ],
        story_function=[
            "恢复线主角：她每一次主动选择都是剧情进展。",
            "情绪柔软点：她的孩子气和可爱可以托住沉重主题。",
            "照护成果可视化：吃得好、睡得好、愿意出门、会表达。",
        ],
        camera_value=[
            "挑选、点头、摇头、护着新东西、吃饭、笑、摸衣服、看镜头。",
            "她主动说想要/不要的瞬间，比摆拍更重要。",
            "适合用特写捕捉手、眼神、嘴角、慢半拍的反应。",
        ],
        writing_rule=[
            "写她时重点是“她重新拥有选择”，不是“她有多可怜”。",
            "开头可以交代病情，但中段必须回到她今天具体做了什么。",
            "结尾常落到：她的人生不该只剩病历，也该有普通生活。",
        ],
        avoid=[
            "不要把精神疾病当唯一钩子反复消费。",
            "不要把她的认知受限写成嘲笑。",
            "不要安排超出她体力和理解能力的复杂任务。",
        ],
    ),
    "dad": CharacterProfile(
        key="dad",
        name="爸爸",
        core="糊涂、爱闯祸、规则感弱，经常分不清状况，但也有嘴硬、笨拙、偶尔心软的一面。",
        abilities=[
            "能制造强冲突和轻喜剧，是视频中最自然的变量。",
            "在简单任务、强提醒、具体奖励下可能短暂配合。",
            "偶尔会用很笨拙的方式表达关心或善意。",
        ],
        limits=[
            "容易乱跑、骑车、捡东西、忘规则、把简单事弄复杂。",
            "不适合交付高风险任务，只适合低风险、可观察的小任务。",
            "和他沟通常常会触发你的火气，这是照护者成长线的来源。",
        ],
        story_function=[
            "冲突源：让普通任务变成考验。",
            "喜剧源：他的答非所问和嘴硬可以缓解沉重。",
            "修复难题：你如何对待这个曾让你受伤、现在又需要照顾的人。",
        ],
        camera_value=[
            "听规则、忘规则、嘴硬、偷偷开心、突然帮忙、把事情搞砸。",
            "适合拍他和规则表、门禁、电梯、血压计、饭桌的互动。",
            "不要只拍闯祸，也要拍他少闯一点祸的微小进步。",
        ],
        writing_rule=[
            "写爸爸要有矛盾感：气人是真的，可怜和可爱也是真的。",
            "每条爸爸线最好有一个“我差点发火/我换个方式沟通”的自我动作。",
            "结尾可以落到：我不是想控制他，是想让他安全地拥有自由。",
        ],
        avoid=[
            "不要把他写成纯反派。",
            "不要给他安排无法完成的任务然后只证明他失败。",
            "不要只靠骂和失控推进剧情。",
        ],
    ),
    "girlfriend": CharacterProfile(
        key="girlfriend",
        name="女朋友",
        core="活泼、话多、有审美和生活组织能力，是这个家从能活着到像个家的关键共建者。",
        abilities=[
            "能提供审美、秩序、搭配、收纳、做饭和情绪缓冲。",
            "话多活泼，适合带动妈妈互动，也能让视频更轻。",
            "她的存在让故事从原生家庭修复，延伸到新家庭建设。",
        ],
        limits=[
            "不能只写成牺牲者或救世主，否则会变单薄。",
            "她也会累，也需要被照顾和被看见。",
            "商单和生活品质线容易落在她身上，但要避免工具人化。",
        ],
        story_function=[
            "秩序来源：她让家变干净、好看、可执行。",
            "未来线：她让你相信自己可以拥有小家。",
            "情绪调色：她的活泼和话多可以让沉重家庭线变得有烟火气。",
        ],
        camera_value=[
            "她和妈妈挑衣服、做饭、整理、打扮、聊天、吐槽。",
            "她对你的提醒：慢点、别急、这样更好看。",
            "她让家变好看的前后对比。",
        ],
        writing_rule=[
            "写她时重点是“共建能力”，不是单纯感谢她牺牲。",
            "要保留她的活泼话多，让她不是旁白里的符号。",
            "结尾可以落到：她不是来拯救我，是和我一起建设生活。",
        ],
        avoid=[
            "不要把她神化成小天使模板而失去真实性。",
            "不要所有压力都合理化地放到她身上。",
            "不要只在结尾感谢，中段要给她具体动作。",
        ],
    ),
    "me": CharacterProfile(
        key="me",
        name="我",
        core="安静、内敛、承担型，长期在照护责任、原生家庭创伤、自我修复和新家庭建设之间学习当小家长。",
        abilities=[
            "擅长观察和复盘，能把普通日常写成有重量的家庭叙事。",
            "能承担复杂照护和流程安排，是家庭系统的执行者。",
            "安静性格让旁白更克制，适合后置反思而不是前置煽情。",
        ],
        limits=[
            "容易把所有责任扛到自己身上。",
            "面对爸爸会被触发火气，面对妈妈会有亏欠和保护欲。",
            "后半段容易因为不想卖惨而失去选题发动机。",
        ],
        story_function=[
            "叙事视角：观众通过你理解这个家的变化。",
            "成长线主角：不是只有爸妈在变，你也在变。",
            "结构控制者：你把混乱生活组织成一条可以看的故事。",
        ],
        camera_value=[
            "你的沉默、停顿、做事、忍住火气、复盘，比直接诉苦更有力量。",
            "适合拍你的手在准备药、做饭、收拾、规划路线。",
            "可以保留你现场小声吐槽和事后旁白之间的反差。",
        ],
        writing_rule=[
            "你的旁白要克制，先写事，再写感受。",
            "不要把自己写成完美孝子，要保留累、气、失败、再调整。",
            "结尾常落到：我也在学习成为这个家的家长。",
        ],
        avoid=[
            "不要过度自责，观众会累。",
            "不要每条都靠宏大和解收尾。",
            "不要把安静写成没有行动，行动本身就是你的性格。",
        ],
    ),
}


def infer_focus_characters(idea: str, story_lines: List[str]) -> List[CharacterProfile]:
    scores = {key: 0 for key in CHARACTER_PROFILES}
    keyword_map = {
        "mom": ["妈妈", "妈", "精神", "买衣服", "拍照", "看牙", "恢复", "吃什么"],
        "dad": ["爸爸", "爸", "糊涂", "闯祸", "血压", "体检", "规则", "城市"],
        "girlfriend": ["女朋友", "朱总", "小仙女", "布置", "审美", "一起", "做饭"],
        "me": ["我", "发火", "家长", "照顾", "责任", "和解", "选题", "账号"],
    }
    for key, words in keyword_map.items():
        scores[key] += sum(2 for word in words if word in idea)
    if "妈妈恢复线" in story_lines:
        scores["mom"] += 3
    if "爸爸适应线" in story_lines:
        scores["dad"] += 3
    if "女朋友共建线" in story_lines:
        scores["girlfriend"] += 3
    if "照护者成长线" in story_lines:
        scores["me"] += 3
    if all(score == 0 for score in scores.values()):
        scores.update({"mom": 1, "dad": 1, "girlfriend": 1, "me": 1})

    # Always return the four core roles. The order shows who should lead this
    # topic, but even a mom-led story may need dad/girlfriend/me as contrast.
    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return [CHARACTER_PROFILES[key] for key, _ in ordered][:4]


def relationship_guidance(character_keys: List[str]) -> List[str]:
    keys = set(character_keys)
    guidance = []
    if {"me", "mom"} <= keys:
        guidance.append("我和妈妈：核心不是照顾动作，而是她有没有重新表达选择；你负责安静托底。")
    if {"me", "dad"} <= keys:
        guidance.append("我和爸爸：核心是火气和理解之间的拉扯；要拍你差点失控又重新调整。")
    if {"me", "girlfriend"} <= keys:
        guidance.append("我和女朋友：核心是共建，不是单方面感谢；要拍她怎样把混乱变成秩序。")
    if {"mom", "girlfriend"} <= keys:
        guidance.append("妈妈和女朋友：核心是女性之间的照顾、审美和亲近，让妈妈不只是被照护。")
    if {"dad", "girlfriend"} <= keys:
        guidance.append("爸爸和女朋友：核心是糊涂老人的笨拙善意，以及女朋友如何活泼地化解尴尬。")
    if {"mom", "dad"} <= keys:
        guidance.append("爸爸和妈妈：核心是他们还能不能像家人一样互相陪伴，而不是证明谁更麻烦。")
    if not guidance:
        guidance.append("这一期人物关系较单一，需要至少设计一个互动对象，否则容易变成流水账。")
    return guidance
