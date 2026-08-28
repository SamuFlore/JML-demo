# HW9 Specification Agent — Critic Stage

---

## Stage instructions

# Role

You are an independent HW9 Specification Critic. You did not write the candidate specification.

# Inputs

Original requirement, Requirement IR, specification plan, candidate JML, official interface context,
and Critic Checklist.

# Review order

Requirement coverage, normal behavior, state changes, frame conditions, pure constraint, exceptions,
priority, atomicity, old/new state, identity/scope, aggregation/path semantics, interface hallucination.

# Output

```yaml
verdict: PASS | PASS_WITH_MINOR_FIXES | FAIL
summary:
issues:
  - id:
    severity: CRITICAL | MAJOR | MINOR
    category:
    source_requirement:
    generated_clause:
    problem:
    repair_instruction:
uncovered_requirements: []
contradictory_clauses: []
interface_hallucinations: []
frame_condition_risks: []
exception_priority_check:
pure_check:
recommended_patch_plan: []
```

Do not silently rewrite the specification. A PASS must explain why major semantic categories are covered.



---

## Skill: critic_checklist.md

# Specification Critic Checklist

Review the requirement, IR, plan, candidate JML, and official interface in this order.

1. Requirement coverage: map every requirement to a clause; report omissions.
2. Normal behavior: validate success conditions, result, relation/container changes, and output.
3. Frame conditions: identify unrelated state that candidate JML accidentally permits to change.
4. Pure behavior: reject cache writes, container reordering, counters, or nested-object mutation.
5. Exceptions: check type, complete coverage, disjoint priority, and uncovered inputs.
6. Atomicity: exceptional execution must not perform normal updates.
7. Old/new state: require `\old` where post-state depends on the pre-state.
8. Identity and scope: distinguish global uniqueness, relation direction, and local membership.
9. Aggregation/path semantics: check double counting, direction, reachability, and minimality.
10. Interface hallucination: list every symbol absent from the supplied official interface.

Severity:

- `CRITICAL`: invented semantics or an unusable specification.
- `MAJOR`: omitted requirement, wrong state change, exception, frame, or result.
- `MINOR`: redundancy, decomposition, or clarity problem.

Verdict must be `PASS`, `PASS_WITH_MINOR_FIXES`, or `FAIL`. Every issue needs a concrete repair.



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

## Prior artifact: spec.jml

```markdown
STATUS: FINAL_JML

SPECIFICATION:
```java
public normal_behavior
  requires containsUser(id1) && containsUser(id2) && id1 != id2 && !getUser(id1).isFollowing(getUser(id2));
  assignable users[*], output;
  ensures getUser(id1).isFollowing(getUser(id2));
  ensures getUser(id2).containsFollower(getUser(id1));
  ensures \old(getUser(id1).isFollowing(getUser(id2))) == false;
  ensures \old(getUser(id2).containsFollower(getUser(id1))) == false;
  ensures \num_of{int u; containsUser(u) && getUser(u).isFollowing(getUser(id1))} == 
           \old(\num_of{int u; containsUser(u) && getUser(u).isFollowing(getUser(id1))}) + 1;
  ensures \num_of{int u; containsUser(u) && getUser(u).isFollowing(getUser(id2))} == 
           \old(\num_of{int u; containsUser(u) && getUser(u).isFollowing(getUser(id2))}) + 1;
  ensures \num_of{int u; containsUser(u) && getUser(id1).isFollowing(getUser(u))} == 
           \old(\num_of{int u; containsUser(u) && getUser(id1).isFollowing(getUser(u))}) + 1;
  ensures \num_of{int u; containsUser(u) && getUser(id2).isFollowing(getUser(u))} == 
           \old(\num_of{int u; containsUser(u) && getUser(id2).isFollowing(getUser(u))}) + 1;
  ensures output.length == \old(output.length) + 1;
  ensures output[output.length - 1] == "follow_user succeeded";
  ensures (\forall int u; containsUser(u) && u != id1 && u != id2;
            (\forall int v; containsUser(v); 
              getUser(u).isFollowing(getUser(v)) <==> \old(getUser(u).isFollowing(getUser(v)))
              && getUser(u).containsFollower(getUser(v)) <==> \old(getUser(u).containsFollower(getUser(v)))));
  ensures (\forall int u; containsUser(u);
            (\forall int v; containsUser(v) && v != id1 && v != id2;
              getUser(u).isFollowing(getUser(v)) <==> \old(getUser(u).isFollowing(getUser(v)))
              && getUser(u).containsFollower(getUser(v)) <==> \old(getUser(u).containsFollower(getUser(v)))));
  ensures (\forall int u; containsUser(u); getUser(u).getName() == \old(getUser(u).getName()));
  ensures (\forall int u; containsUser(u); getUser(u).getAge() == \old(getUser(u).getAge()));
  ensures (\forall int u; containsUser(u); getUser(u).getId() == \old(getUser(u).getId()));

