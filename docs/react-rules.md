# React Component Rules

Generic, framework-agnostic React component-design rules.

General TypeScript concerns (naming, exports, `readonly`, type imports) are defined in
the **TypeScript Best Practices** baseline; this section does not restate them.

## Component Design

- One component = one responsibility; split when a second concern appears.
- Keep components under ~100 lines (advisory guideline, not enforced; concrete
  limits are project-specific).
- Extract when a component has >~8 props, 2+ distinct concerns, deep JSX
  nesting, multiple state/effect clusters, or repeated markup.
- Extraction order: subcomponent → custom hook → pure helper.
- One primary component per file; follow the baseline file-naming policy.
- Type props explicitly with a named `Props` type and follow the baseline immutability
  policy.

## Hooks

- Custom hooks use `useX` naming, own one concern each, return a typed value,
  and contain no JSX.
- Separate data-fetching from presentational concerns where it aids testability
  (prefer a custom hook over a container component wrapper).
- Extract logic into hooks or pure functions for unit testability; test
  behavior, not implementation.

## State and Effects

- Derive state during render; never mirror props or other state.
- `useState` for simple local state; `useReducer` for ≥3 related transitions.
- Server state via a query library (for example TanStack Query), not manual
  `useEffect` + `useState`.
- Effects are for external synchronization only, never for derived data; always
  return a cleanup function.
- Prefer idiomatic fixes over suppressions: derive state during render, remount
  via a `key`, give effects explicit ownership.

## Lists

- Use stable identity keys; never use the array index for reorderable lists.

## Anti-Patterns

Reject in review:

- God components and prop explosion.
- State kept in sync with an effect.
- Inline `style` props.
- Array-index keys.
- Suppressing a rule instead of fixing the underlying pattern.
