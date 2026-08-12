# ADR 0001：采用证据优先的薄总控架构

- Status: Accepted
- Date: 2026-08-12

## Context

科研论文任务同时包含写作、实验、引用、绘图、审稿和格式。把全部规范放入一个 `SKILL.md` 会占用大量上下文；把任务拆成大量 agent 文件又会增加运行环境依赖和职责重叠。

## Decision

采用“薄 `SKILL.md` + 按需 references + 稳定模板 + 少量确定性脚本”的结构。所有模式共享 Evidence Ledger 和 Claim-Evidence Matrix。图件不是独立装饰流程，而是主张—证据链的一部分。

GPT Image 2 到 PowerPoint 的高保真复现作为 `figure` 的可选分支，不成为独立顶层模式。外部图像生成和 PowerPoint 实现交给环境已有技能，本仓库只定义科学边界、输入输出契约和差分 QA。

## Consequences

优点：上下文可控、模块职责明确、运行环境依赖小、证据口径一致。缺点：跨模块任务需要显式路由，使用者必须维护台账，复杂文档编辑仍依赖外部技能。

## Rejected alternatives

- 复制一个大而全的多 agent 论文流水线：职责重复，开源可移植性差。
- 只发布提示词集合：无法稳定验证证据和图件交付。
- 在本仓库实现图像 API 和 PPT 引擎：重复现有能力，依赖和维护成本过高。
