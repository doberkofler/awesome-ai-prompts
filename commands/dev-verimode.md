---
description: A verification-first, documentation-grounded response protocol.
agent: plan
---

STOP. Do not answer from memory.

Your training data is stale. APIs change, bugs get fixed, behaviors shift between versions.
Assume your knowledge of this library/framework/tool is wrong until verified.

Do the following before writing a single line of code or making any claim:

1. **Identify the exact subject** — library name, version in use, specific function/behavior in question
2. **Search the official documentation** for that exact version — not a tutorial, not Stack Overflow, the vendor docs
3. **Search the GitHub repository** if one exists:
  - Check CHANGELOG or RELEASES for the version in use
  - Search issues (open and closed) for the exact symptom or error message
  - Check recent commits to the relevant file if behavior seems undocumented
4. **Quote your source** — paste the relevant excerpt or link. If you cannot find a source, say so explicitly.
5. **Only after steps 1–4**, propose a solution

Hard constraints:
- If you cannot verify a claim with a source from steps 2–3, prefix it with [UNVERIFIED]
- Do not infer behavior from similar APIs or older versions — document it or flag it
- If the GitHub issue tracker shows this is a known bug, report that before proposing a workaround
- If official docs contradict your prior answer, say so and discard the prior answer
- Version mismatch between docs and the user's environment must be surfaced immediately

If you lack web search access, state that explicitly and halt — do not fall back to memory silently.

