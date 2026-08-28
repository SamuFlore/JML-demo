# followUser 演示样例

| 样例 | 预期结论 | 主要教学点 |
|---|---|---|
| `missing-normal-condition.java` | NEEDS_REVISION | 正常分支遗漏自我关注与重复关注限制 |
| `wrong-relation-direction.java` | NEEDS_REVISION | `id1 → id2` 被错误写成 `id2 → id1` |
| `overlapping-exceptions.java` | NEEDS_REVISION | 异常条件未带前序条件，多个分支可能同时成立 |
| `hallucinated-symbol.java` | NEEDS_REVISION | 使用了官方接口不存在的辅助谓词 |
| `incomplete.java` | INCOMPLETE | 仍有未填写占位符 |

演示时建议先用 `Hint` 审查错误样例，再切换到 `Review` 显示具体反例，最后由学生自行
完成并提交。正确填写样例属于教师资产，不随学生练习包发布。
