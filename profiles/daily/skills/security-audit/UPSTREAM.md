# Upstream provenance and Pi integration

- Source: https://github.com/cloudflare/security-audit-skill
- Commit: `c1c8a8c1471069fb0e188eeaff69b8e8db6564a8`
- Imported: complete `skills/security-audit/` plus repository MIT `LICENSE`, unchanged.
- Updates: review a specific upstream commit, replace vendored files, rerun both validator test suites, and update this record. No automatic updates or installer execution.

Pi routing lives in `~/.pi/agent/AGENTS.md`, not patched upstream files. Guidance works in current session. Full audits require explicit Herdr delegation, independent contexts, a confirmed output directory, and all upstream sandbox controls for target-code execution. Neither skill installation nor an audit request authorizes spawning agents. Missing independence blocks full audit; missing sandbox controls block target execution. Never claim independent verification from sequential self-review.
