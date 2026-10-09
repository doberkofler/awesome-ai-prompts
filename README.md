<div align="center">
	<div>
		<img width="500" height="350" src="media/logo.svg" alt="Awesome">
		<h1 style="color: #494368; font-family: Futura, 'Inter', system-ui, -apple-system, sans-serif; font-size: 3.8em; font-weight: 400; letter-spacing: -0.02em; margin-top: -60px;">ai prompts</h1>
	</div>
</div>

## What this is

A personal installer that distributes my agent rules, commands, and skills to the
local configuration of every supported agent. It is a personal policy repository,
not a curated public list: the content encodes my preferences and is published so
that it can be installed and updated with one command.

- **Audience:** primarily me; usable by anyone who wants opinionated, versioned
  agent rules.
- **Scope:** local distribution only. The installer never fetches rules from
  elsewhere; it copies the content committed in this repository.
- **Status:** personal policy. External material is adapted selectively and
  recorded in [`PROVENANCE.md`](PROVENANCE.md).

## Install / update the AI rules

Distributes the rules in [`docs/`](docs/), plus [`commands/`](commands/) and
[`skills/`](skills/), to your local agent configurations:

| Agent | Rules | Commands | Skills |
| --- | --- | --- | --- |
| OpenCode V2 | `~/.config/opencode/AGENTS.md` | `~/.config/opencode/commands/` | reads `~/.agents/skills/` |
| Claude Code | `~/.claude/CLAUDE.md` | `~/.claude/commands/` | `~/.claude/skills/` |
| Codex | `~/.codex/AGENTS.md` | `~/.codex/prompts/` | `~/.agents/skills/` |
| Pi | `~/.pi/agent/AGENTS.md` | `~/.pi/agent/prompts/` | reads `~/.agents/skills/` |

Rules are concatenated into each agent's native single-file location. Skills are
written to only **two** directories — `~/.agents/skills/` (read by OpenCode V2,
Codex, and Pi) and `~/.claude/skills/` (read by Claude Code) — because each
harness scans several skills directories at once and duplicate skill names across
them collide. OpenCode V2 officially supports `~/.agents/skills/` as a global
compatibility source; using it avoids a second copy in its native skills directory.

Requires `git` and Python 3.

### Release install (recommended)

