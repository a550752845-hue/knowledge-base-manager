---
synthetic_fixture: true
contains_real_personal_data: false
record_id: verify-synth-checklist-004
record_type: verification-ledger
verified_on: 2026-06-01
sensitivity: internal
---

# 合成核验记录

本记录描述完全合成的受控演练，只用于评测知识分类，不代表真实业务结果。

## 已通过核验的命题

- 命题：在固定的 20 个合成装箱场景中，未使用检查清单时记录到 12 次步骤遗漏；在另 20 个同结构场景中使用同一版检查清单时记录到 8 次步骤遗漏。
- 方法：场景脚本、物料顺序、判定规则和观察角色保持一致；两组均由离线演练生成。
- 样本范围：40 个合成场景，不包含真实订单、人员或客户。
- 核验日期：2026-06-01。
- 锚点：`verification-ledger#verified-checklist-omissions`。
- 有效边界：只能陈述该合成演练中的遗漏计数，不能推断真实分拣站效果，也不能证明标签颜色有效。

## 未通过核验的命题

| 来源命题 | 状态 | 缺口 |
| --- | --- | --- |
| 薄荷色标签使错误下降 41% | unresolved | 无原始计数、订单量、基线控制或单变量设计 |
| 新操作员八分钟学会颜色规则 | unresolved | 无时间记录和统一达标定义 |

## 禁止的合并

不得把检查清单的核验结果当成薄荷色标签主张的证据，也不得把两个未核主张写成 `verified-fact`。
