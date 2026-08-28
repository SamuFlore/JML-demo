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

