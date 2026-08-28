# HW9 Specification Agent — Planner Stage

---

## Stage instructions

# Role

You are the HW9 Specification Planner. Do not generate final JML.

# Inputs

- original requirement;
- Requirement Analyzer IR;
- official interface context;
- JML Level-0 Skill;
- Specification Patterns Skill.

# Tasks

Select patterns, design normal and disjoint exceptional branches, identify `\old` uses, choose the
frame strategy, determine pure behavior, and distinguish official symbols from abstract helpers.

# Output

```markdown
## Method classification
## Applicable patterns
## Normal behavior plan
## Exceptional behavior plan
## State-change plan
## Frame-condition plan
## Old-state requirements
## Helper predicates
## Quantification / collection reasoning
## Potential specification pitfalls
## Missing interface information
```

For every helper mark `AVAILABLE_INTERFACE` or `ABSTRACT_HELPER`. Do not commit to a Java container.



---

## Skill: jml_level0.md

# JML Level-0 Specification Skill

## Goal

Design behavioral specifications for the OO course. First determine when a method may execute,
its observable result, permitted and forbidden state changes, exceptions, atomicity, and whether
it is a pure query. Syntax translation is secondary.

## Core concepts

- `requires`: condition of one behavior branch. Keep mutually exclusive branches separate.
- `ensures`: observable post-state or result. Avoid forcing an implementation container.
- `\old`: refer to the pre-state for size, counter, relation, and conditional changes.
- `assignable`: name the smallest meaningful state that may change.
- `pure`: no observable mutation, container reordering, cache write, or consumed state.
- `invariant`: property that holds for every visible object state.
- `\forall`, `\exists`, `\sum`, `\num_of`: express collection-wide semantic constraints.

## Exceptional behavior

Encode priority as disjoint conditions. If priorities are `E1 > E2 > E3`, branches must represent
`C1`, `!C1 && C2`, and `!C1 && !C2 && C3`. Do not leave overlap to implementation order.

Unless explicitly allowed, an exception performs none of the normal business updates. Tests must
verify state atomicity as well as exception type.

## Interface discipline

Never invent an official field, model field, method, or getter. If a required semantic concept is
not representable with supplied interface symbols:

1. introduce a semantic predicate marked `ABSTRACT_HELPER`;
2. list it under `missing_interface_symbols`;
3. label the result `ABSTRACT_JML_DRAFT`, not compile-ready JML.

## Quality bar

A good specification is complete, consistent, deterministic where required, explicit about frame
conditions and exceptions, grounded in the interface, and testable.



---

## Skill: spec_patterns.md

# OO Specification Design Patterns for HW9

## Pure Query

Define valid inputs, exact result, aggregation/path semantics, and `assignable \nothing` or pure
behavior. Verify nested objects, not only the top-level network.

## Unique Container Insertion

Before: ID is absent and parameters are valid. After: exactly one matching object exists, its
initial fields are correct, size increases by one, and every old object remains. Failure is atomic.

## Bidirectional Relation Transaction

One command may update two representations of one relation. Both sides change together; neither
side changes on failure. Unrelated relations and objects remain unchanged.

## Ordered Notification Insertion

Insert a new item at the front, increase length by one, and shift every old element right while
preserving relative order.

## Conditional Removal

Removing a received video constrains the target user's queue while global videos and unrelated
users remain unchanged. Specify behavior when the element was absent if observable.

## Aggregate Query

Define the counting unit and avoid double counting. Cover empty, singleton, zero-hit, all-hit, and
mixed cases. HW9 mutual following counts unordered pairs via an `i < j` interpretation.

## Directed Shortest Path

Separate same-node, reachable, and unreachable branches. Define valid paths using directed edges
and establish minimality against every other valid path.

## Exception Priority

Turn ordered validation rules into disjoint exceptional branches. Do not rely on Java check order.

## Frame Condition

For every method list both permitted changes and important unchanged state. For exceptions,
normally require all business state to remain unchanged.



---

## Original requirement

# followUser 自然语言需求

在全局 Network 中执行 `followUser(id1, id2)`。

