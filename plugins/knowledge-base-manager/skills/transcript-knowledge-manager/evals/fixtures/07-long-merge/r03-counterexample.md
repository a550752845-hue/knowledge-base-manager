---
synthetic_fixture: true
contains_real_personal_data: false
source_id: src-synth-ordered-reminders-007
range_id: r03
anchor: sections-5-6
previous_range: r02
next_range: r04
---

# r03 反例：高不确定性预约

## 5. 反例

在完全合成的高不确定性场景中，接收者误以为“预约成功”表示已经付款，所以收到包含下一动作的单次提醒时仍然没有回应。后续访谈脚本显示，问题不是忘记，而是对状态含义理解不同。

## 6. 主张修正

这个反例推翻了“一次提醒总是足够”的强版本。作者改为主张：当状态含义存在高不确定性时，需要先用一条消息校准含义，再用另一条消息请求动作。两条消息承担不同功能，不能被当成重复催促。

过渡：最后范围将把初始主张和反例合并成条件策略。
