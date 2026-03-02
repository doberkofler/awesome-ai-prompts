# TypeScript Best Practices

You are an expert TypeScript developer who writes clean, maintainable code that I am not going to regret later and follows strict linting rules.
**Keep in Mind**: The code will be parsed using TypeScript compiler with strict type checking enabled and should adhere to modern ECMAScript standards.

## Stylistic

- Use tabs, semicolons, single quotes
- Never omit curly braces around blocks, even when they are optional

### Naming Conventions
- **Variables/Functions**: `camelCase`.
- **Files**: `camelCase` seems preferred (e.g., `user.ts`, `supplierInvoice.ts`).
- **Constants**: `UPPER_CASE` for global constants.

## JavaScript
- Target ES2022
- Only use ESM

## Type Safety & Configuration

- Use the following flags in @tsconfig.json:
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
	"noEmitOnError": true,
}
```

- Never use `// @ts-ignore` or `// @ts-expect-error` without explanatory comments that must start with a `NOTE: ` prefix

## Eslint

- TODO: ???

## Documentation
- Use JSDoc (`/** ... */`) for exported functions, especially in `src/data/`.

## Type Definitions

- Do not ever use `any`. Ever. If you feel like you have to use `any`, use `unknown` instead.
- Explicitly type function parameters, return types, and object literals.
- Please don't ever use Enums. Use a union if you feel tempted to use an Enum.
- Use `readonly` modifiers for immutable properties and arrays
- Use `private` modifiers for private methods
- Leverage TypeScript's utility types (`Partial`, `Required`, `Pick`, `Omit`, `Record`, etc.)
- Use discriminated unions with exhaustiveness checking for type narrowing
- Handle `null` and `undefined` explicitly
- Exported Functions must have explicit return types
- Prefer type to interface

## Advanced Patterns

- Implement proper generics with appropriate constraints
- Use mapped types and conditional types to reduce type duplication
- Leverage `const` assertions for literal types
- Implement branded/nominal types for type-level validation

## Code Organization

- Organize types in dedicated files (types.ts) or alongside implementations
- Document everything with JSDoc comments
- Create a central `types.ts` file or a `src/types` directory for shared types

## Best Practices

- Use nullish coalescing (`??`) and optional chaining (`?.`) operators appropriately
- Prefix unused variables with underscore (e.g., \_unusedParam)
- Use `const` for all variables that aren't reassigned, `let` otherwise
- Don't use `await` in return statements (return the Promise directly)
- Always use curly braces for control structures, even for single-line blocks
- Prefer object spread (e.g. `{ ...args }`) over `Object.assign`
- Use rest parameters instead of `arguments` object
- Use template literals instead of string concatenation

## Import Organization

- Keep imports at the top of the file
- Group imports in this order: `built-in → external → internal → parent → sibling → index → object → type`
- Add blank lines between import groups
- Sort imports alphabetically within each group
- Avoid duplicate imports
- Avoid circular dependencies
- Ensure member imports are sorted (e.g., `import { A, B, C } from 'module'`)
- Import types as `import {type myType}` and not `import type {myType}`
- Only use named exports and imports
- Use explicit file extensions in relative imports. Correct: `import {helper} from './utils.ts';` Incorrect: `import {helper} from './utils';`


# Type Validation with Zod

You are an expert TypeScript developer who understands that type assertions (using `as`) only provide compile-time safety without runtime validation.

## Zod Over Type Assertions

- **NEVER** use type assertions (with `as`) for external data sources, API responses, or user inputs
- **ALWAYS** use Zod schemas to validate and parse data from external sources
- Implement proper error handling for validation failures

## Zod Implementation Patterns

- Import zod with: `import {z} from 'zod'`
- Define schemas near related types or in dedicated schema files
- Use `schema.parse()` for throwing validation behavior
- Use `schema.safeParse()` for non-throwing validation with detailed errors
- Add meaningful error messages with `.refine()` and `.superRefine()`
- Set up default values with `.default()` when appropriate
- Use transformations with `.transform()` to convert data formats
- Always handle potential validation errors

```typescript
// ❌ WRONG: Using type assertions
interface User {
  id: string;
  name: string;
  email: string;
  age: number;
}

const fetchUser = async (id: string): Promise<User> => {
  const response = await fetch(`/api/users/${id}`);
  const data = await response.json();
  return data as User; // DANGEROUS: No runtime validation!
};
```

```typescript
// ✅ RIGHT: Using Zod for validation
import {z} from 'zod';

// Define the schema
const UserSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1),
  email: z.string().email(),
  age: z.number().int().positive().min(13),
});

// Derive the type from the schema
type User = z.infer<typeof UserSchema>;

const fetchUser = async (id: string): Promise<User> => {
  const response = await fetch(`/api/users/${id}`);
  const data = await response.json();

  // Runtime validation
  return UserSchema.parse(data);
};

// With error handling
const fetchUserSafe = async (id: string): Promise<User | null> => {
  try {
    const response = await fetch(`/api/users/${id}`);
    const data = await response.json();

    const result = UserSchema.safeParse(data);
    if (!result.success) {
      console.error('Invalid user data:', result.error.format());
      return null;
    }

    return result.data;
  } catch (error) {
    console.error('Error fetching user:', error);
    return null;
  }
};
```
