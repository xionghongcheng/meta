# Skills Compatibility Layer

`skills/` 仍然保留，是为了兼容旧导入路径。

正式粗剪实现已经迁到：

- `pipelines/roughcut_pipeline/`
- `tools/cutmeta.py`

新代码建议直接从 V2 流水线或 orchestrator 调用，不再直接依赖 `skills/`。
