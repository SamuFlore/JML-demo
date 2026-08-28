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

