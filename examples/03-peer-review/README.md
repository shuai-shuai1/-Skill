# 03 · Simulated Peer Review

## 场景

对一篇 synthetic 算法论文执行投稿前整合式评审。三个 `perspective` 是检查视角，不是虚构的审稿人身份；如果没有独立上下文，不得宣称相互盲审。

## 台账设计

- `R1-M1`：影响中心结论的阻断项。
- `R2-M1`：非阻断的Major原创性定位问题。
- `R3-m1`：局部表达问题。
- 每项都包含主张位置、证据位置、影响和可验证的 `resolution_test`。

以 `MAJOR_REVISION` 和三个视角运行审计应得到 `PASS`。若改成 `READY`，脚本应拒绝该建议，因为仍有未关闭Major与阻断项。
