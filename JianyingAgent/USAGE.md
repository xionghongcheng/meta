# 使用指南

## 一、自动粗剪

推荐入口：

```bash
python -m apps roughcut --source "E:\素材\项目A" --script "保留有说话内容和明显反应的片段，目标时长约120秒。" --name "项目A_粗剪"
```

常用参数：

- `--source`：素材目录
- `--script`：剪辑目标或脚本描述
- `--name`：项目名
- `--duration`：目标时长，单位秒
- `--width` / `--height`：画布尺寸
- `--srt`：指定字幕文件
- `--bgm`：指定背景音乐
- `--no-jcc`：不导出剪映草稿

交互式方式：

```bash
python -m apps roughcut
```

## 二、选题写稿

导入历史配音：

```bash
python -m apps ingest "E:\素材\全部配音文字汇总.txt" --out shared_base\memory\stories.json
```

查看故事库画像：

```bash
python -m apps profile --memory shared_base\memory\stories.json
```

生成选题脚本建议：

```bash
python -m apps suggest "带妈妈逛街买衣服，让她自己选一身喜欢的"
```

保存为 Markdown：

```bash
python -m apps suggest "带妈妈逛街买衣服，让她自己选一身喜欢的" --out temp\content_memory\sample_brief.md
```

## 三、统一入口

```bash
python -m apps
```

它会显示所有推荐命令。

## 四、Python 调用

推荐新代码直接使用调度层：

```python
from orchestrator import JianyingOrchestrator

orchestrator = JianyingOrchestrator()
orchestrator.load_agents()

result = orchestrator.process_roughcut(
    script="带爸妈逛大学，目标时长约90秒。",
    source_dir="E:/素材/大学",
    project_name="逛大学",
    export_jcc=True,
)
```

## 五、配置说明

正式配置文件：

- `infra/config.py`

## 六、输出目录

```text
output/
├─ analysis/             # 片段分析结果
├─ jianying_projects/    # JCC 信息文件
├─ logs/                 # 运行日志
├─ transcripts/          # 转写文本和 SRT
└─ videos/               # 非 jcc 模式下的成片
```

## 七、兼容入口

如果你有历史脚本，还可以继续使用：

```bash
python main.py ...
python content_assistant.py ...
python quick_start.py
python test_caicha.py
```

但新脚本建议统一改到：

```bash
python -m apps ...
```

示例脚本现在位于：

- `examples/quick_start.py`

smoke test 现在位于：

- `tests/smoke/test_caicha.py`
- `tests/smoke/test_dad_buddha.py`
- `tests/smoke/test_skill5_exporter.py`
