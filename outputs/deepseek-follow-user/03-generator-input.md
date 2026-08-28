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

```yaml
method:
  behavior_type: mutation
  parameters:
    - id1
    - id2
  entities_read:
    - user(id1)
    - user(id2)
    - following_relation(id1, id2)
  normal_conditions:
    - user(id1) exists
    - user(id2) exists
    - id1 != id2
    - id1 does not follow id2
  derived_values: []
  state_changes:
    - user(id1) following list includes user(id2)
    - user(id2) followers list includes user(id1)
    - output_sequence contains "follow_user succeeded"
  conditional_state_changes: []
  unchanged_state:
    - all users other than id1 and id2
    - all videos
    - all received-video queues for all users
    - user(id1) basic attributes (name, age, ID)
    - user(id2) basic attributes (name, age, ID)
  return_constraints:
    - method returns void
  exceptions:
    - name: UserIdNotFoundException
      condition: user(id1) does not exist
      priority: 1
    - name: UserIdNotFoundException
      condition: user(id1) exists AND user(id2) does not exist
      priority: 2
    - name: SelfSubscriptionException
      condition: user(id1) exists AND user(id2) exists AND id1 == id2
      priority: 3
    - name: DuplicateSubscriptionException
      condition: user(id1) exists AND user(id2) exists AND id1 != id2 AND id1 already follows id2
      priority: 4
  atomicity_requirements:
    - No partial following relation may be established in any exceptional branch
    - No other business state modification may occur in any exceptional branch
    - Success must establish both directions of the relation atomically
  ordering:
    - Exception check order: id1 existence, id2 existence, self-follow, duplicate relation
  scope_constraints:
    - Only affects the following and follower relations between id1 and id2
  missing_information:
    - None
  ambiguities:
    - None
  unsupported_assumptions:
    - None
```


---

## Prior artifact: plan.md

## Method classification

- **Mutation method** — modifies following/follower relations and appends to an output sequence.
- **Not pure** — changes observable state.
- **Atomic** — success establishes both relation directions together; every exceptional branch leaves all business state unchanged.

## Applicable patterns

- **Bidirectional Relation Transaction** — both `id1`'s following list and `id2`'s followers list change together on success.
- **Exception Priority** — four validation rules with strict priority must be encoded as disjoint branches.
- **Frame Condition** — list permitted changes and require all other business state unchanged.
- **Output Sequence Update** — success appends `"follow_user succeeded"` to an output sequence.

## Normal behavior plan

- **Precondition (normal branch):** `containsUser(id1) && containsUser(id2) && id1 != id2 && !getUser(id1).isFollowing(getUser(id2))`.
- **Postconditions:**
  - `getUser(id1).isFollowing(getUser(id2))` holds.
  - `getUser(id2).containsFollower(getUser(id1))` holds.
  - Output sequence contains `"follow_user succeeded"` as the newly appended entry.
- **Atomicity:** both relation directions established together; no intermediate observable state.

## Exceptional behavior plan

Use disjoint conditions in priority order:

1. **Branch 1 — `UserIdNotFoundException`:**
   - Condition: `!containsUser(id1)`.
   - Signals: `UserIdNotFoundException`.

2. **Branch 2 — `UserIdNotFoundException`:**
   - Condition: `containsUser(id1) && !containsUser(id2)`.
   - Signals: `UserIdNotFoundException`.

3. **Branch 3 — `SelfSubscriptionException`:**
   - Condition: `containsUser(id1) && containsUser(id2) && id1 == id2`.
   - Signals: `SelfSubscriptionException`.

4. **Branch 4 — `DuplicateSubscriptionException`:**
   - Condition: `containsUser(id1) && containsUser(id2) && id1 != id2 && getUser(id1).isFollowing(getUser(id2))`.
   - Signals: `DuplicateSubscriptionException`.

- **Atomicity for all exceptional branches:** no relation change, no output sequence update, no change to any user, video, queue, or attribute.

## State-change plan

- **On success:**
  - Add `id2` to `id1`'s following set.
  - Add `id1` to `id2`'s followers set.
  - Append `"follow_user succeeded"` to the output sequence.
- **On any exception:** no state changes whatsoever.

## Frame-condition plan

- **Permitted changes (success only):**
  - The following relationship of `user(id1)`.
  - The followers relationship of `user(id2)`.
  - The output sequence.
- **Forbidden changes (always, including success):**
  - All other users’ following and followers sets.
  - All users’ basic attributes (name, age, ID).
  - All videos.
  - All received-video queues for all users.
- **For exceptional branches:** `assignable \nothing` equivalent — no observable business state changes.

## Old-state requirements

- **`\old` needed for:**
  - Verifying no existing following relation before success: `!\old(getUser(id1).isFollowing(getUser(id2)))`.
  - Verifying the output sequence length increased by exactly one and the new last element is `"follow_user succeeded"`.
  - Verifying all users, videos, queues, and attributes except the two relations are unchanged — use `\old` to compare sizes or collection contents where required.

## Helper predicates

- `containsUser(int id)` — `AVAILABLE_INTERFACE` (official method).
- `getUser(int id)` — `AVAILABLE_INTERFACE` (official method).
- `User.isFollowing(User other)` — `AVAILABLE_INTERFACE` (official method).
- `User.containsFollower(User other)` — `AVAILABLE_INTERFACE` (official method).
- `output_sequence` — `AVAILABLE_INTERFACE` (official output stream concept; must be grounded to provided interface).
- **No ABSTRACT_HELPER introduced** — all required semantic concepts are representable with supplied interface symbols.

## Quantification / collection reasoning

- **Following set size:** on success, `\num_of` over following set of `id1` increases by exactly 1.
- **Follower set size:** on success, `\num_of` over followers set of `id2` increases by exactly 1.
- **No double counting:** each relation is a single directed edge; `isFollowing` and `containsFollower` are inverse representations of the same edge.
- **Unchanged quantification:** for every other user `u` (with `u.id != id1 && u.id != id2`), the count of following and followers remains `\old`-equal.

## Potential specification pitfalls

1. **Overlap between exception branches** — must write branches as fully disjoint conditions, not rely on Java evaluation order.
2. **Output sequence frame** — must explicitly state that no output is appended on exceptions.
3. **Nested object mutation** — ensure that modifying `user(id1)` and `user(id2)` does not implicitly modify unrelated users via shared references.
4. **`assignable users[*]` too broad** — in final JML, prefer a more precise frame, e.g., only the two user objects and the output sequence, or use a helper to express that only those relation fields change.
5. **Atomicity of the two-direction update** — the specification must not allow a state where only one direction is visible between steps.
6. **`getUser` use in exceptional branches** — must not call `getUser(id2)` when `id2` does not exist; guard with `containsUser` before dereferencing.

## Missing interface information

- **None identified.** All necessary symbols (`containsUser`, `getUser`, `User.isFollowing`, `User.containsFollower`, output mechanism) are available from the official interface grounding.
- If the exact output sequence method name or type is not declared, mark the output postcondition with a note: `ABSTRACT_HELPER` for the output stream only if not specified in the official interface.


---

## Your response

Return only the output required by the stage instructions.
