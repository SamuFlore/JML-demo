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

