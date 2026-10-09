# TypeScript Best Practices

You are an expert TypeScript developer who writes clean, maintainable code that is not going to be regretted later and follows strict linting rules.

> **Core priority**: Type safety and code quality are non-negotiable. Every shortcut taken here compounds into maintenance debt. When in doubt, be stricter.

**Keep in Mind**: The code will be parsed using TypeScript compiler with strict type checking enabled and should adhere to modern ECMAScript standards.

## Scope and precedence

This document is the canonical TypeScript baseline for language use, type safety,
runtime boundaries, modules, naming, and API documentation.

- Use the **Oxlint and Oxfmt Configuration** section to implement this policy; that
  section does not redefine it.
- Use the **React Component Rules** section only for React-specific design.
- A project may override this baseline only through a local rule that states the
  affected scope, effective replacement policy, and reason.
- Apply the baseline wherever a project has no explicit override.
- Treat the examples here as guidance. This repository distributes rules; it does not
  compile, lint, or test them. A consuming project owns its toolchain, dependency
  versions, lockfile, and tests, so no example is claimed to be locally verified.

## Formatting and naming

- Let Oxfmt enforce tabs, semicolons, single quotes, spacing, and wrapping.
- Never omit curly braces around blocks, even when they are optional

### Naming Conventions
- **Variables/Functions**: `camelCase`
- **Non-component modules**: `camelCase` (e.g., `user.ts`, `supplierInvoice.ts`).
- **Hooks**: `camelCase` with a `use` prefix (`useUser.ts`).
- **Named React component modules**: `PascalCase.tsx` (e.g., `UserCard.tsx`).
- **Module entrypoints**: `index.ts` and `index.tsx` are exempt from the module-name
  convention.
- **Tests and stories**: mirror the production filename before the suffix
  (`UserCard.test.tsx`, `UserCard.stories.tsx`, `useUser.test.ts`). Generated and
  framework-mandated filenames are exempt.
- **Constants**: `UPPER_CASE` for global constants

## JavaScript
- Use ES modules only.
- Choose `target`, `module`, `moduleResolution`, and emit behavior from one compatible
  compiler profile (see **Compiler profiles**).

## Type Safety & Configuration

> Type safety is a top priority. Never weaken it for convenience.

- Set the universal strictness baseline in `tsconfig.json`:

```json
{
	"strict": true,
	"noUnusedLocals": true,
	"noUnusedParameters": true,
	"noImplicitReturns": true,
	"noFallthroughCasesInSwitch": true,
	"noUncheckedIndexedAccess": true,
	"noImplicitOverride": true,
	"noPropertyAccessFromIndexSignature": true,
	"exactOptionalPropertyTypes": true,
	"allowUnreachableCode": false,
	"allowUnusedLabels": false,
	"forceConsistentCasingInFileNames": true
}
```

- `strict` already enables `noImplicitAny`, `strictNullChecks`, `strictFunctionTypes`,
  `strictBindCallApply`, `strictPropertyInitialization`, `noImplicitThis`,
  `useUnknownInCatchVariables`, and `alwaysStrict`; do not repeat them unless a scoped
  override changes one.
- Enable `noUncheckedIndexedAccess` in the baseline; a project may disable it explicitly
  only with a scoped statement of the effective setting and reason.
- Use `noPropertyAccessFromIndexSignature: true` rather than advertising `false` as a
  strict default.
- Keep `target`, `module`, `moduleResolution`, and emit options in a compiler profile
  below, not in the universal baseline.

### Why the baseline relies on `strict`

`strict` is not one check; it enables the entire strict-mode family (`noImplicitAny`,
`strictNullChecks`, `strictFunctionTypes`, `strictBindCallApply`,
`strictPropertyInitialization`, `noImplicitThis`, `useUnknownInCatchVariables`,
`alwaysStrict`, and later additions such as `strictBuiltinIteratorReturn`). Repeating
those flags next to `strict` is redundant and misleading: the list cannot stay
exhaustive.

