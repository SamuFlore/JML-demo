可以，而且我觉得老师的意思其实比你上次“给模型一个 skill 帮它写 JML”更进一步：

**不要把重点放在 Skill 本身，而是把它包装成一个真正的“规格化设计智能体（Specification Design Agent）”**。Skill 只是这个智能体内部的一部分知识来源。你最终要展示的是：**给它自然语言需求、已有接口和已有规格，它能够辅助课程组完成 JML 的设计、检查和迭代。**

这个方向和 U3 很贴。U3 本身要求学生“阅读 JML 规格，依据规格实现自己的类和方法”，而且测试不只是 `requires/ensures`，还明确涉及 `pure`、`assignable` 等副作用约束。 你之前迭代的视频社区作业又加入了合集、用户推荐、评论跳转、个性化排序等大量**跨对象状态更新**，天然适合做规格生成实验。

---

## 一、先重新定义你这次要做的东西

我建议你暂时把名字定成：

> **JML Specification Design Agent**
>
> 面向 OO 课程规格化设计任务，将自然语言业务需求转化为结构化行为约束，并进一步生成、检查和修改 JML 规格。

它不是简单的：

> 用户：帮我写 JML
> LLM：输出 JML

而是一个完整流程：

**自然语言需求 → 需求结构化 → JML 草案 → 一致性检查 → 反例检查 → 修改 → 最终规格**

这就有一个非常清晰的“智能体”味道了。

---

# 二、你首先要明确：它到底解决什么问题

你可以在组会上这样解释。

目前课程组出 U3 作业的时候，本质上经历的是：

```text
自然语言业务设想
        ↓
确定类、属性、方法
        ↓
确定前置条件
        ↓
确定正常行为
        ↓
确定异常行为
        ↓
确定哪些状态允许修改
        ↓
写成 JML
        ↓
人工检查是否遗漏 / 冲突
        ↓
写测试
```

最麻烦的其实不是 JML 的**语法转换**，而是：

> **把不完全形式化的需求变成完整、无歧义、无遗漏的规格。**

例如你之前设计的：

> “用户观看过视频后，可以主动推荐该视频；同一用户对同一视频至多推荐一次。”

真正写 JML 时至少要考虑：

```text
前置条件：
user 是否存在？
video 是否存在？
user 是否看过？
是否已经推荐过？

成功后：
recommendedVideos 中加入 video

还不能改什么：
观看记录不能变化
coins 不能变化
followers 不能变化
video 自身不能变化
其他用户不能变化

异常时：
所有状态是否保持不变？
```

而现有 U3 本身就特别强调这种 side effect 约束。例如当前指导书规定 `safe` 方法不得修改 JML 未涉及的对象或属性。

**所以智能体真正做的不是“JML 翻译器”，而是“规格设计助手”。**

这个定位很重要。

---

# 三、我建议你的 Agent 做成 5 个阶段

你不需要一上来搞很复杂的 multi-agent。

**一个 Agent + 五阶段 pipeline 就足够了。**

---

## Stage 1：Requirement Analyzer

### 自然语言 → 结构化规格需求

输入例如：

```text
用户观看过视频后，可以推荐该视频。
一个用户不能重复推荐同一个视频。
推荐成功后视频的全局推荐人数增加。
推荐行为不能修改用户的观看历史。
```

Agent 第一阶段不直接写 JML。

先生成一个中间表示：

```yaml
method: recommendVideo

parameters:
  - userId
  - videoId

preconditions:
  - userExists(userId)
  - videoExists(videoId)
  - userHasWatched(userId, videoId)
  - notAlreadyRecommended(userId, videoId)

state_changes:
  - add videoId to user.recommendedVideos

frame_conditions:
  unchanged:
    - user.watchedVideos
    - user.following
    - user.followers
    - video
    - other users

exceptions:
  - UserIdNotFoundException
  - VideoIdNotFoundException
  - VideoUnwatchedException
  - DuplicateRecommendationException
```

这一层特别重要。

因为这样你就可以研究：

> Agent 是“理解需求失败”，还是“JML 生成失败”。

这比单纯看最终 JML 对不对更有研究价值。

---

# 四、Stage 2：Specification Planner

第二阶段让 Agent 思考：

> 这个方法应该需要哪些 JML 构件？

比如：

```text
requires
ensures
signals
assignable
pure / safe
\old
\result
\forall
\exists
```

例如查询推荐视频：

```java
queryRecommendedVideos(...)
```

Agent 应判断：

> 这是查询操作，因此应该是 pure。

而：

```java
recommendVideo(...)
```

则会修改状态，因此不能是 pure，需要说明允许修改哪些对象。

这其实正好对应现有课程作业要求。

因为 U3 已经明确要求学生测试：

> 除 requires / ensures 外，还要验证 pure、assignable 等规格内容。

所以你的 Agent 不是只学几条 JML syntax，而是学习：

