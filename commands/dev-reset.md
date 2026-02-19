---
description: A formalized epistemic reset protocol that halts iterative drift, surfaces flawed assumptions, enforces requirement re-grounding, and biases toward minimal viable correctness before proceeding.
agent: plan
---

STOP. Do not continue your current approach.

You are looping or have hit a wall. This is a signal your mental model is wrong, not that you need to try harder.

Do the following in order:

1. **State what you were trying to do** (one sentence, outcome only — not steps)
2. **State what assumption you made that is now suspect** — be specific, not vague
3. **State what evidence contradicts that assumption**
4. **Discard your current approach entirely.** Do not patch it.
5. **Re-read the original requirement** as if you are seeing it for the first time
6. **Identify the simplest possible solution** that satisfies only what was explicitly asked — no more
7. **Name one thing you were over-engineering or misunderstanding**
8. **Now propose a new approach** — one paragraph, no code yet — and wait for confirmation before proceeding

Constraints:
- Do not reference your previous attempts in the new approach
- Do not explain why the old approach was close — it wasn't, that's why you stopped
- If you are uncertain about a requirement, ask exactly one clarifying question before proposing anything