Relying on `strict` is also the safer long-term choice. TypeScript may add stricter
checks to the `strict` family in a release, so an upgrade can surface errors that were
previously unchecked. That is the intended signal. The baseline inherits the new check
instead of silently keeping the weaker behavior because a hand-maintained list omitted it.

- Pin the TypeScript version, and treat new `strict`-family errors after an upgrade as
  real findings, not as a reason to weaken the configuration.
- If one specific check must be relaxed, disable that named flag explicitly and record the
  scope and reason, as required for any override; never replace the baseline with a
  hand-maintained list of enabled checks.
- The options that are not part of `strict` stay explicit because the baseline needs them
  regardless: `noUnusedLocals`, `noUnusedParameters`, `noImplicitReturns`,
  `noFallthroughCasesInSwitch`, `noUncheckedIndexedAccess`, `noImplicitOverride`,
  `noPropertyAccessFromIndexSignature`, `exactOptionalPropertyTypes`,
  `allowUnreachableCode`, `allowUnusedLabels`, and `forceConsistentCasingInFileNames`.

### Semantic safety

Enforce these language constraints through Oxlint. Each closes a failure mode that the
type checker alone does not:

- **Coercion safety**: use strict equality and an explicit radix; reject implicit
  coercion except explicit boolean coercion with `!!`.
- **Control-flow safety**: use `const` by default and never `var`; reject variable
  shadowing and invalid derived-class construction.
- **Code-execution security**: reject `eval`, implied evaluation, `new Function`, `with`,
  and native-object extension.
- **Promise handling**: reject floating and misused promises.
- **`any` containment**: reject unsafe `any` operations and unnecessary assertions and
  constraints.
- **Error contracts**: throw `Error` objects rather than literals and reject invalid
  thrown values.
- **Import emission**: require one declaration per module with inline type specifiers.
- **Module and configuration boundaries**: require explicit module-boundary types and
  explicit member accessibility, and keep direct environment access inside the project's
  runtime boundary.
- Reject array deletion, dynamic property deletion, duplicate union constituents, wrapper
  object types, and unbound methods.

Readability and architecture rules are guidance, not correctness rules, and stay separate
so each can be weighed rather than treated as a defect:

- Treat complexity limits as advisory signals, not correctness failures. Default warning
  thresholds are complexity 30, nesting depth 10, 1,300 lines, 10 parameters, 150
  statements, and 10 nested callbacks. Projects may override these thresholds explicitly.
- Prefer conventional over Yoda conditions, declare variables near their first use, and
  use property dot notation except for snake-case keys. Report `prefer-const` as a warning.
- Keep import grouping and ordering; it makes large import blocks navigable at review time.
- Do not require template literals, object shorthand, spread syntax, or bans on increments
  and numeric literals.

### Suppressions

Suppressions hide a real defect from the compiler. Treat every one as temporary debt, and
use exactly one form in production code:

```typescript
// @ts-expect-error TS2345 -- NOTE: why it is unavoidable; what removes it.
```

- **Ban `@ts-ignore`.** It silences every error on the next line, including errors that
  appear after the original cause is fixed. `typescript/ban-ts-comment` rejects it.
- **`@ts-expect-error` in type tests is the single exception.** There the annotation is the
  assertion, so a bare `// @ts-expect-error` needs no description and no approval.
- **`@ts-expect-error` in production code requires explicit, granted permission** before it
  is added.
- The **diagnostic code is documentary, not compiler-enforced.** TypeScript never checks that
  `TS2345` is the code that would have fired, and the directive silences whatever error does
  occur. Keep the code accurate by hand and delete the directive as soon as the error is gone.
- The text after `-- NOTE: ` is **mandatory** and must state why the suppression is
  unavoidable and, when temporary, the condition that removes it.

