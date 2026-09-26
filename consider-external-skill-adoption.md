# Skill Adoption Analysis

You are a principal engineer curating a personal agent-rules repository. Analyze an
upstream skills repository and decide which skills, if any, to adopt locally.

**Analysis only.** Produce a report. Do not edit files, change sync state, or commit.
Halt for approval.

## Inputs
- Upstream repo: default `https://github.com/mattpocock/skills` (branch `main`).
  Override if `$ARGUMENTS` names another.
- Local repo: this repository. Read first: `skills/` (and each `SKILL.md` frontmatter),
  `commands/`, `docs/`, `AGENTS.md`, `sync_ai_rules.py`.

## Step 1 — Inventory upstream
1. Fetch `https://api.github.com/repos/<owner>/<repo>/git/trees/main?recursive=1`.
   It can truncate; if so, walk directories via the contents API.
2. Fetch the README reference section (authoritative list + invocation class).
3. For each skill, fetch `skills/**/SKILL.md`; record: name, description, invocation
   (`disable-model-invocation`?), bundled files (siblings, scripts, templates), and
   every other skill it references.
4. Treat upstream `docs/` as per-skill prose, not rules. Ignore `.changeset/`,
   `.out-of-scope/`, `.claude-plugin/`, `skills/deprecated/`, `skills/in-progress/`.

## Step 2 — Inventory local
Note each local skill/command/doc's purpose; map what already exists and overlaps.

## Step 3 — Filter (hard constraints)
- **Generic only.** Exclude any skill that assumes an issue tracker or host workflow
  (GitHub/GitLab/Linear), or needs a per-repo `setup` step. Upstream examples:
  setup-matt-pocock-skills, triage, to-spec, to-tickets, implement, wayfinder, ask-matt,
  code-review.
- **Self-contained.** No dependency on an absent skill; if it references one, mark it a
  dependency to include or a reason to skip.
- **Runtime-feasible.** Flag background/parallel sub-agent needs and network/CDN use.
- **No overlap.** Reject skills duplicating an existing local skill or each other.
- **Domain-doc assumptions.** Note reliance on `CONTEXT.md`/`CONTEXT-MAP.md`/`docs/adr/`.

## Step 4 — Classify
Per candidate: **Already have / Adopt / Adapt (why) / Skip (why) / Defer**, naming the
tradeoff (perf, maintainability, correctness, security).

## Step 5 — Adoption mechanics (only when asked to implement)
- Flatten to `skills/<name>/`; directory name == frontmatter `name`; description ≤ 1024
  chars; `disable-model-invocation: true` for user-invoked only.
- Strip upstream's per-skill `agents/` sidecars.
- Keep wrappers as stubs; move shared files to the owning skill.
- Remove/reword every reference to a non-adopted skill.
- Record new conventions in `AGENTS.md` and `README.md`.

## Step 6 — Verify (only when asked to implement)
- Check frontmatter and that all cross-skill references resolve.
- Run `./sync_ai_rules.py`, then `./sync_ai_rules.py --check`; require `up to date`.
- List uncommitted changes. Do not commit.

## Output
1. Upstream inventory table: skill | class | deps | decision | reason.
2. Recommended set with rationale.
3. Integration notes (layout, sidecars, refactors, convention changes).
4. Open questions. Then stop and wait for approval.

## Hard constraints
- No edits during analysis. Halt for approval before any file change.
- `[UNVERIFIED]` for any claim not confirmed from a fetched source.
- If network access is unavailable, say so and halt; never invent the inventory.
- Quote primary sources (repo files), not memory.
