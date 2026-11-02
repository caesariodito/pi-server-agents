# Portable daily coding workflow and optional Ovis

## Goal and approved scope

User approved refreshing pi-server-agents into a portable VM setup with an optional daily coding workflow and a separate optional Ovis integration. Existing missing/reinstall setup modes remain independent from these choices. This is repository implementation, not permission to install tools on this Mac, deploy a VM, expose terminals, or start delegated agents.

Baseline: local main at `87150990bee2f62c0cc0120a9b892b5076d31f7b`, clean before this spec. Read-only fetch found origin/main at `7692020c72049206e8617838f80077580db8035b`; implementation must fast-forward first to retain upstream setup-mode and tmux changes. No pre-existing local edits.

## Evidence

- install.sh currently clones source directly into `${PI_CODING_AGENT_DIR:-$HOME/.pi/agent}`, pulls there, pins Pi 0.87.1, and installs qmd unconditionally. origin/main adds missing/reinstall choices and tmux configuration.
- Root AGENTS.md contains repository commit/push instructions. Pi 1.4.0 configuration documentation confirms agent-directory AGENTS.md becomes global context; maintenance instructions must not be installed globally.
- Local daily setup uses Pi 1.4.0 and pinned question/todo packages 2.12.0 plus pi-web-access 0.45.0. Server currently declares pi-memory 0.4.2; retain this existing base dependency rather than silently remove it.
- Existing extension reads shell-format credentials from ~/.config/9router/env, but a partially populated process environment suppresses file fallback entirely, and gateway discovery failure aborts extension startup. Fix these failure paths within server integration.
- Ovis INSTALL.md requires Herdr >=0.9.0 and Bun >=1.4.0, recommends Herdr plugin installation, defaults to 127.0.0.1:7317, and separates phone network setup. Latest observed Ovis release: v0.4.21; verify supported pinned plugin installation syntax before implementation.
- Existing home/AGENTS.md contains server Docker/Homepage policies. Preserve them; do not copy Mac machine instructions.
- Local skills contain machine-specific absolute references and large node_modules trees. Copy only selected source/support files, adapt references to installed locations, retain licenses/provenance, and exclude caches/generated output. Do not vendor installed dependencies.

## Proposed decisions

### 1. Separate installer source from agent runtime

Use `$HOME/.local/share/pi-server-agents` for managed source checkout; retain `${PI_CODING_AGENT_DIR:-$HOME/.pi/agent}` for runtime. Keep repository-maintenance AGENTS.md in source; install a separate runtime guidance template. Source updates must be clean fast-forward operations; stop on dirty/conflicting source instead of resetting user work.

Alternative: continue cloning into agent runtime and add AGENTS.override.md. Smaller initial diff, but runtime settings/private files remain mixed with mutable source, profile installation dirties tracked files, and future pulls can conflict. Source/runtime separation is preferred for reliable reruns.

Migration: detect legacy runtime checkout without deleting/moving its auth, sessions, caches, or unknown files. Create separate source checkout, back up each changed managed runtime file, and install from source. Leave legacy Git metadata untouched; stop using it for runtime updates. Document optional cleanup separately, never remove it automatically.

### 2. Independent opt-ins

- Keep PI_SETUP_MODE=missing|reinstall.
- Add `Install daily coding workflow? [y/N]`, configurable through PI_SETUP_DAILY_WORKFLOW=0|1.
- Add `Install Ovis for mobile access? [y/N]`, configurable through PI_SETUP_OVIS=0|1. Explain that selection authorizes installation of missing Bun and Ovis plugin, not network exposure.
- Validate flags before mutations. First unattended run defaults to neither optional feature. Record enabled daily profile so ordinary reruns do not silently remove it; declining installation is not uninstall authorization.
- qmd becomes optional, not a prerequisite of daily/mobile coding. Keep an existing qmd installation; do not remove it.
- Do not configure Tailscale Serve, public listeners, relay, firewall, token, or device pairing automatically. Print separate documented phone setup instructions and explicit exposure warning.

### 3. Portable daily resources