Never relax any other lint or TypeScript rule (disabling a rule inline, weakening a `tsconfig`
flag, casting to `any`) without:
1. Demonstrating it is strictly necessary — not merely convenient.
2. Explicit permission requested and granted before proceeding.
3. A `NOTE: ` comment at the site stating the justification and what removes it.

## Compiler profiles

Runtime, module, and emit settings belong to a profile, not the universal baseline. Use
exactly one profile per project or package, and keep inherited options internally
compatible.

### Bundler-owned application

Use when a bundler owns JavaScript output:

```json
{
	"compilerOptions": {
		"target": "ES2022",
		"module": "Preserve",
		"moduleResolution": "Bundler",
		"noEmit": true,
		"verbatimModuleSyntax": true
	}
}
```

- Add `allowImportingTsExtensions: true` only when the bundler accepts TypeScript
  extensions.
- `Preserve` reflects what most modern bundlers and Bun accept. A project that uses
  `ESNext` instead must record that scoped replacement and its reason.

### Node-compatible ESM

Use `"type": "module"` in `package.json` or `.mts` files, with:

```json
{
	"compilerOptions": {
		"target": "ES2022",
		"module": "NodeNext",
		"moduleResolution": "NodeNext",
		"verbatimModuleSyntax": true
	}
}
```

- Write runtime JavaScript extensions in TypeScript source:
  `import {helper} from './helper.js';`.
- When `tsc` emits the JavaScript, also set `noEmitOnError: true` and an output
  directory.
- When another build tool owns output, set `noEmit: true`; do not add
  `allowImportingTsExtensions` merely to replace runtime `.js` specifiers with `.ts`.

### Direct Node TypeScript execution

For Node's built-in type stripping:

```json
{
	"compilerOptions": {
		"target": "ESNext",
		"module": "NodeNext",
		"moduleResolution": "NodeNext",
		"noEmit": true,
		"allowImportingTsExtensions": true,
		"erasableSyntaxOnly": true,
		"verbatimModuleSyntax": true
	}
}
```

- Use explicit TypeScript extensions in relative specifiers.
- Node recommends TypeScript 5.8 or newer, ignores `tsconfig.json` while executing, does
  not support `.tsx`, and accepts only erasable syntax: enums, runtime namespaces,
  parameter properties, and import aliases fail.

### TypeScript extension rewriting

TypeScript 5.7 or newer can rewrite supported relative TypeScript extensions:

```json
{
	"compilerOptions": {
		"target": "ES2022",
		"module": "NodeNext",
		"moduleResolution": "NodeNext",
		"rewriteRelativeImportExtensions": true,
		"verbatimModuleSyntax": true,
		"noEmitOnError": true,
		"outDir": "dist"
	}
}
```

- Rewriting applies only to supported literal relative paths ending in `.ts`, `.tsx`,
  `.mts`, or `.cts`.
- It does not rewrite package imports, path aliases, package import/export mappings,
  extensionless paths, or computed dynamic-import paths.

### Shared source consumed by bundlers and Node

When the same source is consumed by a bundler and by Node-compatible ESM, use JavaScript
extensions in relative specifiers:

```typescript
export {schema} from './schema.js';
```

Bundlers accept this syntax, while Node-compatible ESM requires the runtime extension.
Validate shared source with the strictest consumer resolution rather than Bundler
resolution alone.

### Published libraries

Validate a published library with a consumer-compatible module profile rather than
Bundler resolution alone. Target the oldest supported runtime, emit declaration files,
and verify those declarations from representative consumer configurations.

## Documentation

- Document public APIs and non-obvious contracts; do not document every export merely
  because it is exported.
- Cover the applicable invariants, side effects, return semantics, and thrown errors.
- Use TypeDoc-compatible documentation comments (`/** ... */`). Do not repeat
  TypeScript types in `@param`/`@returns` tags — TypeDoc derives them from the
  signature.
