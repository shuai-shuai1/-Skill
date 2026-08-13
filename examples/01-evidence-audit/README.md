# 01 · Evidence Audit

## 场景

一个匿名化分类实验报告了正式测试集的 weighted F1，并引用了一篇方法文献。目标是验证结果段是否能回到明确证据，而不是判断算法本身是否优秀。

## 文件

- `evidence_ledger.csv`：一条正式测量证据和一条文献证据。
- `claim_evidence_matrix.csv`：两条主张及其允许措辞和边界。
- `manuscript.md`：带内部 `[E:...]` 标签的结果段。

## 预期结果

Evidence Ledger 和 manuscript audit 均为 `PASS`。这只说明示例字段、ID和内部追溯关系完整；真实任务还必须核对数据划分、运行身份、统计协议和引用语义。