Keep optional resources outside default discovery directories until enabled. Install selected lifecycle, project-init, Herdr, Cloudflare security-audit, frontend craft, and existing review skills with their required source/support files. No Mac paths, browser profiles, credentials, caches, or node_modules. Preserve optional HTML review behavior; no browser-service dependency for ordinary coding.

Use pinned package declarations for question/todo 2.12.0 and pi-web-access 0.45.0; preserve existing pi-memory and user packages. Merge package entries by package identity, back up changed settings, and write valid JSON atomically. Preserve unrelated preferences. Missing mode must not silently downgrade a newer Pi; require compatible Pi >=1.4.0 and report inability to upgrade rather than claim success. Pin 1.4.0 for fresh installs and explicit managed reinstall.

Runtime guidance keeps security/correctness precedence, small diffs, focused tests, repository-local instructions, explicit approval boundaries, lifecycle only for consequential changes, and opt-in Herdr delegation. Full security audits still require genuinely independent agents and all upstream execution sandbox controls. Source-only guidance must disclose missing validation. Confirm output directory before audit artifacts.

### 4. Server gateway integration

Retain ~/.config/9router/env as canonical file source. Each process variable overrides its corresponding file value independently. Do not create a second secret store. Export resolved values to Pi process for web-access tools without printing values. Validate HTTP(S) gateway URL, bound discovery timeout, reject malformed model payloads, and keep existing static provider configuration usable when discovery is unavailable. Do not copy machine-specific model catalogs; static fallback must not embed another machine's gateway address.

### 5. Ovis lifecycle

Install through supported Herdr plugin mechanism after version checks, using a tested release where CLI supports it. Validate Bun and Herdr minima before plugin build; report actionable errors without stopping/restarting existing Herdr server. Keep Ovis listener loopback-only, detect conflicting configuration, and never replace existing secrets/config. Start only via plugin actions when running Herdr is available; otherwise report pending startup accurately. Check local health endpoint when started. Do not equate queued action acknowledgement with healthy service.

Keep reboot/service setup and private phone access documented follow-up unless existing supported mechanisms can be reused without changing host exposure or privileged service configuration. Service PATH must include installed user tools.

## Acceptance criteria

1. Existing missing/reinstall mode and tmux behavior retained from origin/main; optional flags reject invalid values before installation side effects.
2. Daily profile off leaves base package set intact; enabling adds exact pinned packages and portable skills; reruns are idempotent and preserve user settings, secrets, sessions, and unknown files.
3. Repository maintenance instructions never become global runtime context on fresh or migrated installs.
4. Legacy runtime migration creates backups before changing managed files and never resets/deletes user work.
5. Fresh Pi pinned to 1.4.0; incompatible existing Pi detected. Herdr/Bun minima checked when Ovis selected; qmd not mandatory.
6. Ovis selection is independent of daily profile and never exposes network access, changes Tailscale, prints secrets, or restarts Herdr.
7. Gateway partial-environment fallback, invalid URLs, discovery errors, and malformed payloads have focused checks; no unrelated live gateway requests in tests.
8. README documents options, unattended flags, source/runtime layout, migration/rollback, non-root recommendation, private phone setup, and VM acceptance checklist.
9. Automated installer tests use isolated temporary HOME and stubbed tools/network; never execute downloaded installers, alter current Pi installation, control real Herdr, or expose ports. Skill references and pinned provenance checked.

## Verification

- `bash -n install.sh` and any new shell scripts.
- One stdlib-based runnable installer regression test covering flags, combinations, reruns, preservation, backup/migration, version failures, source-update refusal, and Ovis no-exposure behavior.
- Focused Node checks for extension credential/discovery behavior using fake responses and temporary credential file.
- Existing tmux isolated-socket validation from README; do not touch current sessions.
- Upstream Cloudflare validator tests if vendored; check local skill links and absence of Mac paths/missing support files.
- `git diff --check`; inspect `git status --short --ignored` and secret ignore rules before any commit.
- Fresh Linux VM smoke test is required before claiming deploy-ready: install as non-root, rerun, reach configured gateway, start Pi in Herdr, connect phone privately, render custom questions/approvals, disconnect/reconnect, verify persistence and reboot procedure. No VM access supplied; leave this acceptance stage explicitly pending.

## Failure and rollback

