# HW9 规格设计模式

本文件是 HW9 Specification Agent 的课程知识层。规则来自 HW9 官方接口与现有实现，
用于指导自然语言需求拆解、JML 草拟和 critic，不替代官方接口。

## 1. Pure Query

- 适用：getter、存在性判断、统计、最短路查询。
- 规格：结果由当前模型状态唯一确定；不得修改 Network 或内部对象。
- 测试：重复调用结果一致；调用前后做深度状态快照。
- HW9 示例：`containsUser`、`queryMutualFollowingSum`、`queryShortestPath`。

## 2. Container Insert

- 前置：元素尚不存在，其他参数合法。
- 正常后置：新元素存在、字段初始化正确、长度增加 1、旧元素全部保留。
- 异常：重复 ID 或非法参数；失败时状态不变。
- HW9 示例：`addUser`、`uploadVideo`。

## 3. Bidirectional Relation Transaction

- 一个业务关系需要同步维护两个方向的容器。
- 正常后置：`A.following` 包含 B，同时 `B.followers` 包含 A。
- 删除时两个方向必须同时消失。
- 任意异常分支不得只更新一侧。
- HW9 示例：`followUser`、`unfollowUser`。

## 4. Notification Queue

- UP 主上传视频后，当前粉丝的接收队列头部加入新视频。
- 原有元素相对顺序保持不变。
- 观看操作从对应用户的未观看接收队列删除目标视频。
- 测试需覆盖无粉丝、多粉丝、连续上传、重复观看及未接收视频。

## 5. Aggregate Query

- 统计的计数单位必须明确，避免有向边、无向点对重复计数。
- 空集合结果通常为零，但必须以规格为准。
- HW9 示例：互关用户对只计一次，要求使用 `i < j` 语义。

## 6. Graph Shortest Path

- 自身到自身距离为 0。
- 路径沿 `following` 的有向边传播。
- 存在路径时返回最少边数；不存在时抛出不可达异常。
- 测试覆盖直达、多跳、环、多条路径、方向相反和不可达。

## 7. Exception Priority and Atomicity

- 多个异常条件同时满足时，依据接口中 `signals` 的排他条件识别优先级。
- 先检查第一个用户，再检查第二个用户，之后检查自关联、重复关系等业务条件。
- 所有异常测试必须额外验证对象图没有被部分修改。

## 8. HW9 Critic Checklist

1. 每个正常业务条件是否进入 `requires`？
2. 每项可观察状态变化是否进入 `ensures`？
3. `assignable` 是否覆盖必要修改，同时没有放宽到无关状态？
4. 双向关系是否同时约束两个方向？
5. 异常条件是否完整、排他且优先级明确？
6. `pure` 或 `assignable \\nothing` 是否有副作用测试？
7. 数组/容器是否覆盖空、单元素、顺序保持和重复元素？
8. 图查询是否明确方向、距离单位与不可达行为？
