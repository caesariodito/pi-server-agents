# pi-server-agents

Portable Pi setup for a personal Linux VM, with optional daily coding workflow and Heeler mobile access over SSH to herdr-core. macOS installer paths are supported; fresh Linux VM verification remains required before production use.

## Install

Use a dedicated non-root user. Review installer before running:

```bash
curl -fsSLo /tmp/install-pi.sh https://raw.githubusercontent.com/caesariodito/pi-server-agents/main/install.sh
less /tmp/install-pi.sh
bash /tmp/install-pi.sh
```

Installer asks independently:

```text
Choose setup mode:
  1) Install/update missing setup
  2) Reinstall managed tools
  3) Cancel

Install daily coding workflow? [y/N]
Install optional qmd search tool? [y/N]
```

A noninteractive first run leaves optional features off. Enabling daily workflow persists across reruns; answering no does not uninstall it. qmd remains installed when declined later. Reinstall reruns selected managed installers without deleting runtime state. Root still requires typing `ROOT` through a terminal; avoid root for agent work.

### Unattended flags

```bash
export PI_SETUP_MODE=missing               # missing or reinstall
export PI_SETUP_DAILY_WORKFLOW=1          # 0 or 1
export PI_SETUP_QMD=0                     # optional
export NINEROUTER_URL="https://your-private-gateway.example"
read -rsp '9Router key: ' NINEROUTER_KEY; export NINEROUTER_KEY; echo
bash /tmp/install-pi.sh
unset NINEROUTER_KEY
```

No flags authorize Tailscale configuration, public binding, relay, pairing, or restarting Herdr. `localhost:20128` means the VM itself, not your Mac. An existing `~/.config/9router/env` is preserved, mode `600`. Process variables override file values individually. Credentials never belong in this repository.

## What installs

- Node.js 24 through nvm; Pi **1.4.0** for fresh/reinstall. Missing mode keeps compatible newer Pi, rejects older Pi with upgrade instructions.
- herdr-core **0.1.19** if missing. Existing compatible core is never automatically updated/restarted, even in reinstall mode. Legacy `herdr` is not installed or used.
- Existing base `pi-memory@0.4.2` declaration on fresh runtime. Existing settings/preferences/packages retained.
- Server-compatible gateway discovery with bounded timeout and default-model fallback. No imported machine-specific generated catalog.
- Existing server home instructions, including Docker layout and Homepage discovery policies.
- tmux configuration only if tmux already exists; installer never installs/upgrades tmux. Existing content preserved with one managed source line. Active tmux reload behavior retained.

Shared workflows install from an exact reviewed Git commit in `profiles/shared-skills.json`, using native Pi package resource filters. Base includes server-operations and shared gateway skills. Daily workflow adds pinned `rpiv-ask-user-question@2.12.0`, `rpiv-todo@2.12.0`, and `pi-web-access@0.45.0`, plus lifecycle, project-init, security-audit, frontend craft, decision-sheet, QA, optional review skills, and focused pstack-derived unslop/teach/architect/arena skills. Consequential work uses one independently authorized Herdr reviewer through independent-review after author verification; this is Cloudflare guidance-mode review, not full security audit. Exploration stays scoped, and human visuals are optional. Herdr agent skill remains separately reviewed/upstream-managed; it is not vendored here. No Mac browser profiles, credentials, caches, installed dependencies, or machine .NET instructions. HTML review tools require Python 3 when used; Mermaid remains a separately installed optional pinned dependency, never a base installer step. Full audits still require independent authorized agents and strict OS sandbox controls; installing the skill does not provision these.

Heeler uses SSH to herdr-core; no Ovis plugin, Bun prerequisite, HTTP listener or legacy Herdr installation. `PI_SETUP_OVIS=1` fails before any installation. Existing Ovis files/runtime remain untouched for deliberate retirement.

## Source and runtime layout

```text
~/.local/share/pi-server-agents/   # managed Git source, clean fast-forward only
~/.pi/agent/                      # runtime; PI_CODING_AGENT_DIR may override
  AGENTS.md                      # runtime guidance, not repo maintenance rules
  settings.json                  # preserved preferences + selected package pins
  extensions/                    # gateway integration
  skills/                        # remaining server-specific gateway chat reference
  git/                           # Pi-managed pinned shared skill package
  daily-skills/                  # legacy only; retained but no longer discovered
  auth.json, sessions/, ...      # private existing state, never copied to source
~/.config/9router/env             # canonical server credential file
```

