#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CutMeta - 视频/音频/剪映 元工具集

封装 FFmpeg、faster-whisper、ffprobe、pyJianYingDraft 四个核心工具，
提供独立可调用的方法。需要什么调什么。

用法:
    from tools.cutmeta import CutMeta

    cm = CutMeta()

    # ffprobe - 获取视频信息
    info = cm.video_info("video.mp4")

    # FFmpeg - 提取音频
    cm.extract_audio("video.mp4", "output.wav")

    # whisper - 语音转文字
    text = cm.transcribe("audio.wav")

    # pyJianYingDraft - 创建剪映草稿
    cm.create_jianying_draft("项目名", ["v1.mp4", "v2.mp4"])
"""

import os
import json
import subprocess
import tempfile
from typing import List, Dict, Optional, Tuple, Union


class CutMeta:
    """视频/音频/剪映 元工具集"""

    def __init__(self,
                 ffmpeg: str = os.getenv("FFMPEG_PATH", "D:/soft/ffmpeg/bin/ffmpeg.exe"),
                 ffprobe: str = os.getenv("FFPROBE_PATH", "D:/soft/ffmpeg/bin/ffprobe.exe"),
                 whisper_model: str = "base",
                 whisper_device: str = "cpu",
                 whisper_lang: str = "zh",
                 jianying_draft_root: str = os.getenv("JIANYING_DRAFT_ROOT", "E:/JianyingPro Drafts")):
        self.ffmpeg = ffmpeg
        self.ffprobe = ffprobe
        self.whisper_model_name = whisper_model
        self.whisper_device = whisper_device
        self.whisper_lang = whisper_lang
        self.jianying_draft_root = jianying_draft_root
        self._whisper_model = None

    # ================================================================
    #  ffprobe 工具
    # ================================================================

    def video_info(self, video_path: str) -> Dict:
        """
        获取视频完整信息（分辨率、时长、编码、旋转等）

        Args:
            video_path: 视频文件路径

        Returns:
            Dict: 包含 format 和 streams 信息

        示例:
            info = cm.video_info("video.mp4")
            print(info['width'], info['height'], info['duration'])
        """
        cmd = [self.ffprobe, "-v", "quiet", "-show_format", "-show_streams", "-of", "json", video_path]
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        if r.returncode != 0:
            return {}
        return json.loads(r.stdout.decode("utf-8"))

    def video_duration(self, video_path: str) -> float:
        """获取视频时长（秒）"""
        info = self.video_info(video_path)
        if info and "format" in info:
            return float(info["format"].get("duration", 0))
        return 0.0

    def video_resolution(self, video_path: str) -> Tuple[int, int]:
        """
        获取视频分辨率和旋转信息

        Returns:
            (display_width, display_height) 考虑旋转后的实际显示尺寸

        示例:
            w, h = cm.video_resolution("video.mp4")
            print(f"{w}x{h}")  # 如 1080x1920（竖屏）或 1920x1080（横屏）
        """
        info = self.video_info(video_path)
        for s in info.get("streams", []):
            if s.get("codec_type") == "video":
                w = int(s.get("width", 0))
                h = int(s.get("height", 0))
                # 检查旋转（iPhone 视频可能带 rotation 标记）
                tags = s.get("tags", {})
                rotation = str(tags.get("rotate", "0"))
                if rotation in ("90", "270", "-90", "-270"):
                    w, h = h, w
                return (w, h)
        return (0, 0)

    def video_orientation(self, video_path: str) -> str:
        """
        判断视频横竖屏方向

        Returns:
            "landscape" 或 "portrait"
        """
        w, h = self.video_resolution(video_path)
        return "portrait" if h > w else "landscape"

    def scan_videos(self, directory: str, extensions: list = None) -> List[Dict]:
        """
        扫描目录中所有视频文件，返回文件列表+时长+分辨率

        Returns:
            [{"path": "...", "filename": "...", "duration": 10.5, "width": 1920, "height": 1080}]

        示例:
            videos = cm.scan_videos("D:/素材/采茶")
            for v in videos:
                print(f"{v['filename']}: {v['duration']:.1f}s {v['width']}x{v['height']}")
        """
        if extensions is None:
            extensions = [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".mts"]

        results = []
        for root, dirs, files in os.walk(directory):
            for f in sorted(files):
                if any(f.lower().endswith(ext) for ext in extensions):
                    path = os.path.join(root, f)
                    w, h = self.video_resolution(path)
                    dur = self.video_duration(path)
                    results.append({
                        "path": path,
                        "filename": f,
                        "duration": dur,
                        "width": w,
                        "height": h,
                        "orientation": "portrait" if h > w else "landscape",
                        "size_mb": os.path.getsize(path) / 1024 / 1024,
                    })
        return results

    # ================================================================
    #  FFmpeg 工具
    # ================================================================

    def _run_ffmpeg(self, args: list, timeout: int = 3600) -> Tuple[bool, str]:
        """执行 FFmpeg 命令"""
        cmd = [self.ffmpeg] + args
        try:
            r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
            return r.returncode == 0, r.stderr.decode("utf-8", errors="ignore")
        except Exception as e:
            return False, str(e)

    def extract_audio(self, video_path: str, output_path: str = None,
                      sample_rate: int = 16000) -> str:
        """
        从视频中提取音频（WAV格式，适合 Whisper）

        Args:
            video_path: 视频文件路径
            output_path: 输出路径，默认同目录 .wav
            sample_rate: 采样率，默认 16000（Whisper 最佳）

        Returns:
            str: 输出音频文件路径

        示例:
            audio = cm.extract_audio("video.mp4")
            # → "video.wav"
        """
        if output_path is None:
            output_path = os.path.splitext(video_path)[0] + ".wav"

        ok, err = self._run_ffmpeg([
            "-i", video_path,
            "-vn",                   # 不要视频
            "-acodec", "pcm_s16le",  # 16bit PCM
            "-ar", str(sample_rate), # 采样率
            "-ac", "1",              # 单声道
            "-y",                    # 覆盖
            output_path
        ])
        if not ok:
            raise RuntimeError(f"FFmpeg 提取音频失败: {err}")
        return output_path

    def extract_audio_copy(self, video_path: str, output_path: str = None) -> str:
        """
        瞬间提取音频（直接复制音频流，不重新编码）

        比 extract_audio() 快 100 倍以上（无需解码重编码）。
        faster-whisper 内部会用 ffmpeg 自动转格式，所以直接传 m4a 也可以。

        Args:
            video_path: 视频文件路径
            output_path: 输出路径，默认同目录 .m4a

        Returns:
            str: 输出音频文件路径

        示例:
            audio = cm.extract_audio_copy("video.mp4")
            # → "video.m4a"（瞬间完成）
        """
        if output_path is None:
            output_path = os.path.splitext(video_path)[0] + ".m4a"

        ok, err = self._run_ffmpeg([
            "-i", video_path,
            "-vn",           # 不要视频
            "-acodec", "copy",  # 直接复制，不重编码
            "-y",
            output_path
        ])
        if not ok:
            raise RuntimeError(f"FFmpeg 音频复制失败: {err}")
        return output_path

    def extract_audio_batch(self, directory: str, output_dir: str = None,
                            instant: bool = True) -> List[str]:
        """
        批量提取目录中所有视频的音频

        Args:
            instant: True=直接复制音频流（瞬间），False=重编码为WAV（慢但兼容）

        Returns:
            List[str]: 输出音频文件路径列表

        示例:
            audios = cm.extract_audio_batch("D:/素材/")
            # → ["D:/素材/IMG_001.m4a", "D:/素材/IMG_002.m4a", ...]
        """
        extensions = [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".mts"]
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        results = []
        for root, dirs, files in os.walk(directory):
            for f in sorted(files):
                if any(f.lower().endswith(ext) for ext in extensions):
                    video_path = os.path.join(root, f)
                    ext_out = ".m4a" if instant else ".wav"
                    if output_dir:
                        out = os.path.join(output_dir, os.path.splitext(f)[0] + ext_out)
                    else:
                        out = os.path.splitext(video_path)[0] + ext_out
                    try:
                        if instant:
                            self.extract_audio_copy(video_path, out)
                        else:
                            self.extract_audio(video_path, out)
                        results.append(out)
                    except Exception as e:
                        print(f"[WARN] {f}: {e}")
        return results

    def proxy_video(self, video_path: str, output_path: str = None,
                    width: int = 480, fps: int = 10,
                    audio_bitrate: str = "32k") -> str:
        """
        生成代理视频（低分辨率预览版）

        10GB 素材 → 30~80MB 代理，用于快速预览。
        最终剪映草稿引用的是原始文件，代理仅用于预览。

        Args:
            video_path: 源视频路径
            output_path: 输出路径，默认同目录 _proxy.mp4
            width: 宽度，默认480（高度自动按比例）
            fps: 帧率，默认10
            audio_bitrate: 音频比特率，默认32k

        Returns:
            str: 代理视频路径

        示例:
            proxy = cm.proxy_video("D:/素材/IMG_001.MOV")
            # → "D:/素材/IMG_001_proxy.mp4"（极小）
        """
        if output_path is None:
            base = os.path.splitext(video_path)[0]
            output_path = f"{base}_proxy.mp4"

        ok, err = self._run_ffmpeg([
            "-i", video_path,
            "-vf", f"scale={width}:-1",
            "-r", str(fps),
            "-c:a", "aac",
            "-b:a", audio_bitrate,
            "-c:v", "libx264",
            "-crf", "28",
            "-preset", "ultrafast",
            "-y",
            output_path
        ])
        if not ok:
            raise RuntimeError(f"FFmpeg 生成代理失败: {err}")
        return output_path

    def proxy_video_batch(self, directory: str, output_dir: str = None,
                          width: int = 480, fps: int = 10) -> List[str]:
        """
        批量生成代理视频

        Args:
            directory: 素材目录
            output_dir: 代理输出目录（默认同目录）
            width: 宽度，默认480
            fps: 帧率，默认10

        Returns:
            List[str]: 代理视频路径列表

        示例:
            proxies = cm.proxy_video_batch("D:/素材/采茶", "D:/素材/采茶_proxy")
        """
        extensions = [".mp4", ".mov", ".avi", ".mkv", ".mts"]
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        results = []
        for root, dirs, files in os.walk(directory):
            for f in sorted(files):
                if any(f.lower().endswith(ext) for ext in extensions):
                    video_path = os.path.join(root, f)
                    if output_dir:
                        out = os.path.join(output_dir, os.path.splitext(f)[0] + "_proxy.mp4")
                    else:
                        out = os.path.splitext(video_path)[0] + "_proxy.mp4"
                    try:
                        self.proxy_video(video_path, out, width=width, fps=fps)
                        results.append(out)
                    except Exception as e:
                        print(f"[WARN] {f}: {e}")
        return results

    def cut_segment(self, video_path: str, start: float, end: float,
                    output_path: str = None) -> str:
        """
        无损裁剪视频片段（直接复制，不重新编码）

        使用 -ss 放在 -i 前面实现快速跳转，无需从头解码。

        Args:
            video_path: 源视频路径
            start: 起始时间（秒）
            end: 结束时间（秒）
            output_path: 输出路径

        Returns:
            str: 输出文件路径

        示例:
            out = cm.cut_segment("video.mp4", 10.5, 25.3)
            # → 截取 10.5s~25.3s 的片段（瞬间完成）
        """
        if output_path is None:
            base = os.path.splitext(video_path)[0]
            output_path = f"{base}_cut_{start:.1f}_{end:.1f}.mp4"

        duration = end - start
        ok, err = self._run_ffmpeg([
            "-ss", str(start),       # 快速跳转（放在 -i 前面）
            "-i", video_path,
            "-t", str(duration),     # 持续时间
            "-c", "copy",            # 无损复制，不重新编码
            "-avoid_negative_ts", "make_zero",
            "-y",
            output_path
        ])
        if not ok:
            raise RuntimeError(f"FFmpeg 裁剪失败: {err}")
        return output_path

    def convert_format(self, input_path: str, output_path: str = None,
                       codec: str = "libx264", audio_codec: str = "aac",
                       crf: int = 23) -> str:
        """
        转换视频格式/编码

        Args:
            input_path: 输入文件
            output_path: 输出文件（根据扩展名自动判断格式）
            codec: 视频编码，默认 libx264
            audio_codec: 音频编码，默认 aac
            crf: 质量（0-51，越小越好，默认23）

        示例:
            cm.convert_format("video.mov", "video.mp4")
            cm.convert_format("video.mp4", "video_compressed.mp4", crf=28)
        """
        if output_path is None:
            ext = ".mp4"
            output_path = os.path.splitext(input_path)[0] + ext

        ok, err = self._run_ffmpeg([
            "-i", input_path,
            "-c:v", codec,
            "-c:a", audio_codec,
            "-crf", str(crf),
            "-y",
            output_path
        ])
        if not ok:
            raise RuntimeError(f"FFmpeg 转换失败: {err}")
        return output_path

    def concat_videos(self, video_list: List[str], output_path: str) -> str:
        """
        拼接多个视频（需要编码格式一致）

        Args:
            video_list: 视频路径列表
            output_path: 输出文件路径

        示例:
            cm.concat_videos(["v1.mp4", "v2.mp4", "v3.mp4"], "merged.mp4")
        """
        # 创建临时文件列表
        fd, list_file = tempfile.mkstemp(suffix=".txt", text=True)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            for v in video_list:
                f.write(f"file '{v}'\n")

        try:
            ok, err = self._run_ffmpeg([
                "-f", "concat",
                "-safe", "0",
                "-i", list_file,
                "-c", "copy",
                "-y",
                output_path
            ])
            if not ok:
                raise RuntimeError(f"FFmpeg 拼接失败: {err}")
        finally:
            os.unlink(list_file)

        return output_path

    def change_speed(self, video_path: str, speed: float,
                     output_path: str = None) -> str:
        """
        调整视频播放速度

        Args:
            speed: 播放速度倍率（0.5=半速, 2.0=两倍速）

        示例:
            cm.change_speed("video.mp4", 1.5)  # 1.5倍速
        """
        if output_path is None:
            output_path = os.path.splitext(video_path)[0] + f"_x{speed}.mp4"

        pts = 1.0 / speed
        ok, err = self._run_ffmpeg([
            "-i", video_path,
            "-filter_complex", f"[0:v]setpts={pts}*PTS[v];[0:a]atempo={speed}[a]",
            "-map", "[v]", "-map", "[a]",
            "-y",
            output_path
        ])
        if not ok:
            raise RuntimeError(f"FFmpeg 变速失败: {err}")
        return output_path

    def add_bgm(self, video_path: str, bgm_path: str,
                bgm_volume: float = 0.3, output_path: str = None) -> str:
        """
        给视频添加背景音乐（保留原声）

        Args:
            bgm_volume: 背景音乐音量（0-1）

        示例:
            cm.add_bgm("video.mp4", "bgm.mp3", bgm_volume=0.2)
        """
        if output_path is None:
            output_path = os.path.splitext(video_path)[0] + "_bgm.mp4"

        ok, err = self._run_ffmpeg([
            "-i", video_path,
            "-i", bgm_path,
            "-filter_complex", f"[1:a]volume={bgm_volume}[bgm];[0:a][bgm]amix=inputs=2:duration=first[a]",
            "-map", "0:v", "-map", "[a]",
            "-c:v", "copy",
            "-y",
            output_path
        ])
        if not ok:
            raise RuntimeError(f"FFmpeg 添加BGM失败: {err}")
        return output_path

    # ================================================================
    #  faster-whisper 工具
    # ================================================================

    def _load_whisper(self):
        """延迟加载 Whisper 模型 + 批量推理管线（自动GPU）"""
        if self._whisper_model is None:
            os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
            from faster_whisper import WhisperModel, BatchedInferencePipeline

            device = self.whisper_device
            if device == "cpu":
                try:
                    import ctranslate2
                    if ctranslate2.get_supported_compute_types("cuda"):
                        device = "cuda"
                except Exception:
                    pass

            self._whisper_model = WhisperModel(
                self.whisper_model_name,
                device=device,
                compute_type="int8",
                num_workers=4,
            )
            self._whisper_batched = BatchedInferencePipeline(model=self._whisper_model)
        return self._whisper_batched

    def transcribe(self, audio_path: str, language: str = None,
                   output_srt: str = None, output_txt: str = None) -> Dict:
        """
        语音转文字（带时间戳，批量推理加速）

        Args:
            audio_path: 音频文件路径（也支持视频文件）
            language: 语言（默认配置的 whisper_lang）
            output_srt: SRT字幕输出路径
            output_txt: 文本输出路径

        Returns:
            {"text": "完整文本", "segments": [{"start": 0.0, "end": 5.2, "text": "..."}], "language": "zh", "duration": 45.2}

        示例:
            result = cm.transcribe("video.m4a")
            for seg in result["segments"]:
                print(f"[{seg['start']:.1f}-{seg['end']:.1f}] {seg['text']}")
        """
        pipeline = self._load_whisper()
        segments_iter, info = pipeline.transcribe(
            audio_path,
            language=language or self.whisper_lang,
            beam_size=5,
            vad_filter=True,
            word_timestamps=True,
            batch_size=24,
            chunk_length=20,
            no_speech_threshold=0.5,
            log_prob_threshold=-0.8,
        )

        segments = []
        full_text = []
        for seg in segments_iter:
            text = seg.text.strip()
            if text:
                segments.append({"start": seg.start, "end": seg.end, "text": text})
                full_text.append(text)

        result = {
            "text": " ".join(full_text),
            "segments": segments,
            "language": info.language,
            "duration": info.duration,
        }

        # 保存 SRT
        if output_srt:
            with open(output_srt, "w", encoding="utf-8") as f:
                for i, seg in enumerate(segments, 1):
                    f.write(f"{i}\n")
                    f.write(f"{self._srt_time(seg['start'])} --> {self._srt_time(seg['end'])}\n")
                    f.write(f"{seg['text']}\n\n")

        # 保存文本
        if output_txt:
            with open(output_txt, "w", encoding="utf-8") as f:
                for seg in segments:
                    f.write(f"[{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['text']}\n")

        return result

    def transcribe_batch(self, directory: str, output_dir: str = None) -> Dict[str, Dict]:
        """
        批量转写目录中所有音频/视频文件

        Returns:
            {"文件名": {"text": "...", "segments": [...], ...}}

        示例:
            results = cm.transcribe_batch("D:/素材/")
            for name, r in results.items():
                print(f"{name}: {len(r['segments'])} segments")
        """
        exts = [".wav", ".mp3", ".mp4", ".mov", ".m4a", ".flac"]
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        results = {}
        for f in sorted(os.listdir(directory)):
            if not any(f.lower().endswith(e) for e in exts):
                continue
            path = os.path.join(directory, f)
            name = os.path.splitext(f)[0]

            srt_out = os.path.join(output_dir, f"{name}.srt") if output_dir else None
            txt_out = os.path.join(output_dir, f"{name}.txt") if output_dir else None

            try:
                r = self.transcribe(path, output_srt=srt_out, output_txt=txt_out)
                results[name] = r
                print(f"  {f}: {len(r['segments'])} segments, {r['duration']:.1f}s")
            except Exception as e:
                print(f"  [WARN] {f}: {e}")

        return results

    def detect_language(self, audio_path: str) -> Tuple[str, float]:
        """
        检测音频语言

        Returns:
            (language_code, probability) 如 ("zh", 0.98)

        示例:
            lang, prob = cm.detect_language("audio.wav")
            print(f"Language: {lang} ({prob:.0%})")
        """
        model = self._load_whisper()
        segments, info = model.transcribe(audio_path, beam_size=1)
        return info.language, info.language_probability

    @staticmethod
    def _srt_time(seconds: float) -> str:
        """秒 → SRT时间码 00:00:00,000"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    # ================================================================
    #  pyJianYingDraft 工具
    # ================================================================

    def create_jianying_draft(self, project_name: str,
                              video_paths: List[str],
                              video_ranges: List[Tuple[float, float]] = None,
                              width: int = 1080, height: int = 1920,
                              fps: int = 30,
                              subtitle_srt: str = None,
                              bgm_path: str = None,
                              bgm_volume: float = 0.3,
                              blur_background: bool = True,
                              allow_replace: bool = True) -> str:
        """
        创建剪映草稿项目

        Args:
            project_name: 项目名称
            video_paths: 视频文件路径列表
            video_ranges: 每个视频的截取范围 [(start, end), ...]，为 None 则取完整视频
            width: 画布宽度（默认1080）
            height: 画布高度（默认1920，即9:16竖屏）
            subtitle_srt: 字幕SRT文件路径
            bgm_path: 背景音乐路径
            blur_background: 横屏素材是否自动加模糊背景（默认True）
            allow_replace: 是否覆盖同名草稿

        Returns:
            str: 草稿目录路径

        示例:
            # 简单版：把几个视频放入草稿
            cm.create_jianying_draft("我的项目", ["v1.mp4", "v2.mp4"])

            # 精确版：指定每个视频的起止时间
            cm.create_jianying_draft(
                "我的项目",
                ["v1.mp4", "v2.mp4"],
                video_ranges=[(5.0, 15.0), (0.0, 30.0)]
            )

            # 带字幕和背景音乐
            cm.create_jianying_draft(
                "我的项目",
                ["v1.mp4", "v2.mp4"],
                subtitle_srt="subtitle.srt",
                bgm_path="bgm.mp3"
            )
        """
        from pyJianYingDraft import (
            DraftFolder, TrackType, VideoSegment, AudioSegment,
            Timerange, SEC
        )

        SEC_UNIT = 1_000_000  # 1秒 = 1,000,000微秒

        draft_folder = DraftFolder(self.jianying_draft_root)
        script = draft_folder.create_draft(project_name, width, height, fps,
                                           allow_replace=allow_replace)

        # 视频轨道
        script.add_track(TrackType.video, "video")
        cur_pos = 0.0

        for i, vpath in enumerate(video_paths):
            if not os.path.exists(vpath):
                continue

            if video_ranges and i < len(video_ranges):
                src_start, src_end = video_ranges[i]
            else:
                src_start = 0.0
                src_end = self.video_duration(vpath)

            clip_dur = src_end - src_start
            if clip_dur <= 0:
                continue

            target = Timerange(int(cur_pos * SEC_UNIT), int(clip_dur * SEC_UNIT))
            source = Timerange(int(src_start * SEC_UNIT), int(clip_dur * SEC_UNIT))

            vseg = VideoSegment(vpath, target, source_timerange=source)

            if blur_background:
                vseg.add_background_filling("blur", blur=0.0625)

            script.add_segment(vseg, "video")
            cur_pos += clip_dur

        # 背景音乐
        if bgm_path and os.path.exists(bgm_path):
            script.add_track(TrackType.audio, "bgm")
            total_us = int(cur_pos * SEC_UNIT)
            aseg = AudioSegment(bgm_path, Timerange(0, total_us), volume=bgm_volume)
            script.add_segment(aseg, "bgm")

        # 字幕
        if subtitle_srt and os.path.exists(subtitle_srt):
            script.import_srt(subtitle_srt, "subtitle")

        script.save()

        draft_dir = os.path.join(self.jianying_draft_root, project_name)
        return draft_dir

    def list_jianying_drafts(self) -> List[str]:
        """
        列出剪映草稿目录中的所有项目

        示例:
            drafts = cm.list_jianying_drafts()
            for d in drafts:
                print(d)
        """
        from pyJianYingDraft import DraftFolder
        folder = DraftFolder(self.jianying_draft_root)
        return folder.list_drafts()

    def read_jianying_draft(self, draft_name: str) -> Dict:
        """
        读取剪映草稿的内容信息

        Returns:
            {"width": 1080, "height": 1920, "duration": 120.5,
             "tracks": [{"type": "video", "segments": 5}]}

        示例:
            info = cm.read_jianying_draft("我的项目")
        """
        draft_path = os.path.join(self.jianying_draft_root, draft_name, "draft_content.json")
        if not os.path.exists(draft_path):
            raise FileNotFoundError(f"草稿不存在: {draft_name}")

        with open(draft_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 剪映打开后会编码文件，不再是纯JSON
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return {"name": draft_name, "encoded": True,
                    "note": "草稿已被剪映编码，只能在剪映中查看"}

        cc = data.get("canvas_config", {})
        tracks_info = []
        for t in data.get("tracks", []):
            segs = t.get("segments", [])
            tracks_info.append({
                "type": t.get("type"),
                "name": t.get("name"),
                "segments": len(segs),
            })

        return {
            "width": cc.get("width", 0),
            "height": cc.get("height", 0),
            "fps": data.get("fps", 30),
            "duration": data.get("duration", 0) / 1_000_000,
            "tracks": tracks_info,
        }

    def delete_jianying_draft(self, draft_name: str):
        """删除剪映草稿"""
        from pyJianYingDraft import DraftFolder
        folder = DraftFolder(self.jianying_draft_root)
        folder.remove(draft_name)
