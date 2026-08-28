# followUser 演示样例

| 样例 | 预期结论 | 主要教学点 |
|---|---|---|
| `complete.jml` | CORRECT | 正常条件、双向关系和异常优先级完整 |
| `missing-normal-condition.jml` | NEEDS_REVISION | 正常分支遗漏自我关注与重复关注限制 |
| `wrong-relation-direction.jml` | NEEDS_REVISION | `id1 → id2` 被错误写成 `id2 → id1` |
| `overlapping-exceptions.jml` | NEEDS_REVISION | 异常条件未带前序条件，多个分支可能同时成立 |
| `hallucinated-symbol.jml` | NEEDS_REVISION | 使用了官方接口不存在的辅助谓词 |
| `incomplete.jml` | INCOMPLETE | 仍有未填写占位符 |

演示时建议先用 `Hint` 审查错误样例，再切换到 `Review` 显示具体反例，最后载入
`complete.jml` 验证修复结果。

