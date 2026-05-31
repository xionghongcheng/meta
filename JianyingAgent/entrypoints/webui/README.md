# Web UI

`webui/` 是 JianyingAgent 的本地网页层。

特点：

- 页面层与底层工具分开
- 底层仍然走 `orchestrator/ agents/ pipelines/ shared_base/`
- 不引入 Flask / FastAPI / Gradio，使用标准库 HTTP 服务

启动方式：

```bash
python -m webui
```

默认地址：

```text
http://127.0.0.1:8765
```