Repository root `AGENTS.md` remains maintenance guidance for editing this source checkout. It is not copied into runtime. Do not manually clone this repository into `~/.pi/agent` for new installs.

### Existing install migration and rollback

Legacy installs may already have this Git checkout in `~/.pi/agent`. Installer creates a separate source checkout, preserves legacy `.git`, auth, sessions, caches, and unknown files, and backs up changed managed files before replacement. Only exact old repository gateway override is cleared, with backup; custom `models.json` overrides remain and produce a review warning. `AGENTS.override.md` remains untouched and overrides managed guidance; review warning before starting Pi.

Backups use `<file>.backup.<timestamp>`. Restore specific files from their backups to roll back settings/guidance; use previous source commit for code rollback. Never remove auth/session/state directories or reset legacy runtime Git checkout. Back up source and uncommitted project work independently; Herdr persistence is not a backup.

Source checkout with local edits stops update instead of resetting it. Keep experiments in a separate development checkout. Shared workflow changes belong in https://github.com/caesariodito/skills; verify/publish there, then bump exact commit in profiles/shared-skills.json. Do not copy skills or node_modules here. Old daily discovery path is removed without deleting files; exact former gateway copies move to retired-skills backups. Modified gateway copies block migration before managed writes for manual merge. Restore specific files/settings from backups for rollback.

## Herdr Core and Heeler

Installer does not start/restart core or configure network exposure. As the non-root user:

```bash
export PATH="$HOME/.local/bin:$PATH"
herdr-core server start
herdr-core server status
```

Heeler >=0.1.18: add Host manually, select **herdr-core**, use approved SSH identity and verify host fingerprint. OpenSSH stream-local forwarding must be permitted. Connecting does not start core. No legacy pairing/plugin commands. See [Heeler core guide](https://docs.heeler.bybee.dev/herdr-core).

Keep SSH access private/restricted. No Ovis port, relay or Tailscale Serve route is needed. Phone keys, pairing, notifications and optional host helper are separate choices. Never copy credentials into source.

Reboot startup needs explicitly approved per-user systemd setup and linger; `.infra` owns that host configuration. Verify reboot and reconnect before relying on it. Root-owned existing sessions are not automatically migrated.

## Validation

```bash
bash -n install.sh scripts/install-ovis.sh
node --test tests/*.test.mjs
git diff --check
```

Tests use temporary directories and fake tool responses; they do not install tools, download dependencies, touch real Herdr, or expose terminals. Optional tmux check uses isolated socket:

```bash
tmux -L pi-config-check -f <(printf '%s\n' 'set -g default-terminal "screen-256color"'; cat home/tmux.conf) new-session -d -s validate
tmux -L pi-config-check kill-session -t validate
```

### VM acceptance checklist — not yet verified

1. Fresh non-root Linux install, base-only and daily workflow options; rerun without duplicate config or private-state loss.
2. Gateway reachable from VM; Pi starts with selected model inside herdr-core.
3. herdr-core health passes; Heeler connects over private SSH with verified host key.
4. Pi custom question/task dialogs and approvals render correctly; terminal fallback works.
5. Phone/SSH disconnect and reconnect preserve ongoing agent work.
6. Supported startup procedure survives reboot with correct user, HOME, PATH, and state.
7. Project backups and restore verified. Keep unresolved failures explicit.

## Source tracking

Track portable settings, source references, templates, scripts, tests, and documentation. Never track auth, environment secrets, sessions, logs, caches, generated model catalogs, or installed package directories. Historical model catalogs and Linux x64 binaries were removed from current source; Git history retains them. Do not clone this repository into ~/.pi/agent. Legacy GitHub .pi repository is unnecessary; local ~/.pi remains runtime state.

Canonical consolidation spec: https://github.com/caesariodito/skills/blob/main/docs/specs/workflow-consolidation/spec.md. No VPS deployment authorized by publishing these changes.