- Prefer `@returns` over `@return` for consistency with TypeDoc's canonical tag.

```typescript
/**
 * Loads a user from persistent storage.
 *
 * @param userId - Identifier of the requested user.
 * @returns The matching user.
 * @throws {@link UserNotFoundError} When no user exists for the identifier.
 */
export const loadUser = (userId: UserId): Promise<User> => { /* ... */ };
```

## Type Definitions

> Code quality and type safety are the top priorities. Every type hole is a potential runtime crash.

- **Never** use `any`. If tempted, use `unknown` and narrow explicitly.
- Enforce this with `typescript/no-explicit-any` for authored code, with no rest-argument
  exemption. Prefer concrete tuples, constrained generics, or `unknown[]` over `any[]` in
  rest and callback signatures; an unavoidable interoperability case is a localized,
  justified suppression, never a blanket rule exemption.
- Exclude generated declaration files from linting instead of weakening the `any` policy for
  the whole project.
- Retain the type-aware `typescript/no-unsafe-*` rules (assignment, call, member access,
  argument, return) so inferred and dependency-sourced `any` values are caught even where no
  explicit `any` appears.
- **Never** use type assertions (`as`) on external data — use Zod (see below).
- Explicitly type function parameters.
- Require explicit return types at public API, recursive, and overload boundaries;
  otherwise allow TypeScript inference.
- No enums. Use union types.
- Use `readonly` modifiers for immutable properties and arrays.
- Use `private` modifiers for private class members.
- Leverage utility types (`Partial`, `Required`, `Pick`, `Omit`, `Record`, etc.).
- Use discriminated unions with exhaustiveness checking for type narrowing.
- Handle `null` and `undefined` explicitly — never assume.
- Prefer `type` over `interface`.

## Advanced Patterns

- Implement generics with appropriate constraints — avoid unconstrained `T` where a bound is possible.
- Use mapped types and conditional types to reduce type duplication.
- Use `const` assertions for literal types.
- Implement branded/nominal types for type-level validation where domain correctness matters (e.g., `UserId`, `EmailAddress`).

## Code Organization

- Colocate types with the implementation they describe by default.
- Create a shared type module (`types.ts` or `src/types/`) only for concepts genuinely
  shared across multiple modules.

## Best Practices

- Use `??` and `?.` where appropriate — never use `||` as a null-coalescing substitute (it conflates `null`/`undefined` with falsy).
- Prefix only intentionally unused parameters with `_` (e.g., `_unusedParam`); remove unused
  local variables so `noUnusedLocals` fails the build instead of hiding them.
- `const` for everything that isn't reassigned, `let` otherwise. Never `var`.
- Return the Promise directly. Use `return await` only when it changes `try`/`catch`/`finally` behavior.
- Always use curly braces for control flow, even single-line.
- Prefer object spread (`{...args}`) over `Object.assign`.
- Use rest parameters instead of `arguments`.
- Use template literals instead of string concatenation.
- Prefer `structuredClone` over manual deep-copy patterns.
- Use `satisfies` operator to validate shapes without widening the inferred type.

## Import Organization

- Imports at top of file.
- Group order: `built-in → external → internal → parent → sibling → index → object → type`
- Blank line between groups.
- Alphabetical sort within groups.
- No duplicate or circular imports.
- Import types inline: `import {type MyType} from '...'` — not `import type {MyType}`.
- Named exports/imports only. No default exports.
- Choose relative import specifiers from the project's compiler and runtime profile; there
  is no universal extension valid for every TypeScript project.

### Relative import extensions

Select relative import specifiers from the profile that owns resolution:

| Profile | Source specifier |
| --- | --- |
| Bundler-owned application | Follow the bundler; extensionless imports are permitted |
| Node-compatible ESM | Use the runtime `.js`, `.mjs`, or `.cjs` extension |
| Direct TypeScript execution | Use `.ts`, `.tsx`, `.mts`, or `.cts` where the runtime supports it |
| TypeScript extension rewriting | Use a TypeScript extension the compiler rewrites |
| Shared source consumed by bundlers and Node | Use the Node-compatible JavaScript extension |

