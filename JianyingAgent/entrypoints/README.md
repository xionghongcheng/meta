# Entrypoints

这里放所有用户直接接触的入口层。

当前分成两类：

- `apps/`：命令行入口
- `webui/`：本地网页入口

它们都只是入口层，底层真正干活的仍然是：

- `orchestrator/`
- `agents/`
- `pipelines/`
- `shared_base/`
