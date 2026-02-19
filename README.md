<div align="center">
	<div>
		<img width="500" height="350" src="media/logo.svg" alt="Awesome">
		<h1>AI Prompts</h1>
	</div>
</div>

# General Meta-Prompts

| Name | Description | Prompt |
| --- | --- | --- |
| Epistemic reset | Forces separation of fact from inference | “What do you actually know vs. assume here?” |
| Assumption audit | Surfaces hidden priors before they compound | “List every assumption embedded in your last response.” |
| Steelman the opposite | Breaks confirmation bias | “What’s the strongest case against your current approach?” |
| Constraint surfacing | Catches over-engineering and scope creep | “What are you optimizing for, and did anyone ask you to?” |
| Uncertainty declaration | Prevents hallucination laundering | “Rate your confidence per claim and flag what you’d need to verify.” |

# Coding-Specific

## opencode commands

- [dev-reset.md](commands/dev-reset.md) - A formalized epistemic reset protocol
- [dev-verimode.md](commands/dev-verimode.md) - A verification-first, documentation-grounded response protocol