These rules apply to relative specifiers. Package imports, package subpaths, and project
aliases are governed by package exports, package imports, or the selected resolver.

```typescript
// Bundler-owned application
import {helper} from './helper';

// Node-compatible ESM or shared bundler/Node source
import {helper} from './helper.js';

// Direct TypeScript execution or extension rewriting
import {helper} from './helper.ts';

// Package or configured alias
import {helper} from '@application/helper';
```

---

# Runtime Validation with Zod

> **Rule**: External data must be validated by a runtime schema before domain use. Type
> assertions (`as`) on external data are banned.

Type assertions only provide compile-time safety. They are lies to the compiler at
runtime. All external data — API responses, `JSON.parse` output, environment variables,
message queue payloads, storage — must pass through a runtime schema.

## Rules

- **Never** use `as` for external or runtime data sources.
- Validate before domain use. The schema call need not be syntactically nested with the
  parse call; it must merely precede any use of the value as domain data.
- Prefer passing `JSON.parse()` directly into a schema so no unvalidated intermediate
  value exists. Stage the parse only when separate syntax-error handling or reuse
  requires it, and type that value as `unknown`.
- **Never** leave a parsed value inferred as `any`. `JSON.parse()` returns `any`, so a
  bare `const parsed = JSON.parse(raw)` is a type hole even when a later statement
  validates it.
- Do not enforce this with a syntax selector that bans `JSON.parse()`. A syntax check
  cannot prove that the value was validated before use.
- Use `schema.parse()` when a validation failure should throw.
- Use `schema.safeParse()` when the error branch must be handled explicitly.
- Add `.refine()` / `.superRefine()` for domain-level constraints, not just shape.
- Use `.default()` for optional fields with known fallbacks.
- Use `.transform()` for data normalization at the boundary.
- Keep malformed input and well-formed-but-invalid shape technically distinct when
  diagnostics or behavior depend on the difference.
- Preserve maximum diagnostics: carry formatted schema output in the message and retain
  the original validation error as `Error.cause`.

## JSON parsing

Pass `JSON.parse()` directly into the schema by default:

```typescript
// ✅ Preferred: no unvalidated intermediate value
const user = UserSchema.parse(JSON.parse(raw));

// ✅ Preferred: explicit error branch
const result = UserSchema.safeParse(JSON.parse(raw));
if (!result.success) {
	throw new Error(`Invalid shape:\n${z.prettifyError(result.error)}`, {
		cause: result.error,
	});
}
const user = result.data;
```

Stage the parse only when syntax errors and shape errors need different handling, and
type the staged value as `unknown`:

```typescript
// ✅ Acceptable: staged and explicitly typed
let parsed: unknown;
try {
	parsed = JSON.parse(raw);
} catch (cause: unknown) {
	throw new Error('Malformed JSON', {cause});
}
const user = UserSchema.parse(parsed);
```

```typescript
// ❌ WRONG: no runtime validation
const data = JSON.parse(raw) as User;

// ❌ WRONG: the parsed value is `any`, so the later check is only partial protection
const parsed = JSON.parse(raw);
const user = UserSchema.parse(parsed);
```

A generic JSON or storage helper must not return a caller-chosen type. Return `unknown`
and let the caller validate, or accept a schema and return the schema's validated output:

```typescript
const readStoredValue = <S extends z.ZodType>(
	key: string,
	schema: S,
): z.output<S> | null => {
	const raw = storage.getItem(key);
	if (raw === null) {
		return null;
	}
	return schema.parse(JSON.parse(raw));
};

// Arbitrary JSON rather than a domain shape
const value = z.json().parse(JSON.parse(raw));
```

