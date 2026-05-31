# JianyingAgent V1 架构总览

版本日期：2026-05-26

## V1 定位

JianyingAgent 不只是自动剪辑工具，而是一个面向个人短视频创作的内容生产系统。

V1 的核心目标：

> 用统一的内容大脑，连接选题、写稿、评稿和自动粗剪，帮助账号从“家庭苦难叙事”升级为“特殊家庭重新学习普通生活”的长期内容 IP。

## 本次 V1 调整

相对旧版“两段式”链路，这次 V1 进行了三处关键调整：

- 原先笼统的“选题脚本 Agent”拆成三个角色：`选题 Agent`、`Script Writer Agent`、`Script Evaluator Agent`。
- 新增统一脚本评分标准：`content_brain/08_SCRIPT_REVIEW_RUBRIC.md`。
- 固定工作顺序为“先写后评”，避免同一轮生成同时写稿和自评，导致标准漂移。

## 总体架构

V1 采用：

```text
内容大脑
  ↓
选题 Agent
  ↓
Script Writer Agent
  ↓
脚本初稿
  ↓
Script Evaluator Agent
  ↓
通过 / 小改 / 重写
  ↓
终稿 / 拍摄清单
  ↓
拍摄素材
  ↓
自动粗剪 Agent
  ↓
剪映粗剪工程
```

如果评估结论是 `小改` 或 `重写`，则回到 `Script Writer Agent` 改稿，再交给 `Script Evaluator Agent` 复审。

## 内容大脑目录

真正可迭代、可被工具读取的内容大脑放在：

- `content_brain/`

模块如下：

- `content_brain/01_ACCOUNT_CANON.md`  
  账号世界观和核心命题。

- `content_brain/02_CHARACTER_PROFILES.md`  
  四个核心人物的性格、能力、限制和叙事功能。

- `content_brain/03_STORY_LINES.md`  
  五条长期内容主线。

- `content_brain/04_RELATIONSHIP_DETAILS.md`  
  真实生活颗粒和关系规律。

- `content_brain/05_SCENE_RULES.md`  
  吃饭、出门、买东西、看病、家务、过节等场景规则。

- `content_brain/06_COMMERCIAL_RULES.md`  
  商业化边界、适合品类和植入原则。

- `content_brain/07_AGENT_ARCHITECTURE.md`  
  内容大脑与各 Agent 的协作方式。

- `content_brain/08_SCRIPT_REVIEW_RUBRIC.md`  
  `Script Writer Agent` 和 `Script Evaluator Agent` 共享的评分标准。

## V1 核心命题

> 记录一个特殊家庭，在爱、责任、混乱和工具的帮助下，重新学习普通生活的过程。

## V1 核心判断

每条视频都先回答：

> 这件普通事，在我们家为什么不普通？

如果回答不出来，这条容易变成流水账。

## 写稿与评稿边界

- `Script Writer Agent` 负责产出，不负责自评通过。
- `Script Evaluator Agent` 负责 review 和打分，不负责代写整稿。
- 两者共享同一份脚本规则，但不能由同一轮生成同时扮演两个角色。
- “先写后评”是固定顺序，目的是避免自我合理化。

## V1 范围

V1 先做：

- 内容大脑
- 选题 Agent
- Script Writer Agent
- Script Evaluator Agent
- 自动粗剪 Agent

暂不拆分：

- 拍摄现场 Agent
- 素材理解 Agent
- 复盘 Agent
- 商业化 Agent
- 文风 Agent

这些作为 V2 的升级方向。

## V1 不做什么

- 不追求一步生成最终成片
- 不把所有 Agent 一次性拆完
- 不让同一轮同时写稿和评稿
- 不把父母标签化为纯苦难钩子
- 不让商业化反过来控制故事
- 不做脱离历史内容的泛选题生成器

## V2 方向

V2 的目标：

> 让内容大脑能从选题、写稿、评稿、拍摄、剪辑、发布、复盘中持续学习，逐渐成为真正懂账号的编导系统。
