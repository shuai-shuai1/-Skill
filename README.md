# Research Paper Skill · 科研论文 Skill

[![CI](https://github.com/shuai-shuai1/research-paper-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/shuai-shuai1/research-paper-skill/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/shuai-shuai1/research-paper-skill)](https://github.com/shuai-shuai1/research-paper-skill/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)](pyproject.toml)

> Evidence-first research-paper writing, polishing, peer review and reproducible scientific figures for Codex.

`research-paper` 面向工程、计算机和人工智能实证论文，把论文组织成可审计链：

`研究问题 → 主张 → 证据 → 实验/文献 → 正文 → 图表 → 结论边界`

它不承诺“一键生成可投稿论文”。它优先拦截无来源结论、正式实验与 smoke/synthetic 结果混写、不可复现图件，以及无统计依据的“显著、稳定、实时”等表述。

## 为什么使用它

| 常见风险 | 本 Skill 的处理方式 |
|---|---|
| 写作很流畅，但结论没有来源 | Evidence Ledger + Claim-Evidence Matrix |
| 单次结果被写成稳定或显著 | 多种子、不确定性与高风险措辞检查 |
| 审稿意见只停留在泛泛建议 | 稳定问题 ID、Major/Minor、阻断项与验收条件 |
| 数据图或概念图无法复现 | 数据/代码优先；可编辑源、溯源信息与图件 QA |
| AI 概念图难以继续修改 | GPT Image 2 草案 → PowerPoint 分层重建 → 渲染差分 |

## 主要能力

- 论文规划、章节架构与逐章写作；
- 证据台账和主张—证据矩阵；
- 从代码、配置、日志和正式结果生成可复现的方法与结果描述；
- 对已有稿件做分层润色、结构修订、证据审计与全文一致性扫描；
- 支持通用、中文核心和显式指定的 Nature 体系期刊风格配置；
- 生成数据图、模型图、系统图和重绘式复现图；
- 可选执行 GPT Image 2 生成科研视觉草案，再用 PowerPoint 重建为可编辑图件，并通过渲染差分进行高保真迭代；
- 拆解审稿意见、维护修改追踪表和形成逐条回复；
- 运行投稿前模拟同行评审、方法专项审查和修改稿复审，并审计 Major/Minor、阻断项和建议是否一致；
- 投稿前检查引用、术语、单位、图文和结论边界。

## 安装

从 [Releases](https://github.com/shuai-shuai1/research-paper-skill/releases) 下载 `research-paper.skill`，或克隆仓库后把 `skill/research-paper` 复制到支持 Skills 的工具目录：

```powershell
git clone https://github.com/shuai-shuai1/research-paper-skill.git
```

Skill 本体只需要 `SKILL.md`、`references/`、`scripts/` 和 `assets/`。

运行位图 QA 和像素差异比较时需要 Pillow：

```powershell
python -m pip install -r skill/research-paper/scripts/requirements.txt
```

## 30 秒开始

```text
使用 research-paper 审计这篇算法论文。先建立证据台账和主张—证据矩阵，
区分正式实验、日志、推导和未验证结果；不要改动原稿。
```

Skill 会优先输出：证据状态、核心阻断项、可安全使用的措辞，以及最小补证据动作，而不是直接生成无法核验的全文。

## 示例展厅

| 示例 | 展示内容 | 可执行检查 |
|---|---|---|
| [01 · 证据审计](examples/01-evidence-audit/) | 从合成实验记录建立证据链并审计论文结果段 | Evidence Ledger + manuscript audit |
| [02 · 分层润色](examples/02-polishing/) | 中文算法论文从过度主张改为可核查表达 | L2结构润色 + 边界冻结 |
| [03 · 模拟同行评审](examples/03-peer-review/) | 三视角整合评审、Major/Minor与阻断项 | review package audit |
| [04 · GPT Image 2 → PPT](examples/04-gpt-image-to-ppt/) | 科研概念图的可编辑重建与像素差分流程 | render comparison contract |

所有示例均为 synthetic/anonymized，不包含未公开论文或真实实验数据。完整索引见 [examples/README.md](examples/README.md)。

## 更多调用方式

```text
不要改数据口径，把这篇工程论文的结果和讨论重构成期刊风格。
```

```text
按中文核心期刊风格做 L2 结构润色，先核对摘要、表格和结论中的数字。
```

```text
基于训练日志和混淆矩阵生成可复现的论文图，标出正式实验与 smoke 运行。
```

```text
先用 GPT Image 2 生成科研概念图，再用 PPT 做可编辑高保真复现，并输出差分报告。
```

```text
对这篇算法论文做完整模拟同行评审；无法真正隔离评审上下文时请明确披露，并输出问题台账。
```

## 开发验证

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -B -m unittest discover -s tests -v
$env:PYTHONUTF8='1'
python path/to/quick_validate.py skill/research-paper
python path/to/package_skill.py skill/research-paper dist
```

上游验证器需要 PyYAML，可通过 `python -m pip install -e ".[dev]"` 安装开发依赖。Windows 非 UTF-8 终端应设置 `PYTHONUTF8=1`，避免中文路径和输出导致编码错误。发布前确认 Skill 目录不含 `__pycache__` 等生成文件。

GitHub Actions 会在 Python 3.10 和 3.12 上运行同一组测试，降低本地环境偶然通过的风险。

架构、开发规范和路线图位于 [`docs/`](docs/)。贡献前请阅读 [`CONTRIBUTING.md`](CONTRIBUTING.md)。

## 设计参考

润色和评审流程综合了分层学术写作、可执行审稿意见、复审闭环和动态风格路由等做法。Nature 体系的路由与评审边界参考了 Apache-2.0 许可的 [NatureSkills](https://github.com/Yuan1z0825/nature-skills)，本项目没有复制其项目结构或期刊专有内容。具体投稿要求仍以目标期刊的最新官方指南为准。

## 许可证

MIT。引用或重绘外部论文图时，仍需遵守原始作品的许可证、期刊政策和学术引用规范。