## Schema definition

Derive types from schemas, never the reverse.

```typescript
import {z} from 'zod';

const UserSchema = z.object({
	id: z.uuid(),
	name: z.string().min(1),
	email: z.email(),
	age: z.number().int().min(13),
});

type User = z.infer<typeof UserSchema>;
```

- Use top-level formats such as `z.uuid()`, `z.email()`, and `z.url()`. The chained
  `z.string().uuid()` forms are deprecated.
- Do not stack redundant constraints. `z.number().int().min(13)` already excludes zero
  and negatives, so an additional `.positive()` adds nothing.
- Replace the deprecated `error.format()` with `z.prettifyError()` for text output or
  `z.treeifyError()` for structured, path-based output.

## Fetch and transport boundaries

Use the established transport abstraction when one exists. Do not call `fetch` directly
from application or domain code to duplicate behavior the abstraction already owns.

The lowest-level transport boundary owns and distinguishes these failure classes:

1. Network or transport failure.
2. Non-successful HTTP status.
3. Response-body read failure.
4. Malformed JSON.
5. Well-formed JSON whose shape is invalid.

Endpoint boundaries own the endpoint-specific schema. Application code owns business
behavior and user-facing fallbacks. A user-facing fallback may be identical for several
internal failures, but the internal classification must stay distinct.

Interpret status before treating a body as a successful payload. Use `response.ok` by
default and document intentional status-specific semantics, such as a no-content
success, a protocol-signalling error status, or a health probe that reports availability
through the status code.

The pattern below is for **transport-adapter implementations**, not ordinary call sites:

```typescript
let response: Response;
try {
	response = await fetch(url);
} catch (cause: unknown) {
	throw new Error('Network request failed', {cause});
}

if (!response.ok) {
	throw new Error(`HTTP request failed: ${response.status}`);
}

let text: string;
try {
	text = await response.text();
} catch (cause: unknown) {
	throw new Error('Response body could not be read', {cause});
}

let parsed: unknown;
try {
	parsed = JSON.parse(text);
} catch (cause: unknown) {
	throw new Error('Response contains malformed JSON', {cause});
}

const result = UserSchema.safeParse(parsed);
if (!result.success) {
	throw new Error(`Invalid response shape:\n${z.prettifyError(result.error)}`, {
		cause: result.error,
	});
}
return result.data;
```

- Read the body as text before parsing when body-read failure and JSON-syntax failure
  must be distinguished; `response.json()` merges the two.
- A helper that wraps transport must not return a caller-selected generic type. It must
  return `unknown`, or accept a schema and return the schema's validated output.

## Environment Boundary

Environment variables are strings from an untrusted source. Direct access is
confined to one configuration adapter per runtime or executable, which validates
the environment with Zod once at startup and exports the parsed result.

```typescript
import {z} from 'zod';

const EnvironmentSchema = z.object({
	DATABASE_URL: z.url(),
	PORT: z.coerce.number().int().positive().default(3000),
	NODE_ENV: z.enum(['development', 'production', 'test']),
});

type Environment = z.infer<typeof EnvironmentSchema>;

const parseEnvironment = (source: unknown): Environment => {
	const result = EnvironmentSchema.safeParse(source);

	if (!result.success) {
		throw new Error(`Invalid environment:\n${z.prettifyError(result.error)}`, {
			cause: result.error,
		});
	}

	return result.data;
};

/** Validated environment for this executable; the only reader of the environment source. */
export const environment = parseEnvironment(process.env);
```

- Read `process.env` — or the runtime's equivalent environment source — only in that
  adapter. Application code imports the validated config and never reads the
  environment source directly.
- Give each runtime or executable its own adapter: Node reads `process.env`, browser
  bundles read `import.meta.env`, and other runtimes use their own source.
- Preserve diagnostics: put the formatted Zod output in the thrown message and retain
  the original error as `cause`.
