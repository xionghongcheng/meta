#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Content memory for the creator workflow.

It turns historical voice-over collections into a searchable story library.
The first version is intentionally local and rule based, so it can work even
without an LLM API.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


PERSON_KEYWORDS = {
    "me": ["我", "小熊", "程序员", "深漂", "家长"],
    "mom": ["妈妈", "妈", "精神病", "精神疾病", "精神病院", "精神自由"],
    "dad": ["爸爸", "爸", "老爸", "糊涂", "闯祸", "电动车"],
    "girlfriend": ["女朋友", "朱总", "小仙女"],
    "friends": ["朋友", "叔叔", "阿姨", "粉丝", "网友"],
}

STORY_LINE_KEYWORDS = {
    "妈妈恢复线": ["妈妈", "精神病", "精神病院", "洗头", "买衣服", "看牙", "拍照", "恢复", "状态"],
    "爸爸适应线": ["爸爸", "老爸", "糊涂", "闯祸", "电动车", "血压", "体检", "走丢"],
    "女朋友共建线": ["女朋友", "朱总", "小仙女", "陪伴", "支持", "一起", "布置"],
    "小家建设线": ["装修", "房间", "卧室", "厨房", "客厅", "收拾", "布置", "家"],
    "迟到体验线": ["第一次", "全家福", "生日", "中秋", "大学", "长城", "逛街", "出门"],
    "照护者成长线": ["家长", "理解", "愧疚", "和解", "责任", "照顾", "焦虑", "发火"],
    "商单生活嵌入线": ["无广", "授权", "血糖仪", "血压计", "摄像头", "牙膏", "筋膜枪", "蒸锅"],
}

STAGE_KEYWORDS = {
    "救回妈妈": ["精神病院", "接回", "出院", "刚接", "三个月"],
    "回村照护": ["回村", "农村", "老家", "院子", "卖废品", "摘"],
    "家庭重建": ["装修", "房间", "全家福", "过节", "布置", "第一次"],
    "爸爸接管": ["爸爸", "糊涂", "闯祸", "电动车", "血压", "体检"],
    "城市/新生活": ["乐山", "城市", "小区", "逛街", "商场", "下午茶", "公交"],
}

TASK_KEYWORDS = [
    "买衣服", "买菜", "做饭", "吃饭", "洗头", "洗澡", "看牙", "体检", "拍照", "全家福",
    "装修", "布置", "收拾", "大扫除", "逛街", "出门", "医院", "复查", "生日", "中秋",
    "见父母", "搬家", "接爸爸", "接妈妈", "散步", "拍摄", "做家务",
]


@dataclass
class ContentStory:
    id: str
    source_file: str
    index: int
    category: str
    title: str
    text: str
    char_count: int
    people: List[str] = field(default_factory=list)
    story_lines: List[str] = field(default_factory=list)
    stage: str = "未分类"
    tasks: List[str] = field(default_factory=list)
    hook: str = ""
    ending: str = ""
    is_commercial: bool = False


class ContentMemory:
    """Searchable local memory built from historical voice-over text."""

    def __init__(self, stories: Sequence[ContentStory] | None = None):
        self.stories = list(stories or [])

    @classmethod
    def from_files(cls, paths: Sequence[str | Path]) -> "ContentMemory":
        stories: List[ContentStory] = []
        for path in paths:
            path = Path(path)
            text = path.read_text(encoding="utf-8")
            stories.extend(_parse_voiceover_file(path, text))
        return cls(stories)

    @classmethod
    def load(cls, path: str | Path) -> "ContentMemory":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls([ContentStory(**item) for item in data.get("stories", [])])

    def save(self, path: str | Path) -> str:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "story_count": len(self.stories),
            "stories": [asdict(story) for story in self.stories],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(path)

    def profile(self) -> Dict[str, object]:
        return {
            "story_count": len(self.stories),
            "total_chars": sum(story.char_count for story in self.stories),
            "people": _count_values(story.people for story in self.stories),
            "story_lines": _count_values(story.story_lines for story in self.stories),
            "stages": _count_values([[story.stage] for story in self.stories]),
            "commercial_count": sum(1 for story in self.stories if story.is_commercial),
            "top_tasks": _count_values(story.tasks for story in self.stories)[:20],
        }

    def search(self, query: str, limit: int = 8) -> List[Dict[str, object]]:
        query_tokens = _tokenize(query)
        scored = []
        for story in self.stories:
            haystack = " ".join([
                story.title,
                story.category,
                story.text[:500],
                " ".join(story.people),
                " ".join(story.story_lines),
                story.stage,
            ])
            score = _similarity(query_tokens, _tokenize(haystack))
            if score > 0:
                scored.append({"score": round(score, 4), "story": story})
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:limit]

    def related_story_lines(self, idea: str) -> List[str]:
        scores = []
        for line, keywords in STORY_LINE_KEYWORDS.items():
            score = sum(idea.count(keyword) for keyword in keywords)
            if score:
                scores.append((score, line))
        if not scores:
            return ["家庭重建", "照护者成长线"]
        return [line for _, line in sorted(scores, reverse=True)[:3]]


