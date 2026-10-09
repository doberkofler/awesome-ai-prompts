---
name: code-review
description: Review a branch, commit range, or current worktree independently against repository standards and the originating specification. Use only when the user explicitly requests a code, PR, branch, or fixed-point review.
---

# Code Review

Review changes along two independent axes:

- **Standards**: does the change follow the repository's documented standards?
- **Spec**: does the change implement the requested behavior without omissions or scope creep?

This is a read-only review. Do not modify files.
Run the two axes in parallel subagents only after the user explicitly requests a review.
An implementation finishing is not, by itself, permission to launch a review.

## 1. Fix the review scope

Translate the user's request into one immutable scope before dispatching reviewers:

- For a supplied commit, tag, or branch, verify it with `git rev-parse`, then review
  `git diff <fixed-point>...HEAD` and `git log <fixed-point>..HEAD --oneline`.
- For current uncommitted work, review `git status --short`, `git diff HEAD`, and
  the complete contents of untracked files.
- If the request does not identify either scope, ask which scope to review.

Stop when the reference is invalid or the selected scope contains no changes.

## 2. Identify the spec source

Use the first available source:

1. A path or document supplied by the user.
2. Requirements and decisions stated in the current conversation.
3. A matching local file under `docs/`, `specs/`, `plans/`, or an equivalent project directory.

Pass the source path or relevant conversation requirements to the Spec reviewer.
If no source exists, skip that reviewer and report **No spec available**.
An issue tracker is never required.

## 3. Identify the standards sources

Find every applicable repository document that governs the changed files, including
nested `AGENTS.md` or `CLAUDE.md`, `CONTRIBUTING.md`, and dedicated coding-standard
documents. Pass their paths to the Standards reviewer.

Apply this smell baseline only where repository standards do not intentionally choose
otherwise. Treat every smell as a judgement call, not a hard violation:

- **Mysterious Name**: a name does not reveal what it represents. Rename it; if no
  honest name exists, the design is unclear.
- **Duplicated Code**: the same logic shape appears in multiple changed locations. Extract the shared shape.
- **Feature Envy**: code reaches into another module's data more than its own. Move
  the behavior toward the data it uses.
- **Data Clumps**: the same fields or parameters repeatedly travel together. Model them as one concept.
- **Primitive Obsession**: a primitive represents a domain concept with behavior or invariants. Give the concept a type.
- **Repeated Switches**: conditionals repeatedly branch on the same discriminator.
  Centralize the decision or use polymorphism.
- **Shotgun Surgery**: one logical change requires scattered edits. Gather what changes together behind one interface.
- **Divergent Change**: one module changes for unrelated reasons. Split responsibilities at the real seam.
- **Speculative Generality**: abstractions or hooks serve no current requirement.
  Remove them until a demonstrated need exists.
- **Message Chains**: callers navigate through long object chains. Hide the traversal behind the owning interface.
- **Middle Man**: a module mostly delegates without reducing complexity. Remove it or deepen it.
- **Refused Bequest**: an implementation rejects most of an inherited contract.
  Prefer composition or a narrower contract.

## 4. Dispatch independent reviewers

When a spec exists, launch both foreground subagents in parallel. If the runtime
cannot run them in parallel, run isolated subagents sequentially and disclose that
constraint. When no spec exists, launch only the Standards reviewer. Never combine
both axes in one reviewer.

### Standards reviewer

Provide:

- the fixed scope and exact diff inputs;
- the applicable standards-source paths;
- the complete smell baseline above.

Ask it to report:

1. Documented-standard violations, citing the source rule and changed file location.
2. Possible baseline smells, naming the smell and citing the changed file location.

Require severity, evidence, and impact for every finding. Distinguish hard documented
violations from judgement calls. Omit style preferences unsupported by a source or
baseline smell. Do not edit files.

### Spec reviewer

Provide:

- the same fixed scope and exact diff inputs;
- the spec path or conversation requirements.

Ask it to report:

1. Missing or partially implemented requirements.
2. Behavior added without a requirement.
3. Implemented behavior that contradicts the requirement.

Require the requirement evidence and changed file location for every finding. Do not edit files.

## 5. Report

Present findings under separate `## Standards` and `## Spec` headings. Preserve each
axis's severity order; do not merge or rerank findings across axes.

For every finding include:

- severity;
- changed file and line;
- evidence;
- consequence.

If an axis has no findings, state that explicitly. End with the finding count and
highest severity for each axis. Never claim the change is correct merely because both
reviewers found nothing; state that no issues were found within the reviewed scope.
