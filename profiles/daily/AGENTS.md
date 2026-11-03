
## Daily coding workflow

- Use todo for multi-step work, one task in progress; ask structured questions for blocking ambiguity, not ordinary implementation choices.
- Load installed `engineering-lifecycle` before consequential contract, data, architecture, trust-boundary, concurrency, or recovery changes. Small low-risk edits stay direct; duration alone does not require documents.
- Canonical specs follow repository convention, otherwise docs/specs/<feature>/spec.md. Review HTML/decision sheets are optional. Artifacts belong in ignored .scratch/<task>/; outside repositories ask for output directory.
- Inspect repository-local AGENTS/CLAUDE guidance first. If absent, suggest project-init once; create guidance only with approval. Reuse its language references when needed.
- Frontend work reuses existing components/tokens and accessibility patterns; load emil-design-eng when relevant.
- Security questions load security-audit in guidance mode. Full audits require explicitly authorized independent agents and confirmed output directory; target execution requires every upstream OS sandbox control. Otherwise source-only guidance, never full-audit claims or live probes.
- Skills load from advertised locations, not fixed runtime paths. Herdr skill is upstream-managed, separately reviewed/installed when needed; its absence never authorizes guessing commands or spawning agents.
