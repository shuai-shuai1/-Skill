# 架构说明

## 目标

`research-paper` 通过证据台账和质量关卡，把论文写作、实验描述和科研绘图连接为可审计流程。它不实现新的大模型、文档编辑器或训练框架。

## 分层

```text
Trigger metadata
  -> SKILL.md router and invariants
      -> references: task-specific reasoning rules
      -> assets/templates: stable work-product contracts
      -> scripts: deterministic validation and initialization
          -> external capabilities: web research, documents, imagegen, presentations
```

### SKILL.md

职责：触发描述、主模式选择、硬性边界、核心工作流和资源索引。

边界：不承载大段学科规范、绘图代码模板、API 文档或某一篇论文的具体规则。

### references

职责：为模式提供按需加载的方法论。所有 reference 都由 `SKILL.md` 直接链接，避免深层引用链。

### assets/templates

职责：定义跨任务稳定的数据结构，包括 Paper Brief、Evidence Ledger、Claim-Evidence Matrix、Review Issue Ledger、Figure Specification 和 PPT Reproduction Specification。

### scripts

职责：处理确定性、重复且容易出错的操作。脚本只能报告其实际检查范围，不能输出“科学有效”之类综合判定。

### 外部能力

- 文献检索与事实核验使用当前环境的网络或学术检索能力。
- DOCX/PDF/LaTeX 使用相应文档技能，不在本仓库复制编辑器。
- GPT Image 2 使用当前环境的 `imagegen` Skill，不在本仓库实现 SDK 客户端。
- PowerPoint 使用当前环境的 Presentations Skill；本 Skill 只定义科研图复现契约和 QA。

## 数据流

```text
User materials
 -> Paper Brief
 -> Evidence Ledger
 -> Claim-Evidence Matrix
 -> Chapter plan + Polishing/Review contracts + Figure Specifications
 -> Manuscript + Figure Packages
 -> Deterministic audits + expert review
 -> Delivery package
```

## Figure 可选分支

```text
Scientific requirement
 -> Figure Specification
 -> route selection
    -> data/code figure
    -> editable vector diagram
    -> GPT Image 2 bitmap concept
       -> PowerPoint layer reconstruction
       -> render PNG
       -> pixel difference report
       -> single-variable iteration
```

像素比较仅用于用户自有、AI 生成、授权或允许复现的参考图。对外部论文图默认进入结构保真重绘，不进入逐像素目标。

## 润色与模拟评审边界

```text
Manuscript snapshot
 -> task / paper type / section / language / venue profile
 -> consistency sweep
 -> bounded polish
 -> immutable review packet
 -> source-grounded issue ledger
 -> post-review synthesis or re-review
```

风格配置不改变证据强度。模拟评审视角不是虚构人物；只有真实隔离上下文时才允许声明相互盲审。评审建议由未关闭 Major 与阻断项约束，综合分只能辅助诊断。

## 依赖策略

- Python 3.10+；
- 标准库处理 CSV、JSON、文本和工作区；
- Pillow 处理位图 QA 和差分；
- Matplotlib 仅用于提供公共绘图样式和用户图脚本；
- 不绑定特定 agent 框架、操作系统路径或私有模型 API。

## 兼容性

CSV 表头和 CLI 参数视为公开接口。新增字段优先采用可选字段；删除或重命名字段需要主版本升级。自动检查规则变严格时必须补充迁移说明和测试。
