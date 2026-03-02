# ESLint Configuration Overview

This document describes the ESLint setup, rule philosophy, and directory-specific behavior.

---

## 1. Base Configuration

### Ignored Paths

The following are excluded from linting:

- All dotfiles (`**/.*`)
- `dist/**`
- `temp/**`
- `node_modules/**`

### Linter Options

- `reportUnusedDisableDirectives`: `warn`
- `reportUnusedInlineConfigs`: `warn`

Ensures stale `eslint-disable` and inline overrides are surfaced.

---

## 2. Extended Presets

The configuration builds on:

- `@eslint/js` (recommended)
- `typescript-eslint`  
	- `strictTypeChecked`
	- `stylisticTypeChecked`
- `eslint-plugin-unicorn` (recommended)
- `eslint-plugin-regexp` (`flat/recommended`)
- `eslint-plugin-react` (`flat/all`)
- `eslint-plugin-react-hooks`
- `eslint-plugin-jsdoc` (TypeScript presets)
- `@vitest/eslint-plugin` (recommended in unit tests)
- `eslint-plugin-playwright` (recommended in e2e tests)
- `eslint-plugin-import-x`

Type-aware linting is enabled via `parserOptions.project`.

---

## 3. JavaScript Rules

### Safety and Correctness

Strict enforcement:

- `eqeqeq`
- `no-eval`
- `no-implied-eval`
- `no-new-func`
- `no-throw-literal`
- `no-shadow`
- `no-with`
- `constructor-super`
- `no-extend-native`
- `no-process-env`
- `no-var`
- `radix`
- `yoda: never`

Prevents unsafe, ambiguous, or legacy patterns.

### Control Flow & Complexity

Warn-only thresholds:

- `complexity: 30`
- `max-depth: 10`
- `max-lines: 1300`
- `max-params: 10`
- `max-statements: 150`
- `max-nested-callbacks: 10`

Designed to surface architectural issues without blocking.

### Style Decisions

- `curly: all`
- `unicode-bom: never`
- `vars-on-top`
- `dot-notation` (with snake_case allowance)
- `prefer-const: warn`
- `no-implicit-coercion` (except `!!`)

Several stylistic rules intentionally disabled:
- `prefer-template`
- `prefer-spread`
- `object-shorthand`
- `sort-imports`
- `no-plusplus`
- `no-magic-numbers`

Formatting is assumed to be handled by Prettier.

---

## 4. TypeScript Rules

Type-aware linting enabled globally.

### Strictness

Errors on:

- `no-explicit-any` (rest args allowed)
- `no-floating-promises`
- `no-misused-promises`
- `no-array-delete`
- `no-dynamic-delete`
- `no-duplicate-type-constituents`
- `no-unnecessary-type-assertion`
- `no-unnecessary-type-constraint`
- `no-wrapper-object-types`
- `only-throw-error`
- `require-await`
- `unbound-method`
- `explicit-module-boundary-types`
- `explicit-member-accessibility`

Encourages explicit, safe type modeling.

### Imports & Types

- `consistent-type-imports`
- `consistent-type-exports`
- `no-require-imports`
- `import-x/no-commonjs`
- `import-x/no-duplicates`

ESM-only, no CommonJS.

### `@ts-expect-error` Policy

Enforced format:

```ts
// @ts-expect-error ts(1234) FIXME: explanation
```
