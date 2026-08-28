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

