#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""LLM-backed workflow advisor with strong-signal constraints."""

from __future__ import annotations

from typing import Any

from infra import Config
from infra.llm_client import CodexClient
from workflow_catalog import list_workflows


class WorkflowAdvisorSkill:
    def __init__(self, config=None, logger=None):
        self.config = config or Config
        self.logger = logger
        self.llm = CodexClient(self.config, logger)

    def advise(self, message: str) -> dict[str, Any]:
        text = (message or "").strip()
        if not text:
            raise ValueError("请输入你现在想做什么")

        forced = self._strong_signal_hint(text)
        if forced:
            return forced

        llm_result = self._advise_with_llm(text)
        if llm_result:
            return llm_result

        return self._advise_with_rules(text)

    def _workflow_by_id(self, workflow_id: str) -> dict[str, Any] | None:
        for workflow in list_workflows():
            if workflow["id"] == workflow_id:
                return workflow
        return None

    def _advise_with_llm(self, message: str) -> dict[str, Any] | None:
        if not self.llm.available:
            return None

        workflows = list_workflows()
        workflow_lines = [
            f"- id={item['id']}, name={item['name']}, description={item['description']}, "
            f"steps={' / '.join(item['steps'])}"
            for item in workflows
        ]

        prompt = f"""你是短视频创作流程编排助手。

你的任务不是写脚本，而是根据用户当前的话，判断他现在最适合走哪条工作流。

可选工作流：
{chr(10).join(workflow_lines)}

判断原则：
1. 如果用户是在先想内容、先想拍法、先想脚本，优先推荐 script_first。
2. 如果用户已经拍好了素材，想先看看能讲什么、先分析素材、再倒推出脚本，优先推荐 material_first。
3. 如果用户已经有明确脚本或目标，只想直接生成粗剪时间线，优先推荐 roughcut。
4. 要特别识别“先拍素材后提炼”和“后配音驱动”的表达。

用户输入：
{message}

只返回 JSON，不要返回其他内容：
{{
  "workflow_id": "script_first | material_first | roughcut",
  "reason": "用简洁中文说明为什么推荐这条工作流",
  "next_step": "一句话告诉用户下一步该填什么或做什么",
  "confidence": 0.0
}}
"""

        try:
            parsed = self.llm.request_json(prompt, max_output_tokens=800, timeout=60)
            if not parsed:
                return None
            workflow_id = parsed.get("workflow_id", "").strip()
            workflow = self._workflow_by_id(workflow_id)
            if not workflow:
                return None

            return {
                "recommended_workflow": workflow,
                "reason": parsed.get("reason", ""),
                "next_step": parsed.get("next_step", ""),
                "confidence": parsed.get("confidence", 0.0),
                "message": message,
                "advisor_mode": "llm",
            }
        except Exception as exc:
            if self.logger:
                self.logger.warning("Workflow advisor LLM fallback: %s", exc)
            return None

    def _advise_with_rules(self, message: str) -> dict[str, Any]:
        text = message.strip()
        lowered = text.lower()

        if any(key in lowered for key in ["roughcut", "jcc"]) or any(
            key in text for key in ["粗剪", "时间线", "剪映", "导出草稿"]
        ):
            workflow_id = "roughcut"
            reason = "你已经明确要进入剪辑执行阶段。"
            next_step = "补充素材目录、项目名称和剪辑脚本，直接启动粗剪。"
        elif any(
            key in text
            for key in ["素材", "拍好了", "拍完了", "拍完", "先发生", "后剪辑", "后配音", "先拍"]
        ):
            workflow_id = "material_first"
            reason = "你更像是素材先发生，再从素材里提炼这一期真正要讲的内容。"
            next_step = "先提供素材目录，必要时补一句你最想保留的情绪、人物或事件。"
        else:
            workflow_id = "script_first"
            reason = "你更像是在先想题、先做脚本和拍摄准备。"
            next_step = "先输入这期的选题想法，让系统先帮你产出脚本建议。"

        return {
            "recommended_workflow": self._workflow_by_id(workflow_id),
            "reason": reason,
            "next_step": next_step,
            "confidence": 0.55,
            "message": message,
            "advisor_mode": "rules",
        }

    def _strong_signal_hint(self, message: str) -> dict[str, Any] | None:
        text = message.strip()

        material_signals = [
            "素材已经拍好了",
            "素材拍好了",
            "素材拍完了",
            "我拍好了",
            "我拍完了",
            "先拍素材",
            "先拍了",
            "后配音",
            "再配音",
            "配音后录画面",
            "画面已经录好了",
            "先发生后剪辑",
            "先发生",
        ]
        if any(signal in text for signal in material_signals):
            return {
                "recommended_workflow": self._workflow_by_id("material_first"),
                "reason": "你明确提到素材已经拍好，或者后面还要再配音。这类场景应先理解素材，再决定这一期怎么讲。",
                "next_step": "先提供素材目录，必要时再补一句你最想保留的情绪、人物或事件。",
                "confidence": 0.98,
                "message": message,
                "advisor_mode": "constraint",
            }

        roughcut_signals = [
            "直接粗剪",
            "先粗剪",
            "生成时间线",
            "导出剪映",
            "导出草稿",
            "只想剪",
        ]
        if any(signal in text for signal in roughcut_signals):
            return {
                "recommended_workflow": self._workflow_by_id("roughcut"),
                "reason": "你已经明确进入剪辑执行阶段，不需要先做题材提炼。",
                "next_step": "直接补充素材目录、项目名和剪辑脚本，启动粗剪任务。",
                "confidence": 0.98,
                "message": message,
                "advisor_mode": "constraint",
            }

        return None
