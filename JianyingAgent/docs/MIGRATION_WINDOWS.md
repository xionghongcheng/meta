# Windows Migration Guide

This guide is for moving JianyingAgent to another internal Windows machine.

## 1. Copy files

Copy the whole project directory:

```text
JianyingAgent/
```

Do not rely on absolute paths from the original machine. Each machine should own its own `.env`.

## 2. Install prerequisites

- Python 3.11+
- FFmpeg and FFprobe
- Jianying/CapCut desktop app
- NVIDIA driver/CUDA is optional, but recommended for faster Whisper transcription

## 3. Setup Python environment

Run from the project root:

```powershell
.\setup.ps1
```

This creates `.venv`, installs Python dependencies, creates `.env` if missing, and downloads FFmpeg into `vendor/ffmpeg` unless you pass `-SkipFFmpeg`.

To pre-download the default faster-whisper model during setup:

```powershell
.\setup.ps1 -DownloadWhisperModel -WhisperModel base
```

## 4. Edit `.env`

Set machine-local paths:

```text
FFMPEG_PATH=vendor/ffmpeg/bin/ffmpeg.exe
FFPROBE_PATH=vendor/ffmpeg/bin/ffprobe.exe
JIANYING_DRAFT_ROOT=E:/JianyingPro Drafts
```

For Codex/OpenAI:

- If the machine has Codex configured, leave `OPENAI_API_KEY` empty.
- If it does not have Codex configured, set `OPENAI_API_KEY` and optionally `OPENAI_RESPONSES_URL` / `CODEX_MODEL`.

## 5. Start WebUI

```powershell
.\run_webui.ps1
```

By default it listens on `0.0.0.0:8765`, so other internal computers on the same network can open:

```text
http://<machine-ip>:8765
```

## 6. Validate

Run these checks from the project root:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_director_plan tests.test_segment_ranker
.\.venv\Scripts\python.exe -m py_compile infra\config.py infra\llm_client.py pipelines\roughcut_pipeline\analyzer.py
```

For a real roughcut smoke test, use the WebUI or:

```powershell
.\.venv\Scripts\python.exe -m apps roughcut --source "E:\素材\项目A" --script "目标时长约120秒，优先保留人物互动和关键对白。" --name "项目A_粗剪"
```

## Notes

- Keep `.env` local to each machine.
- Do not commit or share API keys in screenshots or docs.
- Copying `.codex/auth.json` between machines is not recommended. Use each machine's own Codex login or set `OPENAI_API_KEY` in `.env`.
