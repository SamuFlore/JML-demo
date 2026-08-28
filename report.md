# 0828 Report

## 工具调用流程

1. 课程组先写完整、准确的 JML；
2. 为每道练习写两份元信息：
   1. `requirement.md`：学生读到的自然语言需求
   2. `blank_plan.json`：决定完整 JML 中挖空的位置，并记录每个空位考察的知识点
3. `blank_plan.json` 经人工确认并标为 `teacher_approved` 后，执行 `publish-exercise`。该确定性命令在一个新的 `exercises/<题目名>/` 下自动生成：
   1. `template.java`：由完整 JML 按挖空计划替换出的学生模板
   2. `requirement.md`：复制后的学生题面
   3. `exercise.json`：从上述输入自动派生的 Web 配置
   4. `samples/`：公开样例目录。
4. 选择相应的评测 Profile，包含当前题目可用的 JML 子集与接口方法名等等（*TODO: 目前只支持样例 `followUser`*）
5. 发布。学生填写答案，提交后得到反馈：
   1. 正确性评测由脚本完成，不依赖 LLM，保证可解释性
   2. LLM 根据脚本返回的结果生成指导意见。

## 一致性评测

LLM 不参与评测，保证评测可解释和正确。  

正确 JML 不传递给 LLM，可以防止提示词注入。  

> TODO: 设计通用 Profile 形式

Profile 中填写：  
1. 允许的变量
2. 允许的方法
3. 方法语义
4. 状态集

评测脚本据此验证学生填写结果和正确 JML 是否等价，并返回格式化结果（JSON），LLM 根据学生提交、JSON 和题干生成指导意见。

## 回答若干问题

### 错误类型

| 层 | 错误代码/类别 | 含义 |
| --- | --- | --- |
| 结构检查 | `UNFILLED_BLANKS` | 还有 `{{...}}` 空位 |
| 结构检查 | `FRAMEWORK_CHANGED` | 接口签名、行为框架或锁定部分被改动 |
| 结构检查 | `EMPTY` | 提交为空 |
| 结构检查 | `STRUCTURE_OK` | 信息，不是错误；格式可进入语义检查 |
| 语义评测 | `NORMAL_CONDITION_MISMATCH` | `requires` 与参考规格不等价 |
| 语义评测 | `POSTCONDITION_MISMATCH` | `ensures` 在某个抽象前后态中不等价 |
| 语义评测 | `EXCEPTION_PARTITION_MISMATCH` | `signals` 的异常类型、条件或优先级不正确 |
| 语义评测 | `LOCKED_CLAUSE_CHANGED` | `assignable` 或锁定输出规格被改动 |
| 语义评测 | `JML_FORMAT_OR_SYMBOL` | JML 解析失败、使用未支持/不存在的符号、子句数量不符合当前 Demo 约束等 |
| 服务异常 | `JUDGE_CONFIGURATION` | 服务器缺少参考 JML 或评测脚本 |
| 服务异常 | `JUDGE_UNAVAILABLE` | 调用评测脚本失败或超时 |
| Agent 兜底 | `Agent 反馈格式异常` | LLM 没有按 JSON 契约返回；不影响确定性结果 |

### 反馈类型

1. 第一个错误位置
2. 需要注意
3. 下一步

### JML 在评测中起的作用

- 特殊评测点？
  - 统一评测 Java 和补全的 JML
- 两阶段评测中的第一阶段？
  - 第一阶段发布挖空的官方包，由学生填写 JML 后评测
  - 第二阶段学生根据自己补全的 JML 完成 Java
- 上机实验？
