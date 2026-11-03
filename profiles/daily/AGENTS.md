
## Daily workflow routing

| Trigger | Skill or rule |
|---|---|
| Multi-step work | Todo, one task in progress; ask structured questions only for blockers/consequential decisions. |
| Consequential change | engineering-lifecycle owns exploration, human decisions, approved canonical spec, build/verify, independent review and fix/recheck. Small low-risk work stays direct. |
| Design exploration | architect; arena for real alternatives. Bounded scratch prototypes and safe local checks allowed within scope, no production/external writes or new dependencies. Herdr candidates require explicit grant. |
| Understanding | teach for overview/pipeline/phase/data drill-down and accessible generative UI when available; unslop preserves meaning and user tone. |
| Completion | independent-review after author verification: one explicitly authorized Herdr reviewer covers security guidance, intent, sufficiency, simplicity and documented direction. Missing required review stays blocked unless explicitly waived; no recursive review. |
| Onboarding/frontend | project-init when local guidance missing, create only with approval; emil-design-eng within existing components/tokens/accessibility. |
| Specs/artifacts | Repository convention or docs/specs/<feature>/spec.md; derived evidence in ignored .scratch/<task>/. Outside repository ask directory. HTML optional. |
| Security | security-audit guidance by default; full audit and target execution retain separate authorization, independent roles, output confirmation and all upstream OS sandbox requirements. |

Use advertised skill paths; Herdr skill separately reviewed/upstream-installed. Missing skill never authorizes invented commands or hidden agents. Pi packages do not auto-load shared AGENTS.md; this installer-composed routing is explicit server adapter.
