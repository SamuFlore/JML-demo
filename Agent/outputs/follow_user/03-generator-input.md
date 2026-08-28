# HW9 Specification Agent — Generator Stage

---

## Stage instructions

# Role

You are the HW9 JML Specification Generator.

# Inputs

- original requirement;
- structured IR;
- specification plan;
- official interface context;
- JML Level-0 Skill.

# Goal

Generate the most precise specification supported by the supplied interface. Cover normal behavior,
postconditions, frame conditions, pure constraints, disjoint exception priority, atomicity, old-state
effects, and return constraints.

# Interface safety

Never invent an official symbol. If required semantics cannot be represented, use a clearly marked
`ABSTRACT_HELPER`, list it as missing, and return `ABSTRACT_JML_DRAFT`.

# Output

````markdown
STATUS: FINAL_JML | ABSTRACT_JML_DRAFT

SPECIFICATION:
```java
...
```

ABSTRACT_HELPERS:
MISSING_INTERFACE_SYMBOLS:
REQUIREMENT_TO_CLAUSE_MAP:
- requirement:
  generated_clause:
NOTES:
````



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

## Prior artifact: plan.md

## Method classification

State-changing transaction over a bidirectionally represented directed relation.

## Applicable patterns

- Bidirectional Relation Transaction
- Exception Priority
- Frame Condition

## Normal behavior plan

Use one normal branch requiring both users, distinct IDs, and an absent following relation. Ensure
both observable directions exist afterward and preserve the required success output.

## Exceptional behavior plan

Create four disjoint branches in the stated priority order. Each branch uses `assignable \nothing`
to encode failure atomicity.

## State-change plan

Permit updates to user relation state through `users[*]`. Require both `isFollowing` and
`containsFollower` postconditions.

## Frame-condition plan

The official `safe` extension and `assignable users[*]` permit only described user-state changes.
Add explicit semantic notes that unrelated relations, user fields, received videos, and videos stay
unchanged. Exceptional branches use `assignable \nothing`.

## Old-state requirements

No numeric counter or size delta is required by the supplied interface. The absent relation appears
in the normal precondition, so no additional `\old` expression is needed.

## Helper predicates

- `containsUser`: AVAILABLE_INTERFACE
- `getUser`: AVAILABLE_INTERFACE
- `UserInterface.isFollowing`: AVAILABLE_INTERFACE
- `UserInterface.containsFollower`: AVAILABLE_INTERFACE

## Quantification / collection reasoning

No helper quantifier is required for the two directly observable relation postconditions.

## Potential specification pitfalls

- updating only following or only followers;
- overlapping missing-user exception branches;
- allowing self-follow to reach duplicate checking;
- omitting exception atomicity;
- reversing the follower relation direction.

## Missing interface information

The interface does not expose a concise predicate for “all unrelated user fields unchanged”; the
course `safe` semantics supplies this frame rule. No invented official helper will be used.



---

## Your response

Return only the output required by the stage instructions.
