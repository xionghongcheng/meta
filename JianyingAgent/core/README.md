# Core Compatibility Layer

`core/` 仍然保留，是为了兼容历史代码：

- `from core import JianyingAgent`
- `from core import ContentMemory`
- `from core import TopicScriptAssistant`

新代码建议直接使用：

- `orchestrator/`
- `agents/`
- `shared_base/`
