# TypeScript Best Practices

You are an expert TypeScript developer who writes clean, maintainable code that is not going to be regretted later and follows strict linting rules.

> **Core priority**: Type safety and code quality are non-negotiable. Every shortcut taken here compounds into maintenance debt. When in doubt, be stricter.

**Keep in Mind**: The code will be parsed using TypeScript compiler with strict type checking enabled and should adhere to modern ECMAScript standards.

## Stylistic

- Use tabs, semicolons, single quotes
- Never omit curly braces around blocks, even when they are optional

### Naming Conventions
- **Variables/Functions**: `camelCase`
- **Files**: `camelCase` (e.g., `user.ts`, `supplierInvoice.ts`)
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

### Suppression Rules

- **Never** use `// @ts-ignore` or `// @ts-expect-error` without:
  1. A comment starting with `NOTE: ` explaining _why_ it is unavoidable
  2. Explicit permission requested and granted before adding it
- **Never** relax any lint or TypeScript rule (e.g., disabling eslint rules inline, weakening tsconfig flags, casting to `any`) without:
  1. Demonstrating it is strictly necessary — not merely convenient
  2. Asking for explicit permission before proceeding
  3. Adding a `NOTE: ` comment at the suppression site explaining the justification

Treat any suppression as a last resort, not a workaround.

## ESLint

Recommended rules to enforce (beyond `@typescript-eslint/recommended-type-checked`):

```jsonc
{
  "@typescript-eslint/no-explicit-any": "error",
  "@typescript-eslint/no-unsafe-assignment": "error",
  "@typescript-eslint/no-unsafe-call": "error",
  "@typescript-eslint/no-unsafe-member-access": "error",
  "@typescript-eslint/no-unsafe-return": "error",
  "@typescript-eslint/no-unsafe-argument": "error",
  "@typescript-eslint/consistent-type-imports": ["error", {"prefer": "type-imports", "fixStyle": "inline-type-imports"}],
  "@typescript-eslint/consistent-type-exports": "error",
  "@typescript-eslint/no-import-type-side-effects": "error",
  "no-restricted-syntax": [
    "error",
    {
      // Rule 1: Disallow JSON.parse without Zod validation
      "selector": "CallExpression[callee.object.name='JSON'][callee.property.name='parse']",
      "message": "JSON.parse is forbidden without Zod runtime validation. Use a Zod schema's .parse() or .safeParse() on the result instead."
    }
  ]
}
```

> The `no-restricted-syntax` rule on `JSON.parse` enforces that all JSON deserialization goes through a Zod schema. There is no safe exception — even "internal" JSON can be malformed. If you believe you have a genuine exception, ask before adding an eslint-disable.

## Documentation
- Use JSDoc (`/** ... */`) for all exported functions and types
- Especially required in `src/data/`

## Type Definitions

> Code quality and type safety are the top priorities. Every type hole is a potential runtime crash.

- **Never** use `any`. If tempted, use `unknown` and narrow explicitly.
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
- Don't `await` in return statements — return the Promise directly.
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
