# Provenance and maintenance

This document is the source of truth for where `skills/`, `docs/`, and
`commands/` content originates, how external material is adapted, and how
canonical content is distributed to supported agents.

`PROVENANCE.md` itself is not distributed, so these maintenance details add no
runtime context.

## Repository rename

The repository was renamed in place from `awesome-ai-prompts` to
`personal-agent-config`. The slug, the release archive prefix, the managed-block
markers, and every canonical URL now use the new name; the historical commit
links in this document resolve through GitHub's rename redirect.

GitHub preserves issues, wikis, stars, followers, and releases, and continues to
redirect web, `git clone`, `git fetch`, and `git push` traffic from the old slug.
Existing clones still work, but should retarget their remote:

```bash
git remote set-url origin https://github.com/doberkofler/personal-agent-config.git
```

The old name must never be reused for a new repository, or the redirects stop
working.

Installed rules migrate automatically. The installer recognizes the previous
managed-block markers (`<!-- BEGIN/END awesome-ai-prompts -->`), rewrites them
in place with the new markers on the next run, and preserves all content outside
the block. It also still recognizes the superseded one-line marker
`<!-- awesome-ai-prompts <sha> -->`. A file that mixes or duplicates marker
generations is reported as a malformed block and left untouched.

## Skills

### Upstream baseline

- Repository: [mattpocock/skills](https://github.com/mattpocock/skills)
- Last fully audited snapshot:
  [`b0618bc`](https://github.com/mattpocock/skills/commit/b0618bc436ad893b3c5e84e55fba86586d34a404)
  (2026-10-08)
- Layout: upstream category directories are flattened to `skills/<name>/`.
- Sidecars: upstream `agents/` directories are intentionally omitted.

`Verbatim` below means every retained payload file matched the audited snapshot.
It does not include the intentionally omitted `agents/` sidecars. Each listed
skill is checked against that snapshot by
[`tests/test_provenance_verbatim.py`](tests/test_provenance_verbatim.py) when
network access is available; the test is skipped offline.

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
  [`7b678ab`](https://github.com/doberkofler/personal-agent-config/commit/7b678ab04d501aa38b58ce39f54863109976525e).
- `mui-rules.md` and `react-rules.md` first appear in repository commit
  [`9368ed0`](https://github.com/doberkofler/personal-agent-config/commit/9368ed0ededbbf1bba95a0c6ebf670eae3d0b4d2).

Treat these files as opinionated local standards, not snapshots of vendor
documentation. Verify version-sensitive claims against primary vendor documentation
before changing them. Record an external source here if a future document is imported
or substantially adapted from one.

Examples in the TypeScript documents are guidance; the repository never compiles, lints,
or tests them. Consuming projects own their configurations, dependency versions,
lockfiles, and tests, so no example is claimed to be locally verified.

The TypeScript policy has one ownership chain: `typescript-rules.md` is the canonical
language and runtime-safety baseline, `lint-rules.md` defines its Oxlint/Oxfmt tooling
implementation, and `react-rules.md` adds only React-specific design rules. Suppression
directives and the `any` policy have one form, defined in `typescript-rules.md` and
enforced, not redefined, in `lint-rules.md`. Module-file naming and API-documentation
conventions are also owned by `typescript-rules.md`; `react-rules.md` defers to them
instead of restating them. `lint-rules.md` owns the tooling enforcement model: root
type-aware linting with `tsc --noEmit` as the authoritative gate, per-family rule
scoping, and the replacement invariant that disables a base rule only where its
type-aware replacement is enabled in the same scope. Projects may replace a baseline rule
only with an explicit scoped override and reason, and no override may lower coverage,
lower a rule's severity, or disable a rule without an enabled replacement in that scope.
`typescript-rules.md` also classifies its non-formatting rules: each correctness or
security rule states the failure mode it closes, while readability and architecture
rules (Yoda conditions, declaration placement, complexity thresholds, import grouping)
are documented as guidance rather than defects. Classification clarifies intent; it does
not remove or downgrade any rule.

The domain-oriented skills intentionally use `CONTEXT.md` and `CONTEXT-MAP.md` for
glossaries and `docs/adr/` for decisions. This differs from upstream's current
`GLOSSARY` naming and must remain consistent across `domain-modeling`,
`grill-with-docs`, `wait-what`, `tdd`, and `diagnosing-bugs`.

## Commands

The files under `commands/` are locally authored and have no external upstream.
They are OpenCode-style command protocols that the installer distributes to every
supported agent's command directory.

- `dev-reset.md` and `dev-verimode.md` first appear in repository commit
  [`3e56d9d`](https://github.com/doberkofler/personal-agent-config/commit/3e56d9d56acddcb7cbcf305986d3691b44f98a16).
- `dev-decompose.md` first appears in repository commit
  [`a51dc4f`](https://github.com/doberkofler/personal-agent-config/commit/a51dc4f3117d7118cce18bf06d653411c4e0ad9d).
- `dev-find-reinventions.md` first appears in repository commit
  [`a650280`](https://github.com/doberkofler/personal-agent-config/commit/a6502800aaca063f3e2cc8f97df206d0ead35aab).

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
  (`<!-- BEGIN/END personal-agent-config -->`) inside each agent's native global rules
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

`--check` reports two independent statuses:

- **repository** compares the revision recorded in the manifest with the fetched
  upstream revision (`up to date`, `update available`, or `unknown`). This status is
  informational and does not affect the exit code, because a verified release archive
  has no git metadata to compare;
- **integrity** compares every managed path against its recorded SHA-256 and the
  current source, and lists, separately, `modified` (content changed), `missing`
  (deleted, or rules block markers gone), `unexpected` (an unmanaged file where the
  source wants one), and `obsolete` (managed paths the source no longer distributes)
  artifacts.

The exit code is nonzero for integrity drift or when the required integrity check is
unavailable: an unreadable or absent manifest or a legacy-only install.

The check never mutates installed content.

The script uses user-level directories, symlinks no content, and requires no
administrator rights. It also removes only legacy paths that earlier versions of this
repository managed.

### Release artifacts and trust model

The recommended installation no longer executes from mutable `main`. Pushing an
annotated `v*` tag triggers `.github/workflows/release.yml`, which runs the test suite,
then `release.py` builds `dist/personal-agent-config-<tag>.tar.gz` (via `git archive` at
the tagged commit) and `dist/SHA256SUMS`, and `gh release create` attaches both to the
GitHub release. A checked-out tag is immutable; the installer detects a fixed checkout
and skips `git pull`.

The checksum confirms that the downloaded archive matches the published artifact. It
does **not** protect against a compromised GitHub account, a malicious maintainer, or a
tampered release. Installations should pin an explicit tag, download only over HTTPS
from this repository, and review the script before running it.

Local development runs directly from a working `main` checkout: `python3
sync_ai_rules.py` uses that tree as its source and skips `git pull` when the tree has
local changes (or is checked out at a fixed revision), so rule edits can be installed
and verified before a tag is cut.

OpenCode V2 reads global rules from `~/.config/opencode/AGENTS.md`; its accepted but
inactive `instructions` setting is not a second rule source. Codex reads one
concatenated `~/.codex/AGENTS.md`; increase `project_doc_max_bytes` when the installer
reports truncation. Codex custom prompts are deprecated, but remain a compatibility
distribution target.

After changing `docs/`, `commands/`, `skills/`, or distribution behavior:

1. Run `python3 sync_ai_rules.py`.
2. Run `python3 sync_ai_rules.py --check` and require `integrity` status `ok`; the
   `repository` status is informational.
3. Resolve every validation or size warning, or report the unresolved blocker.
