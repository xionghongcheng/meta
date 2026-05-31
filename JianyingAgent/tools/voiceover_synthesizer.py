#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate and align voice-over audio assets for roughcut drafts."""

from __future__ import annotations

import json
import os
import subprocess
import wave
from dataclasses import asdict, replace
from pathlib import Path
from typing import Dict, List

from contracts import VoiceoverLine, VoiceoverPlan
from tools.agent_workspace import AgentWorkspace
from utils import ensure_dir


class VoiceoverSynthesizer:
    def __init__(self, logger):
        self.logger = logger

    def synthesize(
        self,
        voiceover_plan: VoiceoverPlan | None,
        segments: List[Dict],
        workspace: AgentWorkspace | None,
    ) -> VoiceoverPlan | None:
        if not voiceover_plan or not workspace:
            return voiceover_plan

        voice_dir = Path(workspace.scripts_dir) / "voiceover"
        ensure_dir(str(voice_dir))
        aligned_lines = self._align_lines(voiceover_plan.lines, segments)
        generated: List[VoiceoverLine] = []

        for line in aligned_lines:
            if not line.enabled or not line.text.strip():
                generated.append(line)
                continue

            output_path = voice_dir / f"{line.order:02d}_{line.beat_id}.wav"
            duration = self._synthesize_with_sapi(
                text=line.text,
                output_path=output_path,
                voice_name=voiceover_plan.voice_name,
                rate=voiceover_plan.rate,
                volume=voiceover_plan.volume,
            )
            generated.append(
                replace(
                    line,
                    audio_path=str(output_path) if duration > 0 else "",
                    duration_seconds=duration,
                )
            )

        status = "ready" if any(item.audio_path for item in generated) else "unavailable"
        error = None if status == "ready" else "No local TTS backend produced usable audio."
        package = replace(voiceover_plan, lines=generated, status=status, error=error)
        (voice_dir / "voiceover_plan.json").write_text(
            json.dumps(asdict(package), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return package

    @staticmethod
    def _align_lines(lines: List[VoiceoverLine], segments: List[Dict]) -> List[VoiceoverLine]:
        beat_starts: Dict[str, float] = {}
        for segment in segments:
            beat_id = str(segment.get("beat_id", "") or "")
            if beat_id and beat_id not in beat_starts:
                beat_starts[beat_id] = float(segment.get("actual_timeline_start", segment.get("timeline_start", 0.0)) or 0.0)

        aligned = []
        for line in lines:
            aligned.append(replace(line, preferred_start_seconds=beat_starts.get(line.beat_id, 0.0)))
        return aligned

    def _synthesize_with_sapi(
        self,
        *,
        text: str,
        output_path: Path,
        voice_name: str,
        rate: int,
        volume: int,
    ) -> float:
        ensure_dir(str(output_path.parent))
        escaped = text.replace("'", "''")
        command = f"""
$ErrorActionPreference = 'Stop'
$out = '{str(output_path)}'
if (Test-Path -LiteralPath $out) {{ Remove-Item -LiteralPath $out -Force }}
$voice = New-Object -ComObject SAPI.SpVoice
$token = $null
foreach ($item in $voice.GetVoices()) {{
  if ($item.GetDescription() -eq '{voice_name}') {{ $token = $item; break }}
}}
if ($token -ne $null) {{ $voice.Voice = $token }}
$voice.Rate = {int(rate)}
$voice.Volume = {int(volume)}
$stream = New-Object -ComObject SAPI.SpFileStream
$stream.Format.Type = 22
$stream.Open($out, 3, $true)
$voice.AudioOutputStream = $stream
[void]$voice.Speak('{escaped}', 0)
$stream.Close()
"""
        subprocess.run(["powershell", "-NoProfile", "-Command", command], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return self._wave_duration(output_path)

    @staticmethod
    def _wave_duration(path: Path) -> float:
        if not path.exists() or path.stat().st_size <= 64:
            return 0.0
        try:
            with wave.open(str(path), "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                if frames <= 0 or rate <= 0:
                    return 0.0
                return round(frames / rate, 3)
        except Exception:
            return 0.0
