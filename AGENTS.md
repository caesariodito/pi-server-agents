# Repository guidance

Portable Pi installer and runtime composition, not global agent workflow authority. Shared workflows live in https://github.com/caesariodito/skills; profiles/shared-skills.json pins reviewed source and selected resources.

- Read install.sh, scripts/configure-runtime.mjs, tests, and README before changes. Keep source checkout separate from private runtime.
- Prefer Pi package references over vendored skills/packages. Update shared source first, verify it, then bump exact commit here. Preserve licenses/provenance upstream.
- Never track credentials, sessions, logs, caches, generated model catalogs, installed packages, or scratch output. Review git status --short --ignored before commits.
- Preserve user settings, unknown runtime files, auth/session state, and host-specific ~/AGENTS.md. Changed managed files need backups. Never run real installers or manage live services during fixture tests.
- Keep host policy separate from server-operations procedures; Homepage labels apply only where read-only discovery is configured.
- Commit/push only when explicitly authorized. Use Conventional Commits. Do not infer permission to deploy from permission to publish source.

Checks:

```sh
bash -n install.sh scripts/install-ovis.sh
node --test tests/*.test.mjs
git diff --check
```

Fresh VM, real gateway, Ovis phone/reconnect and reboot acceptance require separately authorized environment; fixture tests do not prove deployment readiness.