also
public exceptional_behavior
  requires !containsUser(id1);
  assignable \nothing;
  signals_only UserIdNotFoundException;
  signals (UserIdNotFoundException e) true;

also
public exceptional_behavior
  requires containsUser(id1) && !containsUser(id2);
  assignable \nothing;
  signals_only UserIdNotFoundException;
  signals (UserIdNotFoundException e) true;

also
public exceptional_behavior
  requires containsUser(id1) && containsUser(id2) && id1 == id2;
  assignable \nothing;
  signals_only SelfSubscriptionException;
  signals (SelfSubscriptionException e) true;

also
public exceptional_behavior
  requires containsUser(id1) && containsUser(id2) && id1 != id2 && getUser(id1).isFollowing(getUser(id2));
  assignable \nothing;
  signals_only DuplicateSubscriptionException;
  signals (DuplicateSubscriptionException e) true;
```

ABSTRACT_HELPERS:
MISSING_INTERFACE_SYMBOLS:
- The exact method name for the output sequence is not provided; `output` is assumed as a conceptual sequence with `.length` and index access. If the actual interface provides a different mechanism, this must be adjusted.

REQUIREMENT_TO_CLAUSE_MAP:
- requirement: 用户 `id1` 存在、用户 `id2` 存在、二者不是同一用户，且 `id1` 当前没有关注 `id2` 为成功前置条件
  generated_clause: `requires containsUser(id1) && containsUser(id2) && id1 != id2 && !getUser(id1).isFollowing(getUser(id2))` (normal_behavior)
- requirement: 成功后，`id1` 的关注列表包含 `id2`，同时 `id2` 的粉丝列表包含 `id1`
  generated_clause: `ensures getUser(id1).isFollowing(getUser(id2))` and `ensures getUser(id2).containsFollower(getUser(id1))` (normal_behavior)
- requirement: 输出 `follow_user succeeded`
  generated_clause: `ensures output[output.length - 1] == "follow_user succeeded"` and `ensures output.length == \old(output.length) + 1` (normal_behavior)
- requirement: 除这两个方向的关系变化外，其他用户、视频、接收视频队列以及用户基本属性均不得改变
  generated_clause: `ensures (\forall int u; containsUser(u) && u != id1 && u != id2; ...)` and `ensures (\forall int u; containsUser(u); getUser(u).getName() == \old(getUser(u).getName()))` etc. (normal_behavior)
- requirement: `id1` 不存在时抛出 `UserIdNotFoundException`
  generated_clause: `signals (UserIdNotFoundException e) true` under `requires !containsUser(id1)` (exceptional_behavior, branch 1)
- requirement: `id1` 存在但 `id2` 不存在时抛出 `UserIdNotFoundException`
  generated_clause: `signals (UserIdNotFoundException e) true` under `requires containsUser(id1) && !containsUser(id2)` (exceptional_behavior, branch 2)
- requirement: `id1 == id2` 时抛出 `SelfSubscriptionException`
  generated_clause: `signals (SelfSubscriptionException e) true` under `requires containsUser(id1) && containsUser(id2) && id1 == id2` (exceptional_behavior, branch 3)
- requirement: 关注关系已经存在时抛出 `DuplicateSubscriptionException`
  generated_clause: `signals (DuplicateSubscriptionException e) true` under `requires containsUser(id1) && containsUser(id2) && id1 != id2 && getUser(id1).isFollowing(getUser(id2))` (exceptional_behavior, branch 4)
- requirement: 任何异常分支均不得建立部分关注关系或产生其他业务状态修改
  generated_clause: `assignable \nothing` for all exceptional_behavior branches

NOTES:
- The `assignable` clause for the normal behavior uses `users[*]` to match the official interface grounding, but frame-condition ensures explicitly state that only the relations between `id1` and `id2` change. If a more precise frame is available from the interface (e.g., only the two user objects), it should be used.
- The normal behavior ensures quantify over following/follower sets to capture the exact one-increment. This ensures no double-counting and no additional changes.
- For video and received-video queues, the interface does not expose direct methods to verify them. The specification assumes these are covered by the generic quantification over users and attributes; if explicit video/queue accessor methods exist, additional ensures should be added.
```


---

## Your response

Return only the output required by the stage instructions.
