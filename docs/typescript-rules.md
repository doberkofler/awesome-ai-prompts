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

## Formatting and naming

- Let Oxfmt enforce tabs, semicolons, single quotes, spacing, and wrapping.
- Never omit curly braces around blocks, even when they are optional

### Naming Conventions
- **Variables/Functions**: `camelCase`
- **Files**: `camelCase` (e.g., `user.ts`, `supplierInvoice.ts`); named React component
  files use `PascalCase.tsx`
- **Constants**: `UPPER_CASE` for global constants

## JavaScript
- Target ES2022
- Only use ESM

## Type Safety & Configuration

> Type safety is a top priority. Never weaken it for convenience.

- Use the following flags in `tsconfig.json`:

```json
{
	"strict": true,
	"noImplicitAny": true,
	"strictNullChecks": true,
	"strictFunctionTypes": true,
	"strictBindCallApply": true,
	"strictPropertyInitialization": true,
	"noImplicitThis": true,
	"useUnknownInCatchVariables": true,
	"alwaysStrict": true,
	"noUnusedLocals": true,
	"noUnusedParameters": true,
	"noImplicitReturns": true,
	"noFallthroughCasesInSwitch": true,
	"noUncheckedIndexedAccess": true,
	"noImplicitOverride": true,
	"noPropertyAccessFromIndexSignature": false,
	"exactOptionalPropertyTypes": true,
	"allowUnreachableCode": false,
	"allowUnusedLabels": false,
	"forceConsistentCasingInFileNames": true,
	"noEmitOnError": true
}
```

### Semantic safety

Enforce these language constraints through Oxlint:

- Use strict equality and an explicit radix.
- Use `const` by default and never use `var`.
- Reject `eval`, implied evaluation, `new Function`, `with`, and native-object
  extension.
- Throw `Error` objects rather than literals.
- Reject variable shadowing and invalid derived-class construction.
- Keep direct environment access inside the project's runtime boundary.
- Reject floating and misused promises, unsafe `any` operations, array deletion,
  dynamic property deletion, unnecessary assertions and constraints, duplicate union
  constituents, wrapper object types, invalid thrown values, and unbound methods.
- Require explicit module-boundary types and explicit member accessibility.

Treat complexity limits as advisory signals, not correctness failures. Default warning
thresholds are complexity 30, nesting depth 10, 1,300 lines, 10 parameters, 150
statements, and 10 nested callbacks. Projects may override these thresholds explicitly.

Use conventional rather than Yoda conditions, declare variables at the top of their
scope, use property dot notation except for snake-case keys, and reject implicit
coercion except explicit boolean coercion with `!!`. Report `prefer-const` as a warning.
Do not require template literals, object shorthand, spread syntax, import sorting, or
bans on increments and numeric literals.

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

## Documentation
- Use JSDoc (`/** ... */`) for all exported functions and types
- Especially required in `src/data/`

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
- Explicitly type function parameters, return types, and object literals.
- No enums. Use union types.
- Use `readonly` modifiers for immutable properties and arrays.
- Use `private` modifiers for private class members.
- Leverage utility types (`Partial`, `Required`, `Pick`, `Omit`, `Record`, etc.).
- Use discriminated unions with exhaustiveness checking for type narrowing.
- Handle `null` and `undefined` explicitly — never assume.
- All exported functions must have explicit return types.
- Prefer `type` over `interface`.

## Advanced Patterns

- Implement generics with appropriate constraints — avoid unconstrained `T` where a bound is possible.
- Use mapped types and conditional types to reduce type duplication.
- Use `const` assertions for literal types.
- Implement branded/nominal types for type-level validation where domain correctness matters (e.g., `UserId`, `EmailAddress`).

## Code Organization

- Organize types in dedicated files (`types.ts`) or alongside implementations.
- Document everything with JSDoc.
- Create a central `types.ts` or `src/types/` directory for shared types.

## Best Practices

- Use `??` and `?.` where appropriate — never use `||` as a null-coalescing substitute (it conflates `null`/`undefined` with falsy).
- Prefix unused variables with `_` (e.g., `_unusedParam`).
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
- Explicit file extensions in relative imports: `import {helper} from './utils.ts'`.

---

# Runtime Validation with Zod

> **Rule**: `JSON.parse` is banned without Zod. Type assertions (`as`) on external data are banned. No exceptions without explicit permission.

Type assertions only provide compile-time safety. They are lies to the compiler at runtime. All external data — API responses, `JSON.parse` output, environment variables, message queue payloads, localStorage — must go through Zod.

## Rules

- **Never** use `as` for external/runtime data sources.
- **Never** call `JSON.parse(...)` and use the result without immediately passing it to a Zod schema.
- Use `schema.parse()` when a validation failure should throw.
- Use `schema.safeParse()` when you want to handle the error branch explicitly.
- Add `.refine()` / `.superRefine()` for domain-level constraints (not just shape).
- Use `.default()` for optional fields with known fallbacks.
- Use `.transform()` for data normalization at the boundary.

## Patterns

```typescript
// ❌ WRONG: type assertion — no runtime safety
const data = JSON.parse(raw) as User;

// ❌ WRONG: JSON.parse without immediate Zod validation
const parsed = JSON.parse(raw);
const user = UserSchema.parse(parsed); // still wrong — the parse is unguarded

// ✅ RIGHT: immediate Zod parse on JSON.parse output
const user = UserSchema.parse(JSON.parse(raw));

// ✅ RIGHT: safeParse for non-throwing path
const result = UserSchema.safeParse(JSON.parse(raw));
if (!result.success) {
	throw new Error(`Invalid shape: ${result.error.format()}`);
}
const user = result.data;
```

```typescript
import {z} from 'zod';

// Define schema — derive type from it, never the reverse
const UserSchema = z.object({
	id: z.string().uuid(),
	name: z.string().min(1),
	email: z.string().email(),
	age: z.number().int().positive().min(13),
});

type User = z.infer<typeof UserSchema>;

/** Fetches and validates a user by ID. Throws on invalid shape or network error. */
export const fetchUser = async (id: string): Promise<User> => {
	const response = await fetch(`/api/users/${id}`);
	const raw: unknown = await response.json();
	return UserSchema.parse(raw);
};
```

## Environment Variables

Environment variables are strings from an untrusted source. Validate them at startup:

```typescript
import {z} from 'zod';

const EnvSchema = z.object({
	DATABASE_URL: z.string().url(),
	PORT: z.coerce.number().int().positive().default(3000),
	NODE_ENV: z.union([z.literal('development'), z.literal('production'), z.literal('test')]),
});

/** Parsed and validated environment. Throws at startup if env is malformed. */
export const env = EnvSchema.parse(process.env);
```
