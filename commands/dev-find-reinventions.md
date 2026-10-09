---
description: Scans a TypeScript/Node repo for (1) duplicated in-repo code
  and (2) custom code duplicating builtin/framework/npm functionality.
  Read-only — reports findings, makes no changes, asks nothing.
agent: plan
---

# Find Reinventions

Scope: `$ARGUMENTS` or repo root. Skip `node_modules/`, `dist/`, `build/`,
anything in `.gitignore`, and generated files (`*_generated.*`, `*.pb.go`,
`*_pb2.py`, minified bundles).

## Pass A — Internal duplication
Look for functions/modules that do the same thing. Group by structural or
token-level similarity — state which basis you used, not just matching
names. For each group, report which one looks canonical (most usages, or
simplest) and where the others are used.

## Pass B — Reinvents something that already exists
For each hand-rolled utility (retry, debounce, deep clone, crypto,
serialization, caching, parsing, etc.), check all four:
1. Node/Web builtin (`structuredClone`, `crypto.subtle`, `AbortSignal`, …)
2. A first-class primitive of a framework already in use
3. Already a dependency in `package.json`/lockfile
4. A well-known npm package (e.g. `lodash.debounce`, `p-retry`, `jose`)

Recommend the simplest option already available. A builtin wins whenever
it's equivalent to the custom code. Any suggested package not already in
`package.json`/lockfile is unverified — no network calls, so mark it
`(unverified)` rather than asserting it fits or is current.

## Rules
- Flag hand-rolled crypto/auth/secret handling first — always report it.
- State what version/context a claim depends on (e.g. "Node ≥17 for
  `structuredClone`") — don't assume, note the assumption.
- If you can't verify something, say so instead of guessing.

## Report

| # | file | issue | suggestion |
|---|---|---|---|

One line per finding. No fixes, no questions — just the table.
