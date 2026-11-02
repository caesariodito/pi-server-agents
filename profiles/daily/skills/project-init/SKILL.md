---
name: project-init
description: Inspect a repository and draft concise repository-local AGENTS.md guidance. Use when a Git repository lacks local agent instructions, when onboarding a codebase, or when the user asks to initialize project guidance or engineering conventions.
---

# Project initialization

Create durable repository guidance from evidence, not generic doctrine.

## 1. Establish scope

1. Resolve repository root with `git rev-parse --show-toplevel`.
2. Search from repository root toward current working directory for `AGENTS.override.md`, `AGENTS.md`, `AGENTS.MD`, `CLAUDE.md`, and `CLAUDE.MD`.
3. If repository-local guidance exists, offer to audit or improve it instead of creating a competing file.
4. Read relevant parent context, but treat machine-level and ancestor-home files as environment guidance rather than repository policy.

Complete when target repository and applicable context files are known.

## 2. Gather evidence

Inspect only files needed to establish:

- build, test, lint, format, type-check, migration, and run commands
- implementation languages and supported runtime versions
- source and test layout
- module or architectural boundaries visible in code
- CI checks and release constraints
- formatter, linter, compiler, and package-manager configuration
- generated files, vendored code, secrets, deployment state, or destructive operations needing protection

Use manifests, lockfiles, scripts, CI, config, and code as sources of truth. Do not copy values that remain easy to discover unless naming them prevents a common mistake.

For each dominant implementation language, read matching file under `references/`. Load only relevant references. Repository evidence overrides generic language guidance.

Complete when every proposed instruction has repository evidence or guards a universal engineering risk.

## 3. Draft one local file

Default target: `<repository-root>/AGENTS.md`.

Keep draft roughly 30–80 lines and organize only applicable sections:

```markdown
# Repository Guidance

## Commands
## Architecture
## Implementation Rules
## Testing and Verification
## Safety
```

Draft rules:

- State exact commands, paths, ownership boundaries, and completion checks.
- Explain non-obvious constraints and reasons.
- Separate mandatory rules from preferences.
- Prefer existing repository vocabulary.
- Keep each rule in one authoritative place.
- Omit generic slogans such as “write clean code,” “follow SOLID,” or “use best practices.”
- Avoid restating dependency versions, scripts, or settings already obvious from nearby files.
- Link a deeper document only when a clear trigger tells the agent when to read it.
- Preserve human editability; no generated markers or required generator.

Complete when draft is concise, evidence-backed, and contains no speculative architecture.

## 4. Request approval

Show proposed file or concise summary of its rules and ask user to approve creation. Do not create or replace repository guidance without approval. Call out conflicts with existing conventions.

Complete when user approves exact direction.

## 5. Write and verify

1. Write approved repository-local file.
2. Re-read it from repository root and check every command and path against repository state.
3. Run cheapest relevant non-destructive validation, such as config parsing or command discovery. Do not run builds or tests solely because guidance names them unless user requested repository validation.
4. Report file path, evidence used, checks run, and any unresolved uncertainty.

Complete when file exists, references valid repository facts, and verification has no unresolved error.
