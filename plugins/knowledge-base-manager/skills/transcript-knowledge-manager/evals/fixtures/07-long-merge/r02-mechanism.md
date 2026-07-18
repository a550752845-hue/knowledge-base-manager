---
synthetic_fixture: true
contains_real_personal_data: false
source_id: src-synth-ordered-reminders-007
range_id: r02
anchor: sections-3-4
previous_range: r01
next_range: r03
---

# r02 中段：提醒的功能

## 3. 机制拆分

作者把提醒拆成两个功能：第一是解释当前状态，第二是请求一个可执行动作。如果首条消息同时完成两者，第二条相同消息只是重复；如果首条只说“别忘了”，接收者仍然不知道该确认、改期还是补资料。

## 4. 暂时推论

作者仍倾向于单次提醒，但增加了限定：单次提醒必须包含状态、下一动作和退出入口。作者尚未讨论接收者对预约含义本身存在误解的情况。

过渡：下一范围给出一个破坏该前提的反例。
