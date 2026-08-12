# 科研论文 Skill

`research-paper` 是一个面向工程、计算机和人工智能实证论文的证据驱动写作与科研绘图 Skill。它把论文组织成一条可审计链：研究问题、主张、证据、实验或文献、正文、图表与结论边界。

它不承诺“一键生成可投稿论文”。它优先阻止三类常见问题：无来源结论、实验口径混写，以及无法复现的科研图。

## 主要能力

- 论文规划、章节架构与逐章写作；
- 证据台账和主张—证据矩阵；
- 从代码、配置、日志和正式结果生成可复现的方法与结果描述；
- 对已有稿件做结构、证据、措辞和一致性审计；
- 生成数据图、模型图、系统图和重绘式复现图；
- 可选执行 GPT Image 2 生成科研视觉草案，再用 PowerPoint 重建为可编辑图件，并通过渲染差分进行高保真迭代；
- 拆解审稿意见、维护修改追踪表和形成逐条回复；
- 投稿前检查引用、术语、单位、图文和结论边界。

## 安装

把 `skill/research-paper` 复制到支持 Skills 的工具目录，或使用 `dist/research-paper.skill` 安装发行包。Skill 本体只需要 `SKILL.md`、`references/`、`scripts/` 和 `assets/`。

运行位图 QA 和像素差异比较时需要 Pillow：

```powershell
python -m pip install -r skill/research-paper/scripts/requirements.txt
```

## 使用示例

```text
用 research-paper 帮我判断这些实验能否支撑论文第三章。
```

```text
不要改数据口径，把这篇工程论文的结果和讨论重构成期刊风格。
```

```text
基于训练日志和混淆矩阵生成可复现的论文图，标出正式实验与 smoke 运行。
```

```text
先用 GPT Image 2 生成科研概念图，再用 PPT 做可编辑高保真复现，并输出差分报告。
```

## 开发验证

```powershell
python -m unittest discover -s tests -v
python path/to/quick_validate.py skill/research-paper
python path/to/package_skill.py skill/research-paper dist
```

架构、开发规范和路线图位于 `docs/`。贡献前请阅读 `CONTRIBUTING.md`。

## 许可证

MIT。引用或重绘外部论文图时，仍需遵守原始作品的许可证、期刊政策和学术引用规范。
