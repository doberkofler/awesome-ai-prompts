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

Do not configure Oxlint rules that compete with Oxfmt over formatting. Do not treat
Oxlint as a replacement for the TypeScript compiler's type and module checks.

## Oxlint

- Configure Oxlint through the project's Oxlint configuration.
- Translate the canonical TypeScript and framework policies into semantic rules.
- Keep file scopes, runtime globals, ignored paths, generated-code exclusions, and
  project-specific exceptions in configuration rather than duplicating policy here.
- Report stale suppression directives and unused inline configuration.

The canonical suppression and runtime-boundary requirements remain in **TypeScript Best
Practices**. React-specific behavior remains in **React Component Rules**.

## Oxfmt

- Configure Oxfmt as the sole formatting owner for supported authored files.
- Keep indentation, semicolons, quotes, spacing, wrapping, and trailing-comma choices
  in Oxfmt configuration.
- Exclude generated, vendored, and unsupported files instead of adding competing
  formatter rules to Oxlint.

## Project overrides

Project configuration may differ from the baseline. Keep each difference explicit and
scoped, and document the effective replacement policy and reason in the project rules.
