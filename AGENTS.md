# Agent Guidelines for awesome-ai-prompts

This document provides instructions for agentic coding assistants operating in this repository. Adhere to these standards to ensure consistency across all AI prompts and meta-protocols.

## 1. Build, Lint, and Test Commands

Currently, this repository consists of Markdown documentation and prompt protocols. It does not use automated build or test pipelines. All "validation" is performed manually or through agent inspection.

### Quality Assurance Protocol
- **Markdown Linting:** 
  - Ensure all `.md` files adhere to standard GitHub Flavored Markdown (GFM).
  - Use one H1 header per file for the title.
  - Maintain a maximum line length of 120 characters for prose, where possible.
  - Use semantic line breaks (one line per sentence or clause) to make git diffs cleaner.
  - Ensure all lists are consistent (either all `*` or all `-`).
- **YAML Validation:** 
  - Files in the `commands/` directory MUST have valid YAML frontmatter.
  - The `description` field should be a single, high-impact sentence.
  - The `agent` field must be one of the specified sub-agent types.
- **Link Checking:** 
  - Ensure all internal links in `README.md` and `commands/` are functional.
  - Use relative paths for local files (e.g., `[label](commands/dev-reset.md)`).
  - Avoid absolute paths that include local directory structures (e.g., `/Users/...`).
- **Consistency Verification:**
  - Check that new prompts do not duplicate functionality of existing prompts.
  - Ensure that if a prompt is referenced by a command, that command exists and is documented.
- **Single File "Test":** 
  - To "test" a new prompt, perform a dry run of its instructions. 
  - Verify that constraints are mutually exclusive and collectively exhaustive (MECE).
  - Check that the prompt does not conflict with existing protocols like `dev-reset.md`.

## 2. Code Style & Standards

Since the "code" here consists of prompts, follow these structural and stylistic guidelines to maintain a high "signal-to-noise" ratio.

### Filenames and Structure
- **Naming:** Use kebab-case for all filenames (e.g., `prompt-engineering.md`).
- **Command Prefix:** Developer-focused meta-prompts in `commands/` should be prefixed with `dev-` (e.g., `dev-verimode.md`).
- **Asset Naming:** Images in `media/` should be lowercase and descriptive (e.g., `logo.svg`).
- **Directories:** 
  - `commands/`: Specific, actionable meta-protocols that an agent can "run".
  - `media/`: Images, icons, and visual assets.
  - Root: General lists, indices, and high-level documentation.

### YAML Frontmatter Schema
Every file in `commands/` MUST start with the following block:
```yaml
---
description: A formalized protocol for [specific task].
agent: [plan | execute | all]
---
```
- **description:** Explain the "why" and "what" of the protocol. It should be written in the third person.
- **agent:** Specify which sub-agent should trigger this prompt. This helps the orchestrator route the task correctly.

### Writing Style for Prompts
- **Imperative Voice:** Use strong, direct verbs. Start instructions with "STOP.", "Identify.", "Search.", or "Verify.".
- **formatting for Emphasis:** 
  - Use **Bold** for critical actions or "hard constraints".
  - Use `Code Blocks` for specific commands, JSON structures, or data models.
  - Use > Blockquotes for external quotes, source snippets, or "mental model" examples.
- **Hierarchical Organization:** 
  - Use H2 headers for major sections (e.g., "Protocol", "Constraints").
  - Use H3 headers for sub-steps or categorized rules.
  - Use numbered lists for sequential steps that must be followed in order.
  - Use bullet points for non-sequential constraints or checklists.

### Imports and References
- **Internal Links:** When one prompt references another, use the relative Markdown link. This creates a "web" of protocols.
- **External Links:** Always verify external URLs (e.g., in `README.md`) are current and relevant to the category. Use descriptive link text.

### Error Handling in Prompts
Prompt protocols should include self-correction mechanisms. If a process is likely to fail, stall, or loop, include a "Reset" or "Clarification" step.
- **Constraint Surfacing:** Prompt the user to list assumptions when progress stalls.
- **Uncertainty Declaration:** Require agents to flag unverified claims with `[UNVERIFIED]`.
- **Halt Conditions:** Clearly state when an agent should stop and wait for user input (e.g., "Wait for confirmation before proceeding").

## 3. Best Practices for New Protocols

When contributing new prompts to the `commands/` directory, adhere to the following meta-principles:

1. **Separation of Concerns:** Each prompt should solve exactly one problem. Avoid "Swiss Army Knife" prompts that try to handle too many edge cases at once.
2. **Minimalism:** Avoid "fluff" or conversational filler in the prompt text. Every word should contribute to the agent's behavior. If it doesn't change the output, remove it.
3. **Verification-First:** Any prompt dealing with technical implementation should mandate documentation lookups or code-base grepping before proposing solutions.
4. **Instructional Density:** Use whitespace to separate distinct ideas, but keep instructions compact.
5. **Idempotency:** A protocol should be repeatable. Running it twice should not result in conflicting state or "hallucination loops".

## 4. Communication Guidelines for Agents

When an agent is triggered by a protocol in this repository, its communication with the user should shift:
- **Tone:** Professional, objective, and slightly more rigid than standard chat.
- **Format:** Use structured responses (checklists, tables, bullet points) as defined in the protocol.
- **Transparency:** If a protocol requires an "Epistemic Reset", the agent must explicitly state it is performing a reset and follow the steps visibility.

## 5. Security & Safety

- **No Secrets:** Never include API keys, tokens, or personal identifiers in prompts or documentation.
- **Code Injection:** Ensure that instructions for generating code include safety checks (e.g., "Sanitize inputs", "Check for buffer overflows").
- **External Fetching:** Protocols that require `webfetch` or external API calls must include a warning to the user about data being sent to third parties.

## 6. Automated Rules
*(No Cursor rules in .cursor/rules/ or .cursorrules were found. No Copilot instructions in .github/copilot-instructions.md were found.)*

### Proactive Maintenance
Agents should proactively check for these files if they are added in the future. If rule files are created, they should be reconciled with this `AGENTS.md` to ensure a single source of truth. Updates to this document should be proposed if discrepancies arise.

## 7. Contribution Checklist

When adding a new prompt or updating an existing one, use this checklist to ensure compliance:

- [ ] Does the filename use kebab-case?
- [ ] If it's a command, does it have the `dev-` prefix?
- [ ] Does it contain valid YAML frontmatter with `description` and `agent`?
- [ ] Is the language imperative and direct?
- [ ] Are hard constraints clearly labeled and emphasized?
- [ ] Have you checked for overlapping functionality with existing prompts?
- [ ] Are all internal links relative and functional?
- [ ] Does it include an "escape hatch" or "reset" mechanism for failure states?

## 8. Versioning & Evolution

This repository is a living set of protocols. Agents and human developers should iterate on these instructions as AI models evolve. If a constraint in a protocol is consistently ignored or misinterpreted by state-of-the-art models, it should be refactored for better "instructional resonance."

### Updating this Guide
When updating `AGENTS.md`:
1.  **Analyze** the current friction points in the workflow.
2.  **Draft** specific, actionable rules to mitigate those points.
3.  **Validate** that new rules do not contradict the "Minimalism" mandate.
4.  **Commit** changes with a clear description of the "why" behind the refinement.

---
*This file is maintained by the AI agents and developers of the awesome-ai-prompts repository.*
