# JianyingAgent

JianyingAgent 是一个面向个人短视频创作的本地内容系统。

当前默认使用 V2 架构：

- `shared_base/` 负责长期记忆
- `agents/` 负责内容理解与执行
- `orchestrator/` 负责调度
- `pipelines/` 负责粗剪流水线
- `entrypoints/` 负责入口层

## 两条主链路

### 拍前链路

- 内容大脑 Agent
- 选题写稿 Agent

输出：

- 选题判断
- 人物使用
- 关系张力
- 开头钩子
- 拍摄清单
- 粗剪提示

### 拍后链路

- 内容大脑 Agent
- 自动粗剪 Agent
- 剪映草稿导出

输出：

- 转写结果
- 筛片结果
- 时间线粗排
- 剪映草稿

## 正式入口

统一 CLI：

```bash
python -m apps
```

常用命令：

```bash
python -m apps suggest "带妈妈逛街买衣服，让她自己选一身喜欢的"
python -m apps profile --memory shared_base\memory\stories.json
python -m apps roughcut --source "E:\素材\采茶" --script "带妈妈体验采茶制茶，目标时长约180秒。" --name "采茶_小熊"
```

网页入口：

```bash
python -m webui --open
```

## 目录结构

```text
JianyingAgent/
├─ entrypoints/          # 正式入口层
│  ├─ apps/
│  └─ webui/
├─ agents/               # 内容大脑 / 选题写稿 / 自动粗剪 Agent
├─ contracts/            # Agent 间标准对象
├─ examples/             # 示例脚本
├─ infra/                # 配置与日志
├─ orchestrator/         # 调度层
├─ pipelines/            # 执行流水线
├─ shared_base/          # 正式内容共享底座
│  ├─ canon/
│  ├─ memory/
│  └─ style/
├─ apps/                 # CLI 兼容层
├─ webui/                # 网页兼容层
├─ core/                 # 兼容层
├─ skills/               # 兼容层
├─ tests/                # 测试与 smoke 脚本
├─ input/
├─ output/
├─ temp/
└─ 架构历史/
```

## 内容资产位置

正式目录：

- `shared_base/canon/`
- `shared_base/memory/stories.json`

兼容目录：

- `content_brain/` 只保留说明，不再作为主目录

## 配置

真正的配置文件在：

- `infra/config.py`

根目录的 `config.py` 仅保留兼容导出。

重点配置项：

```python
FFMPEG_PATH = "D:/soft/ffmpeg/bin/ffmpeg.exe"
FFPROBE_PATH = "D:/soft/ffmpeg/bin/ffprobe.exe"
WHISPER_MODEL = "base"
OPENAI_API_KEY = "你的 OpenAI key"
CODEX_MODEL = "gpt-5.2-codex"
```

如果本机已经登录 Codex，系统会在未设置环境变量时自动读取 `~/.codex/config.toml` 和
`~/.codex/auth.json`，复用 Codex 的 `base_url`、模型和认证信息。

## 安装依赖

```bash
pip install faster-whisper requests pyJianYingDraft
```

## Python 调用

推荐新代码直接调用调度层：

```python
from orchestrator import JianyingOrchestrator

orchestrator = JianyingOrchestrator()
orchestrator.load_agents()

result = orchestrator.process_roughcut(
    script="带妈妈体验采茶制茶，目标时长约180秒。",
    source_dir="E:/素材/采茶",
    project_name="采茶_小熊",
    export_jcc=True,
)

print(result.status)
print(result.jcc_project)
```

## 兼容入口

下面这些入口仍可运行，但不再是推荐用法：

- `python -m apps ...`
- `python -m webui ...`
- `python main.py ...`
- `python content_assistant.py ...`
- `python quick_start.py`
- `python test_caicha.py`
- `python test_dad Buddha.py`
- `python test_skill5.py`
- `from core import JianyingAgent`
- `from skills import ...`

## 相关文档

- `USAGE.md`
- `CONTENT_ASSISTANT.md`
- `架构历史/ARCHITECTURE_V1.md`
- `架构历史/ARCHITECTURE_V2.md`