成功关注必须同时满足：用户 `id1` 存在、用户 `id2` 存在、二者不是同一用户，且
`id1` 当前没有关注 `id2`。成功后，`id1` 的关注列表包含 `id2`，同时 `id2` 的
粉丝列表包含 `id1`，并输出 `follow_user succeeded`。除这两个方向的关系变化外，
其他用户、视频、接收视频队列以及用户基本属性均不得改变。

异常按照以下优先级处理：

1. `id1` 不存在时抛出 `UserIdNotFoundException`；
2. `id1` 存在但 `id2` 不存在时抛出 `UserIdNotFoundException`；
3. 两个用户都存在但 `id1 == id2` 时抛出 `SelfSubscriptionException`；
4. 两个用户都存在、ID 不同但关注关系已经存在时抛出 `DuplicateSubscriptionException`。

任何异常分支均不得建立部分关注关系或产生其他业务状态修改。



---

## Official interface grounding

```json
{
  "interface": "NetworkInterface",
  "name": "followUser",
  "signature": "void followUser(int id1, int id2) throws UserIdNotFoundException, SelfSubscriptionException, DuplicateSubscriptionException",
  "jml": "public normal_behavior\nrequires containsUser(id1) && containsUser(id2) && id1 != id2 && !getUser(id1).isFollowing(getUser(id2));\nassignable users[*];\nensures getUser(id1).isFollowing(getUser(id2));\nensures getUser(id2).containsFollower(getUser(id1));\nensures (* output-> \"follow_user succeeded\" *);\nalso\npublic exceptional_behavior\nsignals (UserIdNotFoundException e) !containsUser(id1);\nsignals (UserIdNotFoundException e) containsUser(id1) && !containsUser(id2);\nsignals (SelfSubscriptionException e) containsUser(id1) && containsUser(id2) && id1 == id2;\nsignals (DuplicateSubscriptionException e) containsUser(id1) && containsUser(id2) && id1 != id2 && getUser(id1).isFollowing(getUser(id2));",
  "markers": [
    "safe"
  ],
  "requires": [
    "containsUser(id1) && containsUser(id2) && id1 != id2 && !getUser(id1).isFollowing(getUser(id2))"
  ],
  "assignable": [
    "users[*]"
  ],
  "ensures": [
    "getUser(id1).isFollowing(getUser(id2))",
    "getUser(id2).containsFollower(getUser(id1))",
    "(* output-> \"follow_user succeeded\" *)"
  ],
  "signals": [
    "(UserIdNotFoundException e) !containsUser(id1)",
    "(UserIdNotFoundException e) containsUser(id1) && !containsUser(id2)",
    "(SelfSubscriptionException e) containsUser(id1) && containsUser(id2) && id1 == id2",
    "(DuplicateSubscriptionException e) containsUser(id1) && containsUser(id2) && id1 != id2 && getUser(id1).isFollowing(getUser(id2))"
  ],
  "behavior_kinds": [
    "normal_behavior",
    "exceptional_behavior"
  ]
}
```

---

## Prior artifact: analyzer.yaml

method: followUser
behavior_type: mutation
parameters:
  - id1
  - id2
entities_read:
  - Network users
  - id1 user's following relation
  - id2 user's followers relation
normal_conditions:
  - user id1 exists
  - user id2 exists
  - id1 is different from id2
  - id1 does not currently follow id2
derived_values: []
state_changes:
  - establish the relation that id1 follows id2
  - establish the inverse representation that id2 contains id1 as a follower
conditional_state_changes: []
unchanged_state:
  - all user identity, name, and age fields
  - all received-video state
  - all videos
  - all unrelated following and follower relations
return_constraints:
  - method returns void
  - successful execution outputs follow_user succeeded
exceptions:
  - name: UserIdNotFoundException
    condition: id1 does not exist
    priority: 1
  - name: UserIdNotFoundException
    condition: id1 exists and id2 does not exist
    priority: 2
  - name: SelfSubscriptionException
    condition: both users exist and id1 equals id2
    priority: 3
  - name: DuplicateSubscriptionException
    condition: both users exist, IDs differ, and id1 already follows id2
    priority: 4
atomicity_requirements:
  - every exceptional branch preserves all business state
  - the two relation representations change together on success
ordering: []
scope_constraints:
  - following is directed from id1 to id2
  - follower representation is the inverse direction on id2
missing_information: []
ambiguities: []
unsupported_assumptions: []



---

## Your response

Return only the output required by the stage instructions.
