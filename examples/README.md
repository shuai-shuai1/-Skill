# Example Gallery

这些示例用于展示 `research-paper` 的公开、可复现使用方式。所有数据、文稿和审稿意见均为 synthetic 或 anonymized，不代表真实论文结论。

| 目录 | 适用问题 | 核心产物 |
|---|---|---|
| [`01-evidence-audit`](01-evidence-audit/) | “这些实验能否支撑论文结论？” | Evidence Ledger、Claim-Evidence Matrix、审计结果 |
| [`02-polishing`](02-polishing/) | “如何在不改变数据的情况下润色？” | 原文/修改稿/修改理由/冻结项 |
| [`03-peer-review`](03-peer-review/) | “投稿前有哪些Major问题？” | 问题台账、阻断项、可验证关闭条件 |
| [`04-gpt-image-to-ppt`](04-gpt-image-to-ppt/) | “如何把AI概念图变成可编辑科研图？” | 提示词、PPT源、渲染图、差分报告契约 |

## 本地运行

在仓库根目录执行：

```powershell
$python = "python"

& $python skill/research-paper/scripts/audit_evidence_ledger.py `
  examples/01-evidence-audit/evidence_ledger.csv

& $python skill/research-paper/scripts/audit_manuscript.py `
  examples/01-evidence-audit/manuscript.md `
  --ledger examples/01-evidence-audit/evidence_ledger.csv `
  --claims examples/01-evidence-audit/claim_evidence_matrix.csv

& $python skill/research-paper/scripts/audit_review_package.py `
  examples/03-peer-review/review_issue_ledger.csv `
  --recommendation MAJOR_REVISION `
  --require-perspectives 3
```

预期三个命令均返回 `PASS`。`MAJOR_REVISION` 通过表示“问题台账与建议内部一致”，不表示论文科学有效。
