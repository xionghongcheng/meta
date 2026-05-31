#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
技能3: AI智能片段筛选打分
- 接入 Codex，按剪辑需求（口播干货 / 剧情看点 / 高光瞬间）筛选有效片段
- 输出合规起止时间码、片段排序清单、淘汰冗余片段
- 替代人工通篇翻看几小时素材，快速锁定可用镜头
"""

import os
import json
import re
from typing import List, Dict
from datetime import datetime

from contracts import DirectorPlan
from infra.llm_client import CodexClient
from utils import ensure_dir, format_time


class Skill3Analyzer:
    """AI智能片段筛选打分技能"""

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.output_dir = ensure_dir(os.path.join(config.OUTPUT_DIR, "analysis"))
        self.llm = CodexClient(config, logger)

    def analyze(
        self,
        script: str,
        transcripts: Dict[str, Dict],
        *,
        director_plan: DirectorPlan | None = None,
        output_dir: str | None = None,
    ) -> List[Dict]:
        """
        分析并筛选片段

        Args:
            script: 用户提供的脚本
            transcripts: 转写结果字典

        Returns:
            List[Dict]: 筛选后的片段列表
        """
        self.logger.info(f"开始分析片段，脚本: {script}")
        self._last_script = script

        if not self.llm.available:
            self.logger.warning("未配置OPENAI_API_KEY，使用基础筛选策略")
            return self._basic_filter(script, transcripts, output_dir=output_dir or self.output_dir)

        # 准备分析数据
        analysis_data = self._prepare_analysis_data(script, transcripts, director_plan=director_plan)

        # 调用Codex
        analysis_result = self._call_codex(analysis_data, director_plan=director_plan)

        if analysis_result:
            parsed = self._parse_llm_result(analysis_result, transcripts, director_plan=director_plan)
            return self._backfill_missing_beats(parsed, transcripts, director_plan=director_plan)
        else:
            self.logger.warning("Codex调用失败，使用基础筛选策略")
            return self._basic_filter(script, transcripts, director_plan=director_plan, output_dir=output_dir or self.output_dir)

    def _prepare_analysis_data(self, script: str, transcripts: Dict[str, Dict], director_plan: DirectorPlan | None = None) -> str:
        """准备Codex分析数据——紧凑格式，只发摘要"""
        summary_parts = []
        summary_parts.append(f"脚本: {script}\n")
        if director_plan:
            summary_parts.append(f"导演计划目标时长: {director_plan.target_duration_seconds:.0f}秒")
            summary_parts.append(f"排序原则: {director_plan.ordering_policy}")
            for beat in director_plan.beats:
                summary_parts.append(
                    f"beat={beat.beat_id}, order={beat.order}, title={beat.title}, "
                    f"priority={beat.priority}, objective={beat.objective}, "
                    f"keywords={'/'.join(beat.keywords[:6])}, refs={'/'.join(beat.reference_file_ids)}"
                )
            if director_plan.editing_rules:
                summary_parts.append("粗剪规则: " + " | ".join(director_plan.editing_rules[:6]))

        # 只发有内容的文件，紧凑格式：一行一个文件
        for file_id, transcript in transcripts.items():
            segs = transcript.get('segments', [])
            if not segs:
                continue
            ft = transcript.get('full_text', '').strip()
            if len(ft) < 3:
                continue
            # 每个文件一行：文件名(时长): 全文摘要（截断到200字）
            text = ft[:200] + ('...' if len(ft) > 200 else '')
            summary_parts.append(f"{file_id}({transcript['duration']:.0f}s): {text}")

        return "\n".join(summary_parts)

    def _call_codex(self, analysis_data: str, director_plan: DirectorPlan | None = None) -> Dict:
        """调用Codex生成片段选择JSON"""
        # 从脚本中提取目标时长
        target_duration = int(director_plan.target_duration_seconds) if director_plan else 180
        import re
        dur_match = re.search(r'目标时长[：:约]?(\d+)\s*秒', self._last_script)
        if dur_match:
            target_duration = int(dur_match.group(1))
        dur_match2 = re.search(r'(\d+)\s*分钟', self._last_script)
        if dur_match2:
            target_duration = int(dur_match2.group(1)) * 60

        beat_rules = ""
        if director_plan and director_plan.beats:
            beat_rules = "\n".join(
                [
                    f"- {beat.beat_id} | order={beat.order} | title={beat.title} | "
                    f"objective={beat.objective} | refs={'/'.join(beat.reference_file_ids)} | "
                    f"keywords={'/'.join(beat.keywords[:6])}"
                    for beat in director_plan.beats
                ]
            )

        prompt = f"""你是视频剪辑助手。根据脚本和导演计划从素材中选片段，总时长约{target_duration}秒。
