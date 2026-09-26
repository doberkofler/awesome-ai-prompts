<div align="center">
	<div>
		<img width="500" height="350" src="media/logo.svg" alt="Awesome">
		<h1 style="color: #494368; font-family: Futura, 'Inter', system-ui, -apple-system, sans-serif; font-size: 3.8em; font-weight: 400; letter-spacing: -0.02em; margin-top: -60px;">ai prompts</h1>
	</div>
</div>

## Install / update the AI rules

Distributes the rules in [`docs/`](docs/), plus [`commands/`](commands/) and
[`skills/`](skills/), to your local agent configurations:

| Agent | Rules | Commands | Skills |
| --- | --- | --- | --- |
| opencode | `~/.config/opencode/AGENTS.md` | `~/.config/opencode/commands/` | reads `~/.agents/skills/` |
| Claude Code | `~/.claude/CLAUDE.md` | `~/.claude/commands/` | `~/.claude/skills/` |
| Codex | `~/.codex/AGENTS.md` | `~/.codex/prompts/` | `~/.agents/skills/` |
| Pi | `~/.pi/agent/AGENTS.md` | `~/.pi/agent/prompts/` | reads `~/.agents/skills/` |

Rules are concatenated into each agent's native single-file location. Skills are
written to only **two** directories — `~/.agents/skills/` (read by opencode,
Codex, and Pi) and `~/.claude/skills/` (read by Claude Code) — because each
harness scans several skills directories at once and duplicate skill names across
them collide.

Requires `git` and Python 3.

### One-liner (recommended)

macOS / Linux:

```bash
curl -fsSL https://raw.githubusercontent.com/doberkofler/awesome-ai-prompts/main/sync_ai_rules.py | python3 -
```

Windows (PowerShell):

```powershell
irm https://raw.githubusercontent.com/doberkofler/awesome-ai-prompts/main/sync_ai_rules.py | python -
```

### Or clone

```bash
git clone https://github.com/doberkofler/awesome-ai-prompts.git ~/.ai-rules/src
python3 ~/.ai-rules/src/sync_ai_rules.py
```

### Update and verify

```bash
python3 ~/.ai-rules/src/sync_ai_rules.py            # pull latest and distribute
python3 ~/.ai-rules/src/sync_ai_rules.py --check    # is the install current?
```

Optional alias: `alias ai-rules='python3 ~/.ai-rules/src/sync_ai_rules.py'`.

### Notes

- No symlinks and no admin rights; only the user-level directories above are written.
- Codex reads a single concatenated `~/.codex/AGENTS.md`. If the script prints a size
  warning, add the suggested `project_doc_max_bytes` line to `~/.codex/config.toml`.
- Codex custom prompts (`~/.codex/prompts/`) are deprecated by Codex; skills are the
  durable mechanism and are distributed to all agents.
- opencode reads rules natively from `~/.config/opencode/AGENTS.md`. If your
  `~/.config/opencode/opencode.jsonc` still lists `docs/*.md` under `instructions`,
  remove that entry — otherwise the rules load twice.
- Skills removed from `skills/` are pruned from both skills directories on sync. The
  script also removes the legacy `~/.config/opencode/docs/`, `~/.config/opencode/skills/`,
  `~/.claude/rules/`, and `~/.pi/agent/skills/` directories it created previously.

## General Meta-Prompts

| Name | Description | Prompt |
| --- | --- | --- |
| Epistemic reset | Forces separation of fact from inference | “What do you actually know vs. assume here?” |
| Assumption audit | Surfaces hidden priors before they compound | “List every assumption embedded in your last response.” |
| Steelman the opposite | Breaks confirmation bias | “What’s the strongest case against your current approach?” |
| Constraint surfacing | Catches over-engineering and scope creep | “What are you optimizing for, and did anyone ask you to?” |
| Uncertainty declaration | Prevents hallucination laundering | “Rate your confidence per claim and flag what you’d need to verify.” |

## Coding-Specific

### opencode - commands

- [dev-reset.md](commands/dev-reset.md) - A formalized epistemic reset protocol
- [dev-verimode.md](commands/dev-verimode.md) - A verification-first, documentation-grounded response protocol

### opencode - resources
- [awesome-opencode](https://github.com/awesome-opencode/awesome-opencode) - awesome opencode

## Prompt engineering

- [impeccable](https://github.com/pbakaus/impeccable) - The vocabulary you didn't know you needed. Curated anti-patterns for impeccable frontend design.
- [prompts.chat](https://prompts.chat/prompts) - Share, discover, and collect prompts from the community
- [awesome-prompts](https://github.com/ai-boost/awesome-prompts) - This repository contains a curated list of awesome prompts
- [chatgpt-prompts](https://www.llmbundle.com/prompts) - ChatGPT Prompts Library
- [ai-prompts-for-developers](https://www.flashprompt.app/blog/ai-prompts-for-developers) - AI Prompts for Developers
- [awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules) - Configuration files with custom rules and behaviors
- [cursor-rules](https://cursor.directory/rules) Cursor directory rules
- [cursor-rules-typescript](https://stevekinney.com/writing/cursor-rules-typescript) - Cursor Rules for TypeScript Engineers
