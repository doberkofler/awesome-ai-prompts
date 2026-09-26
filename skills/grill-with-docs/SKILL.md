---
name: grill-with-docs
description: A relentless interview to sharpen a plan or design, which also maintains CONTEXT.md and ADRs inline as decisions crystallize.
disable-model-invocation: true
---

Call the Skill tool with "grilling" to run the interview.

As decisions crystallize, maintain the project's documentation inline — do not batch it up:

- **`CONTEXT.md`** — the project's glossary of domain terms, and nothing else. When the user uses a term that conflicts with the existing language, call it out. When a fuzzy term is sharpened, update the glossary right there. Follow [`CONTEXT-FORMAT.md`](CONTEXT-FORMAT.md).
- **ADRs** — offer one only when the decision is hard to reverse, surprising without context, and the result of a real trade-off. Follow [`ADR-FORMAT.md`](ADR-FORMAT.md).

Create files lazily — only when there is something to write. `CONTEXT.md` is a glossary: keep implementation details, specs, and scratch notes out of it.
