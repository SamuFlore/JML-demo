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