每个文件后面括号是总时长秒数，冒号后是对话内容。
必须优先保证故事段落覆盖，再考虑视觉质量。
选中的片段指定start和end秒数，每段5-30秒，可从同一文件选多段。
如果给了 beat，必须按 beat.order 覆盖主要段落，不要只挑好看的镜头。

导演计划:
{beat_rules or '无，按脚本自行理解故事段落'}

{analysis_data}

返回JSON（不要其他内容）:
{{"selected_segments":[{{"file_id":"xxx","start":1.2,"end":15.3,"reason":"reason","beat_id":"beat_01"}}],"suggested_order":["beat_01","beat_02"]}}"""

        return self.llm.request_json(prompt, max_output_tokens=4000)

    def _parse_llm_result(
        self,
        llm_result: Dict,
        transcripts: Dict[str, Dict],
        director_plan: DirectorPlan | None = None,
    ) -> List[Dict]:
        """解析Codex返回结果"""
        try:
            selected_segments = []
            beat_lookup = {beat.beat_id: beat for beat in (director_plan.beats if director_plan else [])}
            beat_order = llm_result.get("suggested_order", [])

            for seg in llm_result.get('selected_segments', []):
                file_id = seg['file_id']
                start = seg['start']
                end = seg['end']
                reason = seg.get('reason', '')
                beat_id = seg.get('beat_id', '')
                beat = beat_lookup.get(beat_id)

                # 获取原始文件信息
                if file_id in transcripts:
                    transcript = transcripts[file_id]
                    start, end = self._clamp_segment_bounds(start, end, transcript.get("duration", 0.0))
                    if end <= start:
                        continue

                    selected_segments.append({
                        'file_id': file_id,
                        'start': start,
                        'end': end,
                        'duration': end - start,
                        'reason': reason,
                        'beat_id': beat_id,
                        'beat_title': beat.title if beat else "",
                        'beat_index': beat.order if beat else 999,
                        'beat_priority': beat.priority if beat else "normal",
                        'video_path': transcript.get('video_path', ''),
                        'transcript': transcript
                    })

            # 按推荐顺序排序
            if beat_order and selected_segments:
                selected_segments.sort(
                    key=lambda x: beat_order.index(x['beat_id']) if x.get('beat_id') in beat_order else x.get('beat_index', 999)
                )

            self.logger.info(f"Codex选中 {len(selected_segments)} 个片段")
            return selected_segments

        except Exception as e:
            self.logger.error(f"解析Codex结果失败: {str(e)}")
            return []

    def _basic_filter(
        self,
        script: str,
        transcripts: Dict[str, Dict],
        *,
        director_plan: DirectorPlan | None = None,
        output_dir: str,
    ) -> List[Dict]:
        """基础筛选策略：基于逐句时间戳的精确片段选取"""
        self.logger.info("使用基础筛选策略（逐句时间戳匹配）")

        if director_plan and director_plan.beats:
            selected = self._filter_with_director_plan(director_plan, transcripts)
            if selected:
                self.logger.info(f"导演计划基础筛选选中 {len(selected)} 个片段")
                self._save_analysis_result(script, selected, transcripts, output_dir=output_dir)
                return selected

        keywords = self._extract_keywords(script)
        self.logger.info(f"提取到关键词: {keywords}")

        selected_segments = []

        for file_id, transcript in transcripts.items():
            segs = transcript.get('segments', [])
            if len(segs) < 1:
                continue

            # 逐句匹配关键词，收集命中句子的时间戳
            hit_ranges = []
            for seg in segs:
                text = seg['text'].lower()
                if any(kw in text for kw in keywords):
                    # 向前扩展2秒，向后扩展1秒作为上下文
                    seg_start = max(0, seg['start'] - 2.0)
                    seg_end = min(transcript['duration'], seg['end'] + 1.0)
                    hit_ranges.append((seg_start, seg_end, seg['text'][:30]))

            if not hit_ranges:
                continue

            # 合并重叠的时间段
            merged = self._merge_ranges(hit_ranges)

            for start, end, sample_text in merged:
                # 确保片段至少有2秒
                if end - start < 2.0:
                    mid = (start + end) / 2
                    start = max(0, mid - 1.5)
                    end = mid + 1.5

                selected_segments.append({
                    'file_id': file_id,
                    'start': round(start, 3),
                    'end': round(end, 3),
                    'duration': round(end - start, 3),
                    'reason': f'匹配关键词，内容: {sample_text}...',
                    'video_path': transcript.get('video_path', ''),
                    'transcript': transcript
                })

        # 按文件内时间排序
        selected_segments.sort(key=lambda x: (x['file_id'], x['start']))

        self.logger.info(f"基础筛选选中 {len(selected_segments)} 个片段")
        self._save_analysis_result(script, selected_segments, transcripts, output_dir=output_dir)

        return selected_segments

    def _filter_with_director_plan(self, director_plan: DirectorPlan, transcripts: Dict[str, Dict]) -> List[Dict]:
        selected_segments = []

        for beat in director_plan.beats:
            beat_segments = []
            preferred_ids = set(beat.reference_file_ids)

            for file_id, transcript in transcripts.items():
                if preferred_ids and file_id not in preferred_ids:
                    continue
                segs = transcript.get("segments", [])
                if not segs:
                    continue

                hit_ranges = []
                for seg in segs:
                    text = seg["text"].lower()
                    if any(keyword.lower() in text for keyword in beat.keywords):
                        seg_start = max(0.0, seg["start"] - 1.5)
                        seg_end = min(transcript["duration"], seg["end"] + 1.5)
                        hit_ranges.append((seg_start, seg_end, seg["text"][:30]))

                if not hit_ranges and preferred_ids and file_id in preferred_ids:
                    fallback_end = min(transcript["duration"], max(director_plan.min_segment_seconds, beat.preferred_duration_seconds))
                    hit_ranges.append((0.0, fallback_end, beat.title))

                for start, end, sample_text in self._merge_ranges(hit_ranges)[:2]:
                    start, end = self._clamp_segment_bounds(start, end, transcript.get("duration", 0.0))
                    duration = round(end - start, 3)
                    if duration < director_plan.min_segment_seconds:
                        continue
                    candidate = {
                        "file_id": file_id,
                        "start": round(start, 3),
                        "end": round(end, 3),
                        "duration": duration,
                        "reason": f"{beat.title}: {sample_text}",
                        "beat_id": beat.beat_id,
                        "beat_title": beat.title,
                        "beat_index": beat.order,
                        "beat_priority": beat.priority,
                        "video_path": transcript.get("video_path", ""),
                        "transcript": transcript,
                    }
                    candidate["beat_match_score"] = round(
                        self._score_director_candidate(
                            candidate,
                            beat=beat,
                            transcript=transcript,
                            transcript_position=(start + end) / 2,
                        ),
                        3,
                    )
                    beat_segments.append(
                        candidate
                    )

            if beat_segments:
                beat_segments.sort(
                    key=lambda item: (
                        -float(item.get("beat_match_score", 0.0)),
                        item["file_id"],
                        item["start"],
                    )
                )
                selected_segments.append(beat_segments[0])

        selected_segments.sort(key=lambda item: (item.get("beat_index", 999), item["file_id"], item["start"]))
        return selected_segments

    @staticmethod
    def _clamp_segment_bounds(start: float, end: float, max_duration: float) -> tuple[float, float]:
        max_duration = max(0.0, float(max_duration or 0.0))
        if max_duration <= 0:
            return 0.0, 0.0
        start = max(0.0, min(float(start), max_duration))
        end = max(start, min(float(end), max_duration))
        return round(start, 3), round(end, 3)

    def _backfill_missing_beats(
        self,
        selected_segments: List[Dict],
        transcripts: Dict[str, Dict],
        director_plan: DirectorPlan | None = None,
    ) -> List[Dict]:
        if not director_plan or not director_plan.beats:
            return selected_segments

        covered_beats = {segment.get("beat_id") for segment in selected_segments if segment.get("beat_id")}
        if len(covered_beats) >= len(director_plan.beats):
            return selected_segments

        fallback_segments = self._filter_with_director_plan(director_plan, transcripts)
        appended = list(selected_segments)
        existing_keys = {
            (segment.get("file_id"), round(float(segment.get("start", 0.0)), 3), segment.get("beat_id"))
            for segment in appended
        }
        for fallback in fallback_segments:
            beat_id = fallback.get("beat_id")
            if beat_id in covered_beats:
                continue
            key = (fallback.get("file_id"), round(float(fallback.get("start", 0.0)), 3), beat_id)
            if key in existing_keys:
                continue
            appended.append(fallback)
            covered_beats.add(beat_id)
            existing_keys.add(key)

        appended.sort(key=lambda item: (item.get("beat_index", 999), item.get("file_id", ""), float(item.get("start", 0.0))))
        return appended

    def _score_director_candidate(
        self,
        candidate: Dict,
        *,
        beat,
        transcript: Dict,
        transcript_position: float,
    ) -> float:
        score = 0.0
        file_id = str(candidate.get("file_id", ""))
        if file_id in set(beat.reference_file_ids):
            score += 4.0

        transcript_text = self._candidate_text(candidate)
        dialogue_hits = sum(1 for line in beat.required_dialogue if self._line_overlap(line, transcript_text))
        visual_hits = sum(1 for line in beat.required_visuals if self._line_overlap(line, transcript_text))
        keyword_hits = sum(1 for keyword in beat.keywords if keyword and keyword.lower() in transcript_text)

        score += dialogue_hits * 2.5
        score += visual_hits * 1.5
        score += min(keyword_hits, 6) * 0.6

        position_ratio = 0.0
        duration = float(transcript.get("duration", 0.0) or 0.0)
        if duration > 0:
            position_ratio = min(max(transcript_position / duration, 0.0), 1.0)

        beat_priority = str(getattr(beat, "priority", "")).lower()
        if beat_priority == "anchor" and beat.order == 1:
            score += max(0.0, 1.0 - position_ratio) * 2.5
        elif beat_priority == "anchor":
            score += position_ratio * 2.5
        elif beat_priority == "core":
            score += (1.0 - abs(position_ratio - 0.55)) * 1.2
        else:
            score += (1.0 - abs(position_ratio - 0.5)) * 0.6

        preferred = float(getattr(beat, "preferred_duration_seconds", 18.0) or 18.0)
        duration_delta = abs(float(candidate.get("duration", 0.0) or 0.0) - preferred)
        score += max(0.0, 1.0 - duration_delta / max(preferred, 1.0))
        return score

    @staticmethod
    def _line_overlap(reference: str, transcript_text: str) -> bool:
        reference = reference.strip().lower()
        if not reference:
            return False
        fragments = [
            item.strip().lower()
            for item in re.split(r"[：:\"“”()（）,，。！？\s]+", reference)
            if len(item.strip()) >= 2
        ]
        return any(fragment in transcript_text for fragment in fragments[:8])

    @staticmethod
    def _candidate_text(candidate: Dict) -> str:
        transcript = candidate.get("transcript") or {}
        parts = [
            str(candidate.get("reason", "")),
            str(transcript.get("full_text", "")),
        ]
        for seg in transcript.get("segments", [])[:8]:
            parts.append(str(seg.get("text", "")))
        return " ".join(parts).lower()

    @staticmethod
    def _merge_ranges(ranges: List[tuple]) -> List[tuple]:
        """合并重叠的时间段，保留每段的样本文本"""
        if not ranges:
            return []

        sorted_ranges = sorted(ranges, key=lambda x: x[0])
        merged = [sorted_ranges[0]]

        for start, end, text in sorted_ranges[1:]:
            prev_start, prev_end, prev_text = merged[-1]
            if start <= prev_end:
                # 重叠，合并
                merged[-1] = (prev_start, max(prev_end, end), prev_text)
            else:
                merged.append((start, end, text))

        return merged

    def _extract_keywords(self, script: str) -> List[str]:
        """从脚本中智能提取关键词"""
        import re

        # 中文停用词
        stop_words = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人',
            '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
            '你', '会', '着', '没有', '看', '好', '自己', '这', '他', '她',
            '把', '那', '让', '用', '帮', '对', '然后', '可以', '进行',
            '吗', '呢', '啊', '吧', '嗯', '什么', '怎么', '这个', '那个',
            '按照', '脚本', '视频', '剪辑', '包括', '一些', '一下', '中'
        }

        # 按标点和空格切分
        words = re.split(r'[，。、；：！？\s,;!?]+', script)

        keywords = []
        for w in words:
            w = w.strip()
            if len(w) < 2:
                continue
            if w in stop_words:
                continue
            # 长句拆成 2-4 字的短词
            if len(w) > 6:
                # 按常见虚词再拆分
                sub_words = re.split(r'[的了在是我有和就不人都也到说要去看好]+', w)
                for sw in sub_words:
                    sw = sw.strip()
                    if 2 <= len(sw) <= 6 and sw not in stop_words and sw not in keywords:
                        keywords.append(sw)
            else:
                if w not in keywords:
                    keywords.append(w)

        return keywords

    def _save_analysis_result(self, script: str, segments: List[Dict], transcripts: Dict, *, output_dir: str):
        """保存分析结果"""
        ensure_dir(output_dir)
        output_path = os.path.join(output_dir, f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

        result = {
            'script': script,
            'timestamp': datetime.now().isoformat(),
            'total_files': len(transcripts),
            'selected_count': len(segments),
            'selected_segments': segments
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        self.logger.info(f"分析结果已保存: {output_path}")