Fail closed on invalid flags, incompatible tool versions, dirty source checkout, malformed settings, and network-exposure conflicts. Preserve earlier backups and report partial installation accurately. No uninstall from declining an option. Rollback restores specific timestamped managed-file backups and previous source ref; never delete session/auth/state directories or stop active agents implicitly.

## Dry-run review

Standards pass: source/runtime collision is a material migration concern; proposed separation prevents update/profile writes from overwriting source or leaking maintenance rules. Ovis control surface needs explicit loopback and private-access boundaries. Existing gateway partial-variable behavior needs regression coverage.

Scope pass: approved recommendation covers daily profile and Ovis; source/runtime migration is newly identified implementation detail with meaningful compatibility impact. Obtain confirmation of this spec before implementation rather than silently restructuring existing installs. No implementation code changed.

## Approval and stage

Recommendation and source/runtime separation approved by user through structured confirmation. Repository implementation complete; local verification passed. Source baseline fast-forwarded to origin/main `7692020c72049206e8617838f80077580db8035b`. Fresh Linux VM/mobile acceptance remains pending; setup is not claimed deploy-ready. No commit/push or VM deployment performed.

## Implementation and local verification evidence

- Source/runtime separation, independent daily/Ovis/qmd flags, persistent daily enablement, per-file backups, curated portable source skills, and pinned packages implemented.
- Settings preserve preferences and unrelated packages. Legacy exact repository gateway override migrates with backup; custom overrides and AGENTS.override.md remain with warnings. No auth/session/unknown-file removal or legacy Git reset.
- 9Router resolves environment overrides per variable, rejects unsafe URL forms without leaking supplied values, exports resolved credentials for web tools, validates model catalog, and retains selected default model when discovery fails. Existing streaming implementation unchanged.
- Ovis first install pins v0.4.21 through documented `--ref`; missing Bun installs 1.4.0. Version checks, loopback configuration checks, no automatic network setup/server restart, plugin-state validation, and health checks implemented. Existing plugin remains untouched.
- `bash -n install.sh scripts/install-ovis.sh`: passed.
- `node --test tests/*.test.mjs profiles/daily/skills/security-audit/*.test.cjs profiles/daily/skills/implementation-review/scripts/preview.test.mjs`: 76 passed, zero failed/skipped. Includes all four daily/Ovis combinations through full installer fixture, reruns, dirty-source refusal, legacy state preservation, malformed settings, invalid flags, old Herdr/Bun refusal, public-bind refusal, gateway failure and partial-env fallback.
- Both Python review-builder smoke tests passed. Isolated `tmux -L pi-config-check` config startup/cleanup passed; current sessions untouched.
- Skill entrypoint/frontmatter/local-link/portable-path checks passed. Generated template example links are intentionally output-document references, not installed source files. No node_modules copied. Optional Mermaid absence now tested as supported warning/source fallback.
- `git diff --check` passed; secret/session/scratch/node_modules ignore checks passed. ShellCheck unavailable, not run. Installer fixtures stub downloaded tools and remove only their temporary HOME directories; no actual host installers or external terminal control executed.

## Review disposition

Standards review found and fixed: macOS ancestor /var symlink false-positive in managed-file protection; malformed plugin list triggering install instead of failing; legacy static endpoint overriding dynamic gateway; custom agent directory skill references; optional Mermaid test assuming installed dependency; discovery fallback ignoring selected default model; raw invalid URL error potentially exposing supplied URL. Re-review and local tests passed.

Spec review: local criteria covered by runnable checks and inspection. Fresh source clone/download/install behavior, Linux service PATH/reboot persistence, real Pi custom dialog rendering in Ovis, phone reconnect, actual gateway/provider health, and backup/restore still require VM acceptance. No standalone service provisioning, relay, Tailscale Serve, tokens, VM deployment, or independent audit agents configured. No claim of exhaustive provider compatibility or operational full-audit capability.

## Remaining handoff

Provide VM OS/architecture and authorized access or run README VM checklist manually. Code must be published or copied to VM before remote main installer can use these uncommitted changes. Do not run unchanged remote installer expecting this feature set. Confirm commit/push or VM deployment separately before delivery to remote main.
