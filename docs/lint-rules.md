# Oxlint and Oxfmt Configuration

This document defines how static-analysis and formatting tools implement the
**TypeScript Best Practices** baseline. It does not define competing
language, type-safety, naming, module, runtime-boundary, or API-documentation policy.

## Ownership

| Owner | Responsibility |
| --- | --- |
| TypeScript | Authoritative type and module correctness |
| Oxlint | Semantic static analysis |
| Oxfmt | Formatting |

The tools enforce the baseline; they never redefine it. Do not configure Oxlint rules
that compete with Oxfmt over formatting. Do not treat Oxlint as a replacement for the
TypeScript compiler's type and module checks.

### Replacement invariant

Never disable a base JavaScript rule unless its TypeScript-aware replacement is enabled
in the exact same file scope, and never lower a rule's severity in place of a
replacement. This is not a relaxation: the replacement rule uses type information and
covers cases the base rule cannot classify.

## Oxlint

- Configure Oxlint through the project's Oxlint configuration.
- Enable type-aware linting so rules that need type information receive it.
- Translate the canonical TypeScript and framework policies into semantic rules.
- Keep file scopes, runtime globals, ignored paths, generated-code exclusions, and
  project-specific exceptions in configuration rather than duplicating policy here.
- Prefer native Oxlint rules before JavaScript-plugin equivalents, and do not claim
  plugin parity that is not actually configured.
- Report stale suppression directives and unused inline configuration.

The canonical suppression and runtime-boundary requirements remain in **TypeScript Best
Practices**. React-specific behavior remains in **React Component Rules**.

### Type checking and type-aware linting

- Set `options.typeAware` in the root Oxlint configuration so type-aware rules resolve
  type information.
- Keep `tsc --noEmit` as the authoritative type-checking release gate for type and module
  correctness.
- Treat Oxlint's full `typeCheck` mode as optional while it remains experimental.
  Type-aware linting does not replace the compiler.

### Rule namespaces

Use explicit plugin namespaces in configuration — `eslint/*`, `typescript/*`, `node/*`,
`react/*`, and `vitest/*`. Additional plugins may be added, but do not abbreviate or
omit the namespace of a configured rule.

### Import rules

- Use one import declaration per module, combining value and type imports from the same
  source: `import {createUser, type User} from './user.ts';`.
- Use inline type specifiers; do not emit a separate `import type {User} from ...` for a
  source already imported for values.
- Align `typescript/consistent-type-imports`, `typescript/consistent-type-specifier-style`,
  and the project's duplicate-import rule (`import/no-duplicates`) so their diagnostics
  and fixes agree on that single syntax instead of contradicting each other.

### Required rule configuration

Keep these policies in Oxlint configuration rather than restating them here:

- `typescript/ban-ts-comment`: reject `@ts-ignore`, and require a description on
  `@ts-expect-error` (`allow-with-description`, with `minimumDescriptionLength` and an
  optional `descriptionFormat`). Relax the description requirement for type-test files with
  an `overrides` entry.
- `typescript/no-explicit-any`: leave `ignoreRestArgs` disabled so rest and callback
  signatures are checked like any other type, and exclude generated declaration files
  (`ignorePatterns` or `overrides`) instead of disabling the rule.
- `typescript/no-unsafe-assignment`, `no-unsafe-call`, `no-unsafe-member-access`,
  `no-unsafe-argument`, and `no-unsafe-return`: enable them with type-aware linting
  (`options.typeAware`).
- `typescript/return-await`: set to `error-handling-correctness-only`, so `await` is required
  where omitting it would change `try`/`catch`/`finally` behavior while direct Promise
  returns stay permitted. Requires type-aware linting (`options.typeAware`).
- `typescript/require-await`: use the TypeScript-aware rule instead of also enabling the base
  `require-await`, which would duplicate or contradict its diagnostics.
- `node/no-process-env`: enable it for application code, and disable it only through a
  scoped `overrides` entry for the designated environment adapters, build scripts, and
  test harnesses that require direct access. Application code imports validated config
  instead of reading the environment source. The adapter and its validation are defined
  in the **TypeScript Best Practices** environment boundary.
- `eslint/no-throw-literal` is deprecated for TypeScript files: disable it and enable
  `typescript/only-throw-error` in the same scope so thrown values are checked by type.
- Disable any base JavaScript rule for TypeScript files once its TypeScript-aware
  replacement is enabled, per the replacement invariant.

### Scoping

Scope every rule family to the files where it is semantically valid:

| Rule scope | Applies to |
| --- | --- |
| TypeScript | TypeScript files (`.ts`, `.tsx`, and other configured extensions) |
| React | React-owned frontend files, including `.ts` hooks, not only `.tsx` |
| Vitest | Unit-test, setup, and Vitest configuration files |
| Browser | Browser-owned application code |
| Node | Node packages, scripts, server code, and configuration |
| Playwright | E2E files and `playwright.config.*` |

- Disable `node/no-process-env` only in the scoped environment adapters, build scripts, and
  test harnesses that require direct access.
- Document whether Playwright coverage comes from Oxlint's JavaScript-plugin bridge, an
  accepted coverage reduction, or a narrow fallback linter; never imply full plugin parity.
- Exclude generated, vendored, and unsupported files rather than linting them with weakened
  rules.

### Ignores and overrides

- Every override must target files that are not excluded by an ignore pattern.
- Remove overrides that match no live files, or narrow the conflicting ignore pattern so the
  override becomes effective.
- Keep generated, vendored, and unsupported files in ignore patterns instead of weakening
  rules for them.

## Oxfmt

- Configure Oxfmt as the sole formatting owner for supported authored files.
- Keep indentation, semicolons, quotes, spacing, wrapping, and trailing-comma choices
  in Oxfmt configuration.
- Exclude generated, vendored, and unsupported files instead of adding competing
  formatter rules to Oxlint.
- Remove a formatting constraint from Oxlint only once Oxfmt demonstrably enforces it for
  the same files.

## Project overrides

Project configuration may differ from the baseline. Keep each difference explicit and
scoped, and document the effective replacement policy and reason in the project rules.

No project override may lower coverage, lower a rule's severity, or disable a rule
without an enabled replacement in the same scope.
