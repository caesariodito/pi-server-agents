
## Daily coding workflow

- Use todo for multi-step work; keep one task in progress and finish only after relevant checks pass. Use ask_user_question for blocking ambiguity or consequential choices, not routine implementation details.
- Before consequential contract, persistent-data, architecture, trust-boundary, concurrency, or recovery changes, load `@DAILY_SKILLS@/engineering-lifecycle/SKILL.md`. Small low-risk edits stay direct. Duration alone requires tracking, not documents.
- Keep canonical specs in existing repository convention, otherwise docs/specs/<feature>/spec.md. HTML review is optional, requested or clearly useful for complex review; load implementation-review/technical-spec when needed.
- Work in current session. Do not spawn child agents unless user explicitly requests Herdr delegation. Load `@DAILY_SKILLS@/herdr/SKILL.md` before Herdr control; require HERDR_ENV=1. Follow supervisor continuation, isolated worktree, handoff, and verification rules.
- At first repository task, inspect local AGENTS/CLAUDE instructions. If absent, suggest project-init once; create guidance only with approval. Use project-init language references when needed.
- For frontend work, reuse existing components/tokens and accessibility patterns; load emil-design-eng. Do not add design dependencies without approval.
- For security questions/reviews, load `@DAILY_SKILLS@/security-audit/SKILL.md`; guidance mode by default. Full audits require explicit independent Herdr agents and confirmed output directory. No sequential self-review substituted for independence. Target execution requires every upstream OS sandbox control; otherwise source-only guidance with validation blockers. Never probe live systems.
- Generated reviews/evidence belong in ignored .scratch/<task>/ within target repository. Outside repositories, ask for output directory. Never write secrets into artifacts.
