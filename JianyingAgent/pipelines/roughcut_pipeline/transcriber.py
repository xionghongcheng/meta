#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
技能2: 离线语音时间轴转写
- GPU + BatchedInferencePipeline
- 根据视频数量/大小/时长自动调优 Whisper 参数
- 实时进度输出
"""

import os
import subprocess
import threading
from contextlib import contextmanager
from importlib.util import find_spec
from typing import List, Dict

from utils import ensure_dir, format_time, ProgressTracker


class Skill2Transcriber:

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.output_dir = ensure_dir(os.path.join(config.OUTPUT_DIR, "transcripts"))
        self.model = None
        self.pipeline = None
        # 调优参数（从config默认值初始化，由 auto_tune 覆盖）
        self.tuned_batch = config.WHISPER_BATCH_SIZE
        self.tuned_chunk = config.WHISPER_CHUNK_LENGTH
        self.tuned_workers = config.WHISPER_NUM_WORKERS

    def transcribe(self, source_files: List[Dict], *, output_dir: str | None = None) -> Dict[str, Dict]:
        total = len(source_files)
        self.logger.info(f"开始转写 {total} 个文件")
        output_dir = ensure_dir(output_dir or self.output_dir)

        if total == 0:
            self.logger.warning("没有可转写的文件")
            return {}

        # 根据负载自动调优
        self._auto_tune(source_files)

        if self.model is None:
            self._load_model()

        done_count = [0]
        lock = threading.Lock()
        results = {}

        def _safe_transcribe(file_info):
            fid = file_info['id']
            try:
                r = self._transcribe_file(file_info, output_dir=output_dir)
                with lock:
                    done_count[0] += 1
                    n = done_count[0]
                    segs = len(r['segments']) if r else 0
                    dur = r['duration'] if r else 0
                    print(f"  [{n}/{total}] {fid}: {segs}片段 {dur:.1f}s", flush=True)
                    if r:
                        results[fid] = r
            except Exception as e:
                with lock:
                    done_count[0] += 1
                    n = done_count[0]
                    print(f"  [{n}/{total}] {fid}: FAIL {e}", flush=True)

        # GPU单线程串行（BatchedInferencePipeline内部已batch并行）
        for file_info in source_files:
            _safe_transcribe(file_info)

        print(f"  === 转写完成: {len(results)}/{total} 成功 ===", flush=True)
        self.logger.info(f"成功转写 {len(results)} 个文件")
        return results

    def _auto_tune(self, source_files: List[Dict]):
        """根据文件数量、大小、时长自动调优 Whisper 参数"""
        total = len(source_files)
        if total == 0:
            return

        sizes = [f.get('file_size', 0) for f in source_files]
        durations = [f.get('duration', 0) for f in source_files]
        avg_size_mb = sum(sizes) / total / 1024 / 1024
        avg_dur = sum(durations) / total
        total_dur_min = sum(durations) / 60

        # 基于文件数量和平均时长决策
        if total <= 10 and avg_dur < 30:
            # 少量短视频：小batch，短chunk
            self.tuned_batch = 16
            self.tuned_chunk = 15
            self.tuned_workers = 2
            profile = "少量短视频"
        elif total > 80 or total_dur_min > 200:
            # 大批量：大batch加速吞吐
            self.tuned_batch = 32
            self.tuned_chunk = 20
            self.tuned_workers = 4
            profile = "大批量"
        elif avg_dur > 120:
            # 大文件（长音频）：长chunk减少碎片
            self.tuned_batch = 16
            self.tuned_chunk = 30
            self.tuned_workers = 4
            profile = "大文件"
        else:
            # 中等负载：默认值
            self.tuned_batch = 24
            self.tuned_chunk = 20
            self.tuned_workers = 4
            profile = "中等负载"

        # GPU VRAM 限制修正
        vram_mb = self._gpu_vram_mb()
        if vram_mb and vram_mb < 3000:
            self.tuned_batch = min(self.tuned_batch, 16)

        print(
            f"  [AutoTune] 场景={profile}, 文件数={total}, "
            f"平均时长={avg_dur:.0f}s, 总时长={total_dur_min:.0f}min, "
            f"VRAM={vram_mb or '?'}MB → "
            f"batch={self.tuned_batch}, chunk={self.tuned_chunk}, workers={self.tuned_workers}",
            flush=True
        )
        self.logger.info(
            f"AutoTune: 场景={profile}, batch={self.tuned_batch}, "
            f"chunk={self.tuned_chunk}, workers={self.tuned_workers}"
        )

    def _gpu_vram_mb(self):
        """获取GPU显存大小（MB），失败返回None"""
        try:
            r = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5
            )
            if r.returncode == 0:
                return int(r.stdout.decode().strip().split('\n')[0].strip())
        except Exception:
            pass
        return None

    def _load_model(self):
        self.logger.info("正在加载Whisper模型...")

        os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

        from faster_whisper import WhisperModel, BatchedInferencePipeline

        device = str(self.config.WHISPER_DEVICE or "cpu").lower()
        if device == "auto":
            device = "cpu"
            try:
                import ctranslate2
                if ctranslate2.get_supported_compute_types("cuda"):
                    device = "cuda"
                    self.logger.info("检测到CUDA GPU，使用GPU加速")
            except Exception:
                pass

        try:
            with self._proxy_guard():
                self.model = WhisperModel(
                    self.config.WHISPER_MODEL,
                    device=device,
                    compute_type="int8",
                    num_workers=self.tuned_workers,
                )
        except Exception as exc:
            if device != "cuda":
                raise
            self.logger.warning("CUDA Whisper加载失败，回退到CPU: %s", exc)
            device = "cpu"
            with self._proxy_guard():
                self.model = WhisperModel(
                    self.config.WHISPER_MODEL,
                    device=device,
                    compute_type="int8",
                    num_workers=self.tuned_workers,
                )

        self.pipeline = BatchedInferencePipeline(model=self.model)

        self.logger.info(
            f"Whisper模型加载完成 (模型: {self.config.WHISPER_MODEL}, "
            f"设备: {device}, batch={self.tuned_batch}, "
            f"chunk={self.tuned_chunk}, workers={self.tuned_workers})"
        )

    @contextmanager
    def _proxy_guard(self):
        removed = {}
        all_proxy = os.environ.get("ALL_PROXY", "")
        if all_proxy.lower().startswith("socks") and find_spec("socksio") is None:
            removed["ALL_PROXY"] = os.environ.pop("ALL_PROXY")
            self.logger.warning("检测到 SOCKS 代理但未安装 socksio，临时忽略 ALL_PROXY 以加载 Whisper 模型")
        try:
            yield
        finally:
            os.environ.update(removed)

    def _transcribe_file(self, file_info: Dict, *, output_dir: str) -> Dict:
        audio_path = file_info['audio_path']
        file_id = file_info['id']

        segments, info = self.pipeline.transcribe(
            audio_path,
            language=self.config.WHISPER_LANGUAGE,
            beam_size=5,
            vad_filter=True,
            word_timestamps=True,
            batch_size=self.tuned_batch,
            chunk_length=self.tuned_chunk,
            no_speech_threshold=0.5,
            log_prob_threshold=-0.8,
        )

        transcript_segments = []
        full_text = []

        for segment in segments:
            text = segment.text.strip()
            if text:
                transcript_segments.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": text
                })
                full_text.append(text)

        output_txt = os.path.join(output_dir, f"{file_id}.txt")
        self._save_text(transcript_segments, file_info, output_txt)

        output_srt = os.path.join(output_dir, f"{file_id}.srt")
        self._save_srt(transcript_segments, output_srt)

        self.logger.info(f"  - {file_id}: {len(transcript_segments)} 个片段")

        return {
            "file_id": file_id,
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration,
            "segments": transcript_segments,
            "full_text": " ".join(full_text),
            "txt_path": output_txt,
            "srt_path": output_srt
        }

    def _save_text(self, segments: List[Dict], file_info: Dict, output_path: str):
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"文件: {file_info['filename']}\n")
            f.write(f"检测到的语言: {file_info.get('language', 'zh')} (概率: {file_info.get('language_probability', 1.0):.2f})\n")
            f.write(f"音频时长: {file_info.get('duration', 0):.2f}秒\n")
            f.write("-" * 60 + "\n\n")
            for segment in segments:
                timestamp = f"[{format_time(segment['start'])} - {format_time(segment['end'])}]"
                f.write(f"{timestamp} {segment['text']}\n")

    def _save_srt(self, segments: List[Dict], output_path: str):
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(segments, 1):
                start_srt = self._format_srt_time(segment['start'])
                end_srt = self._format_srt_time(segment['end'])
                f.write(f"{i}\n")
                f.write(f"{start_srt} --> {end_srt}\n")
                f.write(f"{segment['text']}\n\n")

    def _format_srt_time(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