def _parse_voiceover_file(path: Path, text: str) -> List[ContentStory]:
    lines = text.splitlines()
    headers = []
    for pos, line in enumerate(lines):
        match = re.match(r"^\s*(\d+)\.\s*【([^】]+)】([^\n]*)\s*$", line)
        if match:
            headers.append((pos, match))

    stories: List[ContentStory] = []
    for i, (line_no, match) in enumerate(headers):
        end = headers[i + 1][0] if i + 1 < len(headers) else len(lines)
        body = "\n".join(lines[line_no + 1:end])
        body = _clean_body(body)
        if not body:
            continue

        index = int(match.group(1))
        category = match.group(2).strip()
        title = match.group(3).strip()
        story_id = f"{path.stem}_{index:03d}"
        stories.append(_build_story(story_id, path.name, index, category, title, body))
    return stories


def _build_story(
    story_id: str,
    source_file: str,
    index: int,
    category: str,
    title: str,
    text: str,
) -> ContentStory:
    full = f"{category} {title} {text}"
    people = [name for name, words in PERSON_KEYWORDS.items() if any(word in full for word in words)]
    story_lines = [name for name, words in STORY_LINE_KEYWORDS.items() if any(word in full for word in words)]
    tasks = [word for word in TASK_KEYWORDS if word in full]
    stage = _best_label(full, STAGE_KEYWORDS, "未分类")
    is_commercial = any(word in full for word in ["无广", "授权", "广告", "血糖仪", "血压计", "摄像头"])

    return ContentStory(
        id=story_id,
        source_file=source_file,
        index=index,
        category=category,
        title=title,
        text=text,
        char_count=len(text),
        people=people,
        story_lines=story_lines,
        stage=stage,
        tasks=tasks,
        hook=_first_chars(text, 90),
        ending=_last_chars(text, 110),
        is_commercial=is_commercial,
    )


def _clean_body(body: str) -> str:
    body = re.sub(r"=+", " ", body)
    body = re.sub(r"===.*?===", " ", body)
    body = re.sub(r"\[[0-9:,：\-\s]+(?:-->|-)[0-9:,：\-\s]+\]", " ", body)
    body = re.sub(r"\[[0-9:,：\-\s]+\]", " ", body)
    body = re.sub(r"\s+", " ", body).strip()
    return body


def _best_label(text: str, mapping: Dict[str, Sequence[str]], default: str) -> str:
    best_label = default
    best_score = 0
    for label, keywords in mapping.items():
        score = sum(text.count(keyword) for keyword in keywords)
        if score > best_score:
            best_score = score
            best_label = label
    return best_label


def _first_chars(text: str, n: int) -> str:
    return text[:n].strip()


def _last_chars(text: str, n: int) -> str:
    return text[-n:].strip()


def _count_values(values: Iterable[Iterable[str]]) -> List[tuple[str, int]]:
    counter = {}
    for group in values:
        for value in group:
            counter[value] = counter.get(value, 0) + 1
    return sorted(counter.items(), key=lambda item: item[1], reverse=True)


def _tokenize(text: str) -> set[str]:
    text = text.lower()
    tokens = set(re.findall(r"[a-z0-9]+", text))
    chinese = re.findall(r"[\u4e00-\u9fff]+", text)
    for chunk in chinese:
        if len(chunk) <= 2:
            tokens.add(chunk)
        else:
            for i in range(len(chunk) - 1):
                tokens.add(chunk[i:i + 2])
            for i in range(len(chunk) - 2):
                tokens.add(chunk[i:i + 3])
    return {token for token in tokens if token.strip()}


def _similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    overlap = len(left & right)
    return overlap / (len(left) ** 0.5 * len(right) ** 0.5)