> **什么时候应该使用什么规格结构。**

---

# 五、Stage 3：JML Generator

到第三阶段才真正输出 JML。

例如：

```java
/*@
  @ requires containsUser(userId);
  @ requires containsVideo(videoId);
  @ requires getUser(userId).hasWatched(videoId);
  @ requires !getUser(userId).hasRecommended(videoId);
  @
  @ assignable getUser(userId).recommendedVideos;
  @
  @ ensures getUser(userId).hasRecommended(videoId);
  @ ensures getUser(userId).getRecommendedVideos().length
  @         == \old(getUser(userId).getRecommendedVideos().length) + 1;
  @*/
public void recommendVideo(int userId, int videoId);
```

这里先不用纠结最终语法是不是课程组完全一致。

你本周应该先把**Agent framework** 想清楚。

---

# 六、Stage 4 是我觉得最有意思的：Specification Critic

不要让同一个模型“写完就结束”。

让它再检查。

### 检查 1：完整性

比如：

> 有没有规定异常情况下状态不能变化？

### 检查 2：一致性

比如同时出现：

```text
assignable users;
```

但是：

```text
ensures videos changed
```

就是冲突。

### 检查 3：Frame condition

尤其 U3 特别适合：

> 修改 A 的时候，有没有误伤 B？

你当前 U3 指导书中已经多次强调：

> JML 涉及之外的对象或属性不能发生修改。

这完全可以作为 Agent 检查器的一大类。

### 检查 4：边界条件

例如：

```text
count <= 0
空候选集合
重复推荐
自己上传的视频
用户刚刚取消关注
合集取消关注后重新关注
```

这些在你现在的 U3 迭代设计里都有很好的测试素材。比如你的个性化推荐明确规定了合集更新、UP 主兴趣、关注用户推荐、全局推荐热度和 ID 五级排序。

这类需求人工特别容易漏。

---

# 七、Stage 5：Counterexample / Test Generator

这里就能把 Agent 和课程现有的 JUnit 任务连接起来。

让 Agent 根据生成的 JML 自动给出：

```text
正常 case
边界 case
异常 case
side-effect case
```

例如 `recommendVideo`：

```text
Case A
用户存在、视频存在、已观看、未推荐
→ 推荐成功

Case B
用户没有观看
→ 异常，任何状态均不改变

Case C
重复推荐
→ 异常，推荐数量不改变

Case D
成功推荐之后
→ watchedVideos 必须保持完全一致
```

甚至自动生成 JUnit skeleton。

这与你们现有 U3 的设计特别契合，因为本来学生就被要求：

> 针对某一个 JML 方法编写 JUnit，并检测错误实现。

这样你这个 Agent 就形成闭环：

```text
Requirement
   ↓
JML
   ↓
Test Oracle
```

---

# 八、那你上次说的 Skill 去哪里了？

其实**没有丢掉**。

只是从“课题主体”变成 Agent 的知识模块。

我建议设计 4 个 Skill。

### Skill A：JML Syntax Skill

包含：

```text
requires
ensures
signals
assignable
pure
\old
\result
\forall
\exists
```

以及课程组 JML Level 0 的约束。

---

### Skill B：OO Course Specification Patterns

这个反而更重要。

把历年 U3 规格总结成 pattern：

```text
Query Pattern
Mutation Pattern
Container Insert Pattern
Container Delete Pattern
Transaction Pattern
Pure Method Pattern
Exception Pattern
Ranking Pattern
Graph Query Pattern
```

例如：

### Container Insert

```text
前：
element 不存在

后：
size = old(size)+1
element 存在
old elements 全部保留
其他 container 不变
```

---

### Skill C：Consistency Checklist

例如：

```text
1. 每个业务条件有没有落到 requires / signals？
2. 每个状态变化有没有 ensures？
3. 每个未允许变化的状态有没有 frame constraint？
4. 是否存在 conflicting ensures？
5. 是否遗漏 empty / duplicate / self / missing cases？
```

---

### Skill D：U3 Domain Skill

专门描述：

```text
User
Video
Network
following
followers
watchedVideos
recommendedVideos
Collection
Comment
```

以及它们之间的 invariant。

这样你的 Agent 实际上是：

```text
               JML Skill
                   │
Course Pattern Skill ──→ Specification Agent
                   │
            U3 Domain Skill
                   │
          Consistency Skill
```

所以你原来的 Skill 思路其实可以保留。

只是变成：

> **Skill-augmented Specification Agent**

这个说法我觉得就很合理。

---

# 九、你本周千万不要一开始就做“整份指导书自动生成”

范围会直接爆炸。

我建议你做一个非常小但完整的 prototype：

## 第一阶段实验只做 3–5 个方法

就拿你已经设计过的 U3 业务。

例如：

