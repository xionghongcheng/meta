# 内容选题和脚本助手

这个模块是 JianyingAgent 的拍前链路。

它依赖两类资产：

- 内容共享底座：`shared_base/canon/`
- 故事记忆库：`shared_base/memory/stories.json`

## 正式入口

推荐使用统一 CLI：

```bash
python -m apps suggest "带妈妈逛街买衣服，让她自己选一身喜欢的"
python -m apps profile --memory shared_base\memory\stories.json
python -m apps ingest "E:\素材\全部配音文字汇总.txt" --out shared_base\memory\stories.json
```

## 输出内容

每次建议会包含：

- 故事线判断
- 重复风险
- 人物使用方式
- 关系张力
- 相似历史故事
- 新角度
- 开头钩子
- 故事梗概
- 必拍画面
- 必收对白
- 配音大纲
- 粗剪提示

## 实现位置

- `apps/topic_cli.py`
- `agents/topic_writer_agent/`
- `shared_base/memory/`

## 兼容入口

根目录的 `content_assistant.py` 仍然可以运行，但现在只作为兼容入口保留。
