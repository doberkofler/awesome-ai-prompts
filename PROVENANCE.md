# Provenance and maintenance

This document is the source of truth for where `skills/` and `docs/` content
originates, how external material is adapted, and how canonical content is
distributed to supported agents.

`commands/` is outside this document's scope. `PROVENANCE.md` itself is not
distributed, so these maintenance details add no runtime context.

## Skills

### Upstream baseline

- Repository: [mattpocock/skills](https://github.com/mattpocock/skills)
- Last fully audited snapshot:
  [`b0618bc`](https://github.com/mattpocock/skills/commit/b0618bc436ad893b3c5e84e55fba86586d34a404)
  (2026-10-08)
- Layout: upstream category directories are flattened to `skills/<name>/`.
- Sidecars: upstream `agents/` directories are intentionally omitted.

`Verbatim` below means every retained payload file matched the audited snapshot.
It does not include the intentionally omitted `agents/` sidecars.

All files in the verbatim and adapted skill directories listed below are covered
by the upstream MIT license reproduced in
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md). Locally authored skills and
documents are not covered by that upstream notice.

### Verbatim skills

- [`grill-me`](https://github.com/mattpocock/skills/tree/b0618bc/skills/productivity/grill-me)
- [`grill-with-docs`](https://github.com/mattpocock/skills/tree/b0618bc/skills/engineering/grill-with-docs)
- [`grilling`](https://github.com/mattpocock/skills/tree/b0618bc/skills/productivity/grilling)
- [`handoff`](https://github.com/mattpocock/skills/tree/b0618bc/skills/productivity/handoff)
- [`research`](https://github.com/mattpocock/skills/tree/b0618bc/skills/engineering/research)
- [`writing-for-agents`](https://github.com/mattpocock/skills/tree/b0618bc/skills/productivity/writing-for-agents)

### Adapted skills

#### `code-review`

Source:
[`code-review`](https://github.com/mattpocock/skills/tree/b0618bc/skills/engineering/code-review)

Intentional differences:

- Accepts a local document, conversation requirements, or no spec.
- Has no issue-tracker or setup dependency.
- Reviews current uncommitted work as well as fixed-point commit ranges.
- Launches parallel reviewers only after an explicit user review request.
- Keeps all review work read-only and requires severity, evidence, and impact.

#### `codebase-design`

Source:
[`codebase-design`](https://github.com/mattpocock/skills/tree/b0618bc/skills/engineering/codebase-design)

Intentional difference: uses the local `CONTEXT.md` domain-language convention
instead of upstream `GLOSSARY.md`.

#### `diagnosing-bugs`

Source:
[`diagnosing-bugs`](https://github.com/mattpocock/skills/tree/b0618bc/skills/engineering/diagnosing-bugs)

Intentional differences:

- Uses `CONTEXT.md` instead of `GLOSSARY.md`.
- Records the successful hypothesis in the commit message rather than allowing a
  commit or PR message.

#### `domain-modeling`

Source:
[`domain-modeling`](https://github.com/mattpocock/skills/tree/b0618bc/skills/engineering/domain-modeling)

Intentional difference: retains `CONTEXT.md`, `CONTEXT-MAP.md`, and
`CONTEXT-FORMAT.md` instead of upstream's `GLOSSARY` names.

#### `prototype`

Source:
[`prototype`](https://github.com/mattpocock/skills/tree/b0618bc/skills/engineering/prototype)

Intentional difference: records the prototype branch in the implementation commit
instead of requiring an issue tracker.

#### `tdd`

Source:
[`tdd`](https://github.com/mattpocock/skills/tree/b0618bc/skills/engineering/tdd)

Intentional differences:

- Uses `CONTEXT.md` instead of `GLOSSARY.md`.
- Keeps the review-stage rule generic instead of requiring `code-review`.

#### `wait-what`

Source:
[`wait-what`](https://github.com/mattpocock/skills/tree/b0618bc/skills/productivity/wait-what)

Intentional difference: uses `CONTEXT.md` and `CONTEXT-MAP.md` instead of upstream's
`GLOSSARY` names.

### Local skills

#### `oracle-local`

Locally authored. It has no `mattpocock/skills` source.

### Selected upstream updates after initial adoption

- `handoff`: portable temporary-directory resolution from
  [`0f5e033`](https://github.com/mattpocock/skills/commit/0f5e033ebc47b142f5ffa56a582ede6d9d9bada3).
- `tdd`: document what each proposed seam catches and misses from
  [`3f59913`](https://github.com/mattpocock/skills/commit/3f599139104dfceabc7754eeb91319802f85e042).
- `grilling`: word questions so “yes” accepts the recommendation from
  [`95249b0`](https://github.com/mattpocock/skills/commit/95249b0b49782349740fd9b8c6ce32b4e59e497a).
- `diagnosing-bugs`: prove a forced mutation landed before trusting the red from
  [`f3fc563`](https://github.com/mattpocock/skills/commit/f3fc5632f401156837ee3872f14fe33ccf1024ea).

## Documents

No external upstream is recorded for the files under `docs/`; they are local policy
documents maintained in this repository.

- `general-guidelines.md`, `lint-rules.md`, `sql-plsql-rules.md`, and
  `typescript-rules.md` first appear in repository commit
  [`7b678ab`](https://github.com/doberkofler/awesome-ai-prompts/commit/7b678ab04d501aa38b58ce39f54863109976525e).
- `mui-rules.md` and `react-rules.md` first appear in repository commit
  [`9368ed0`](https://github.com/doberkofler/awesome-ai-prompts/commit/9368ed0ededbbf1bba95a0c6ebf670eae3d0b4d2).

Treat these files as opinionated local standards, not snapshots of vendor
documentation. Verify version-sensitive claims against primary vendor documentation
before changing them. Record an external source here if a future document is imported
or substantially adapted from one.

The domain-oriented skills intentionally use `CONTEXT.md` and `CONTEXT-MAP.md` for
glossaries and `docs/adr/` for decisions. This differs from upstream's current
`GLOSSARY` naming and must remain consistent across `domain-modeling`,
`grill-with-docs`, `wait-what`, `tdd`, and `diagnosing-bugs`.

## Synchronization and adaptation

There are two distinct operations:

1. **Upstream synchronization** is a manual review of external source changes before
   they enter this repository.
2. **Local distribution** copies this repository's accepted canonical content to
   agent-specific user directories.

`sync_ai_rules.py` performs only local distribution. It does not pull changes from
`mattpocock/skills` or any documentation source.

### Upstream skill update protocol

1. Read this file before comparing or adopting upstream skills.
2. Compare every borrowed skill against a pinned upstream commit.
3. Preserve every intentional difference unless the user explicitly changes it.
4. Record selected upstream commits and any new divergence here.
5. Advance the audited snapshot only after checking every borrowed skill.
6. Keep only generic, self-contained skills. Remove issue-tracker and personal-workflow
   dependencies unless this repository explicitly adopts them.
7. Flatten upstream category paths to `skills/<name>/` and omit upstream `agents/`
   sidecars.
8. Validate frontmatter and every cross-skill reference.

### Document update protocol

1. Identify whether the change is local policy or a version-sensitive vendor claim.
2. Validate vendor claims against primary documentation for the applicable version.
3. Keep each rule in one `docs/*.md` source file; do not duplicate it in `README.md`
   or `AGENTS.md`.
4. Record newly imported or adapted external sources in this document.

### Local distribution

Running `python3 sync_ai_rules.py`:

- concatenates `docs/*.md` in filename order into a marked repository-owned block
  (`<!-- BEGIN/END awesome-ai-prompts -->`) inside each agent's native global rules
  file, replacing only that block and preserving content outside it; an existing
  rules file without the block is left intact and the block is appended;
- copies each `skills/<name>/` payload file to `~/.agents/skills/` and
  `~/.claude/skills/`, omitting only a top-level `agents/` sidecar directory and
  `.DS_Store` files (a nested `agents/` directory is kept);
- copies each command to every agent's command directory, and reports matching native
  OpenCode skills under `~/.config/opencode/skills/` that override shared copies;
- records every managed file and rules block, with its SHA-256, in
  `~/.ai-rules/manifest.json`, alongside the installed repository commit.

Ownership is explicit. A target path that exists but is not recorded in the manifest
is user-owned and is never overwritten. A recorded path whose content no longer
matches its recorded hash is locally modified; unless `--force` is given, the run
stops before mutating anything. Pruning removes only paths recorded as managed by the
previous manifest and inside the selected scope, so unrelated and locally added files
survive installation, update, and removal. The first run after an upgrade migrates the
previous `installed` and `managed-skills` files: paths the old installer managed are
adopted with their current content as the baseline, then refreshed.

Every run is planned before it mutates anything:

- `--dry-run` prints the exact plan (creates, updates, conflicts, removals, unchanged)
  and changes nothing, including on a conflicting target;
- `--agent <name>` (repeatable) limits the run to named agents and leaves every other
  agent's installed content untouched; the default remains all agents;
- each changed file is written atomically;
- a timestamped backup of every touched path is written under `~/.ai-rules/backups/`
  before the first mutation;
- if any mutation fails, the whole run is rolled back and the backup is discarded;
- `--uninstall` removes only manifest-owned, unmodified content and preserves content
  outside the managed block; locally modified managed files are kept unless `--force`
  is given;
- `--restore [BACKUP]` restores an installer-created backup (default: latest).

`--check` reports two independent statuses and exits nonzero when either is unhappy:

- **repository** compares the revision recorded in the manifest with the fetched
  upstream revision (`up to date`, `update available`, or `unknown`);
- **integrity** compares every managed path against its recorded SHA-256 and the
  current source, and lists, separately, `modified` (content changed), `missing`
  (deleted, or rules block markers gone), `unexpected` (an unmanaged file where the
  source wants one), and `obsolete` (managed paths the source no longer distributes)
  artifacts. An unreadable or absent manifest, a legacy-only install, or an
  unresolvable upstream revision is an unavailable required check and also exits
  nonzero.

The check never mutates installed content.

The script uses user-level directories, symlinks no content, and requires no
administrator rights. It also removes only legacy paths that earlier versions of this
repository managed.

OpenCode V2 reads global rules from `~/.config/opencode/AGENTS.md`; its accepted but
inactive `instructions` setting is not a second rule source. Codex reads one
concatenated `~/.codex/AGENTS.md`; increase `project_doc_max_bytes` when the installer
reports truncation. Codex custom prompts are deprecated, but remain a compatibility
distribution target.

After changing `docs/`, `skills/`, or distribution behavior:

1. Run `python3 sync_ai_rules.py`.
2. Run `python3 sync_ai_rules.py --check` and require `repository` status `up to date`
   and `integrity` status `ok`.
3. Resolve every validation or size warning, or report the unresolved blocker.