| 方法                         | 特点           |
| -------------------------- | ------------ |
| `recommend_video`          | 状态修改         |
| `follow_collection`        | 多对象关系        |
| `jump_from_comment`        | 跨对象 + 间接状态修改 |
| `query_video_comments`     | pure         |
| `query_recommended_videos` | 复杂 pure + 排序 |

这样刚好覆盖：

```text
simple mutation
transaction
cross-object update
pure query
complex query
```

比直接生成 30 个接口有意义得多。

---

# 十、尤其建议用 `query_recommended_videos` 做“困难案例”

因为你自己这版 U3 已经给它设计了一个很复杂而且确定的排序：

```text
collectionUpdateCount ↓
uploaderWatchCount ↓
followedRecommendCount ↓
recommendCount ↓
videoId ↑
```



让 Agent 从自然语言自动生成 JML，这个案例非常适合作为 demo。

因为它会暴露很多能力：

* 能不能理解候选集合；
* 能不能理解“未观看”；
* 能不能理解“不能推荐自己上传的视频”；
* 能不能表达排序；
* 能不能表达 top-k；
* 能不能保证 query 为 pure；
* 能不能处理候选不足 count 的情况。

这就比写：

```java
getId()
```

有意义太多。

---

# 十一、你可以做一个非常简单的实验对照

这个应该会让老师觉得你的方案不只是“我想做一个 Agent”。

做三组：

| 方法       | 输入                                |
| -------- | --------------------------------- |
| Baseline | 直接 Prompt：根据需求写 JML               |
| + Skill  | Prompt + JML Skill                |
| Agent    | Requirement → Plan → JML → Critic |

然后人工标注：

```text
Syntax correctness
Requirement coverage
Frame-condition correctness
Exception completeness
Consistency
Human revision count
```

最后例如：

```text
20 个 method requirements

Direct Prompt
完整率 63%

+ Skill
完整率 76%

Agent
完整率 91%
```

现在不需要真的有结果。

但这个实验框架是非常成立的。

---

# 十二、甚至可以故意构造“有坑需求”

你之前 training 数据设计本来就强调要挖 bug、边界和复杂组合。教学组 training 要求困难数据能够测试隐藏 bug，同时避免纯粹用极端规模卡程序。

规格生成也可以做类似数据：

### 简单

```text
查询用户年龄
```

### 中等

```text
关注合集
```

### 困难

```text
重新关注合集以后，
之前产生的更新不能再次进入 collectionUpdateCount
```

或者：

```text
jump_from_comment 成功后，
目标视频如果已经观看，
uploaderWatchCount 不重复增加。
```

这些特别适合测试 Agent 有没有真正理解状态。

---

# 十三、所以我建议你本周真正做的内容

不用太大，大概下面这些就够组会了。

**第一件事：定义 Agent。**

画出：

```text
Requirement
    ↓
Requirement Analyzer
    ↓
Specification Planner
    ↓
JML Generator
    ↓
Specification Critic
    ↓
JML + Test Obligations
```

**第二件事：建立 4 个 Skill。**

```text
JML syntax
course specification patterns
U3 domain model
consistency checklist
```

**第三件事：选 3 个 U3 方法。**

我建议：

```text
recommend_video
jump_from_comment
query_recommended_videos
```

正好难度递增。

**第四件事：跑一个小实验。**

对比：

```text
Direct Prompt
Skill Prompt
Agent
```

哪怕每组只有 5～10 个需求。

**第五件事：记录人工修改。**

这甚至可能比 pass/fail 更有意义：

```text
生成规格后人工需要修改多少处？
遗漏了哪些 requirement？
最容易错的是 requires？
ensures？
assignable？
还是异常？
```

---

# 十四、你组会上可以把核心创新点说成这一句

我觉得这句话最适合你现在的状态：

> **我上次想的是通过 Skill 向模型提供 JML 的语法和设计经验，但后来觉得仅仅让模型“会写 JML”可能不够。现在我想把它进一步做成一个面向规格化设计的 Agent：先把自然语言需求拆成前置条件、状态变化、异常和 frame condition，再选择合适的 JML 结构生成规格，最后通过独立的 critic 和测试生成阶段检查遗漏和冲突。Skill 作为 Agent 内部的课程知识和设计 pattern，而不是最终产物。**

这样你和老师上次的建议就真正接上了。

---

而且我觉得你现在**不要急着先写 Agent 代码**。最优先的其实是做一件更基础的事：

> **从现有 U3 的 JML 中总结“规格设计模式”。**

因为 Agent 最终好不好，不取决于你用了 LangChain 还是手写 Python，而取决于你能不能告诉它：

> 什么叫一份“好的 OO JML 规格”。

如果你愿意，下一步我们可以直接基于你现在这版 U3 指导书，把 **`recommend_video / jump_from_comment / query_recommended_videos` 三个方法完整做一遍：自然语言需求 → 中间表示 → JML → critic → test obligation**。这个东西基本就可以直接成为你这周组会的核心 demo。
