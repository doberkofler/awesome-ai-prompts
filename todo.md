# Incremental improvement TODO

Temporary working list derived from the validated external critique.
Complete one phase at a time; keep each commit independently usable.

## Ground rules

- Preserve user-owned files by default.
- Treat risk as a defect without claiming historical data loss.
- Back behavior changes with tests before expanding installer features.
- Use primary vendor documentation for version-sensitive rules.
- Update `PROVENANCE.md` when changing `docs/`, `commands/`, adopted skills, or
  distribution behavior.
- Run `python3 sync_ai_rules.py --check` after a distribution change.

## Phase 8 — Target-specific global context and limits

- [ ] Measure the context loaded automatically by each target, including generated
  rule blocks and always-loaded skill metadata; distinguish it from on-demand command
  and skill bodies.
- [ ] Define the minimal rules needed in every project and every session.
- [ ] Move TypeScript, React, MUI, and SQL/PLSQL guidance behind relevant on-demand
  skills or pointers.
- [ ] Keep cross-language safety and interaction rules globally available.
- [ ] Remove contradictory clarification and verbosity requirements or define explicit
  precedence.
- [ ] Add general safeguards for destructive actions, secrets, scope, and external data
  sharing.
- [ ] Keep each target's automatically loaded instructions below its effective default
  limit without requiring user configuration changes or tolerating truncation.

Done when irrelevant technology rules are absent from a new unrelated session and no target truncates instructions.

## Phase 9 — Portable, bounded commands

- [ ] Bound `dev-decompose` verification loops with a blocker and escalation path.
- [ ] Replace unconditional full-file embedding with relevance and size limits.
- [ ] Remove repeated CI and full-context instructions without weakening completion criteria.
- [ ] Give `dev-find-reinventions` measurable evidence, locations, confidence, and severity fields.
- [ ] Define behavior for invalid scope, unavailable tools, and repositories too large to inspect safely.
- [ ] Add the required third-party disclosure before `dev-verimode` sends search terms externally.
- [ ] Shorten `dev-reset` frontmatter without changing its behavior.
- [ ] Verify command support, invocation syntax, arguments, and metadata for every target.
  Transform commands per target or stop distributing unsupported command formats; do not
  copy OpenCode frontmatter unchanged everywhere.

Done when every command has a bounded workflow, verifiable output, and documented target compatibility.

## Deferred

- [ ] Decide whether complexity thresholds should become stricter after collecting project evidence.

## Removed after review

- Phase 7 (import grouping, named exports, `structuredClone`): declined decisions already
  recorded in `docs/typescript-rules.md`; not actionable.
- Emoji headings: no concrete rendering or accessibility defect.
- Public-project governance files: repository is explicitly personal policy.
- Executable reference configurations: contradicts the documentation-only constraint
  (no Node tooling, fixtures, lockfiles, or TypeScript configs).