Every release publishes a source archive and its SHA-256 checksum under
[Releases](https://github.com/doberkofler/awesome-ai-prompts/releases). Set
`VERSION` to the release tag you want (for example `v1.0.0`), then download,
verify the checksum, and extract.

macOS / Linux:

```bash
VERSION=v1.0.0
BASE="https://github.com/doberkofler/awesome-ai-prompts/releases/download/${VERSION}"
TMP="$(mktemp -d)"
curl -fsSL -o "$TMP/awesome-ai-prompts-${VERSION}.tar.gz" "$BASE/awesome-ai-prompts-${VERSION}.tar.gz"
curl -fsSL -o "$TMP/SHA256SUMS" "$BASE/SHA256SUMS"
( cd "$TMP" && sha256sum -c SHA256SUMS )      # macOS: shasum -a 256 -c SHA256SUMS
mkdir -p ~/.ai-rules/src
tar -xzf "$TMP/awesome-ai-prompts-${VERSION}.tar.gz" -C ~/.ai-rules/src --strip-components=1
python3 ~/.ai-rules/src/sync_ai_rules.py
```

Windows (PowerShell):

```powershell
$Version = "v1.0.0"
$Base = "https://github.com/doberkofler/awesome-ai-prompts/releases/download/$Version"
$Tmp = Join-Path $env:TEMP "ai-rules-$Version"
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
Invoke-WebRequest "$Base/awesome-ai-prompts-$Version.tar.gz" -OutFile "$Tmp/awesome-ai-prompts-$Version.tar.gz"
Invoke-WebRequest "$Base/SHA256SUMS" -OutFile "$Tmp/SHA256SUMS"
Get-Content "$Tmp/SHA256SUMS"   # confirm it matches Get-FileHash -Algorithm SHA256
New-Item -ItemType Directory -Force -Path "$HOME/.ai-rules/src" | Out-Null
tar -xzf "$Tmp/awesome-ai-prompts-$Version.tar.gz" -C "$HOME/.ai-rules/src" --strip-components=1
python "$HOME/.ai-rules/src/sync_ai_rules.py"
```

### Or clone at a pinned tag

```bash
VERSION=v1.0.0
git clone --branch "$VERSION" --depth 1 https://github.com/doberkofler/awesome-ai-prompts.git ~/.ai-rules/src
python3 ~/.ai-rules/src/sync_ai_rules.py
```

### Local development

If you are developing the rules rather than consuming them, work in a `main`
checkout and run the installer directly against your working tree:

```bash
git clone https://github.com/doberkofler/awesome-ai-prompts.git
cd awesome-ai-prompts
python3 sync_ai_rules.py --dry-run   # preview the plan
python3 sync_ai_rules.py             # install the working-tree content
```

When the script runs from a checkout it uses that directory as its source. It
skips `git pull` when the checkout has local changes (and when it is checked out
at a fixed revision), so you can edit `docs/`, `commands/`, and `skills/` and
re-run to install your edits.

### Update and verify

```bash
python3 ~/.ai-rules/src/sync_ai_rules.py            # install the checked-out content
python3 ~/.ai-rules/src/sync_ai_rules.py --check    # revision status and content integrity
```

`--check` reports two independent statuses: the installed revision against
upstream, and every installed file against its recorded SHA-256 (`modified`,
`missing`, `unexpected`, `obsolete`). It exits nonzero on content drift or when
the manifest cannot be read; the repository status is informational, since a
release archive has no git metadata. To update, install a newer release tag, or
`git -C ~/.ai-rules/src fetch --tags && git -C ~/.ai-rules/src checkout "$VERSION"`.

Optional alias: `alias ai-rules='python3 ~/.ai-rules/src/sync_ai_rules.py'`.

### Trust and update model

Installing runs code from this repository. Releases are built by CI from an
annotated `v*` tag and published with a SHA-256 checksum. Verifying the checksum
confirms the downloaded archive matches the published artifact; it does **not**
protect against a compromised GitHub account, a malicious maintainer, or a
tampered release. Pin an explicit `VERSION`, download only over HTTPS from this
repository, and review the script before running it.

### Notes

Maintainers cut a release by pushing a `v*` tag; CI runs `release.py`, which
builds `dist/awesome-ai-prompts-<tag>.tar.gz` and `dist/SHA256SUMS` and attaches
both to the GitHub release.

See [`PROVENANCE.md`](PROVENANCE.md) for content origins, intentional adaptations,
upstream maintenance, distribution behavior, and the release process.

## What gets installed

### Rules (`docs/`)

Concatenated in filename order into each agent's global rules file.

| Document | Focus |
| --- | --- |
| [general-guidelines.md](docs/general-guidelines.md) | Persona, clarification protocol, verbosity, validation sources |
| [lint-rules.md](docs/lint-rules.md) | ESLint configuration and rule philosophy |
| [mui-rules.md](docs/mui-rules.md) | Material UI usage, theming, and color schemes |
| [react-rules.md](docs/react-rules.md) | React component and hook design |
| [sql-plsql-rules.md](docs/sql-plsql-rules.md) | SQL and PL/SQL coding standards |
| [typescript-rules.md](docs/typescript-rules.md) | TypeScript best practices and Zod validation |

### Commands (`commands/`)

OpenCode-style command protocols, distributed to every supported agent's command
directory.

| Command | Purpose |
| --- | --- |
| [dev-decompose.md](commands/dev-decompose.md) | Decomposes a researched plan into wave-ordered, self-contained task specs |
| [dev-find-reinventions.md](commands/dev-find-reinventions.md) | Finds internal duplication and reinvented builtin/framework/npm functionality |
| [dev-reset.md](commands/dev-reset.md) | A formalized epistemic reset protocol |
| [dev-verimode.md](commands/dev-verimode.md) | A verification-first, documentation-grounded response protocol |

### Skills (`skills/`)

Each skill is a directory containing a `SKILL.md`; the installer copies the whole
directory.

| Skill | Purpose |
| --- | --- |
| [code-review](skills/code-review/SKILL.md) | Independent review of a branch, commit range, or worktree against repository standards |
| [codebase-design](skills/codebase-design/SKILL.md) | Vocabulary for designing deep modules and choosing seams |
| [diagnosing-bugs](skills/diagnosing-bugs/SKILL.md) | Diagnosis loop for hard bugs and performance regressions |
| [domain-modeling](skills/domain-modeling/SKILL.md) | Build and sharpen a project's domain model and ADRs |
| [grill-me](skills/grill-me/SKILL.md) | Relentless interview to sharpen a plan or design |
| [grill-with-docs](skills/grill-with-docs/SKILL.md) | Relentless interview that also writes ADRs and a glossary |
| [grilling](skills/grilling/SKILL.md) | Grill a plan, decision, or idea to stress-test it |
| [handoff](skills/handoff/SKILL.md) | Compact a conversation into a handoff document |
| [oracle-local](skills/oracle-local/SKILL.md) | Query, test, and validate against a local Oracle database |
| [prototype](skills/prototype/SKILL.md) | Build a throwaway prototype to answer a design question |
| [research](skills/research/SKILL.md) | Investigate a topic against primary sources and capture the findings |
| [tdd](skills/tdd/SKILL.md) | Test-driven development and red-green-refactor |
| [wait-what](skills/wait-what/SKILL.md) | Re-pitch the previous message when it did not land |
| [writing-for-agents](skills/writing-for-agents/SKILL.md) | Write skills, `AGENTS.md`, and `CLAUDE.md` for agents |

## General meta-prompts

Short prompts used while working with an agent. Not distributed; kept here for
reference.

| Name | Description | Prompt |
| --- | --- | --- |
| Epistemic reset | Forces separation of fact from inference | “What do you actually know vs. assume here?” |
| Assumption audit | Surfaces hidden priors before they compound | “List every assumption embedded in your last response.” |
| Steelman the opposite | Breaks confirmation bias | “What’s the strongest case against your current approach?” |
| Constraint surfacing | Catches over-engineering and scope creep | “What are you optimizing for, and did anyone ask you to?” |
| Uncertainty declaration | Prevents hallucination laundering | “Rate your confidence per claim and flag what you’d need to verify.” |

## External resources

Inclusion criteria: the link must be a general reference or collection for a topic
covered by `docs/`, `commands/`, or `skills/`, and it must be non-commercial in
intent. One-off blog posts, SEO prompt dumps, and personal marketing pages are
excluded.

### OpenCode

- [awesome-opencode](https://github.com/awesome-opencode/awesome-opencode) - a curated list of OpenCode resources.

### Prompt engineering

- [prompts.chat](https://prompts.chat/prompts) - share, discover, and collect prompts.
- [awesome-prompts](https://github.com/ai-boost/awesome-prompts) - a curated list of prompts.

### Cursor rules

- [awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules) - configuration files with custom rules and behaviors.
- [cursor-rules](https://cursor.directory/rules) - Cursor directory rules.

### Frontend design

- [impeccable](https://github.com/pbakaus/impeccable) - curated anti-patterns for impeccable frontend design.
