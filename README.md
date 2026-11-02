# pi-server-agents

Portable Pi setup for a personal Linux VM, with optional daily coding workflow and optional Ovis mobile client. macOS installer paths are supported; fresh Linux VM verification remains required before production use.

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
Install Ovis for mobile access (includes missing Bun; no network exposure)? [y/N]
Install optional qmd search tool? [y/N]
```

A noninteractive first run leaves optional features off. Enabling daily workflow persists across reruns; answering no does not uninstall it. Ovis and qmd also remain installed when declined later. Reinstall reruns selected managed installers without deleting runtime state. Root still requires typing `ROOT` through a terminal; avoid root for agent work.

### Unattended flags

```bash
export PI_SETUP_MODE=missing               # missing or reinstall
export PI_SETUP_DAILY_WORKFLOW=1          # 0 or 1
export PI_SETUP_OVIS=1                    # independent from daily workflow
export PI_SETUP_QMD=0                     # optional
export NINEROUTER_URL="https://your-private-gateway.example"
read -rsp '9Router key: ' NINEROUTER_KEY; export NINEROUTER_KEY; echo
bash /tmp/install-pi.sh
unset NINEROUTER_KEY
```

No flags authorize Tailscale configuration, public binding, relay, pairing, or restarting Herdr. `localhost:20128` means the VM itself, not your Mac. An existing `~/.config/9router/env` is preserved, mode `600`. Process variables override file values individually. Credentials never belong in this repository.

## What installs

- Node.js 24 through nvm; Pi **1.4.0** for fresh/reinstall. Missing mode keeps compatible newer Pi, rejects older Pi with upgrade instructions.
- Herdr if missing; optional Ovis requires Herdr >=0.9.0. Existing Herdr is not silently upgraded or restarted in missing mode.
- Existing base `pi-memory@0.4.2` declaration on fresh runtime. Existing settings/preferences/packages retained.
- Server-compatible gateway discovery with bounded timeout and default-model fallback. No imported machine-specific generated catalog.
- Existing server home instructions, including Docker layout and Homepage discovery policies.
- tmux configuration only if tmux already exists; installer never installs/upgrades tmux. Existing content preserved with one managed source line. Active tmux reload behavior retained.

Daily workflow adds pinned `rpiv-ask-user-question@2.12.0`, `rpiv-todo@2.12.0`, and `pi-web-access@0.45.0`, plus curated lifecycle, project-init, Herdr, security-audit, frontend craft, and optional review skills. No Mac browser profiles, credentials, caches, installed dependencies, or machine .NET instructions. HTML review tools require Python 3 when used; Mermaid remains a separately installed optional pinned dependency, never a base installer step. Full audits still require independent authorized agents and strict OS sandbox controls; installing the skill does not provision these.

Ovis uses Herdr plugin **v0.4.21** on first installation and installs missing Bun **1.4.0**. Existing Bun must be >=1.4.0. Existing Ovis checkout/config remains user-owned; installer does not replace or update it. Public/custom listener or relay configuration stops automatic setup for manual review. Fresh listener is `127.0.0.1:7317`.

## Source and runtime layout

```text
~/.local/share/pi-server-agents/   # managed Git source, clean fast-forward only
~/.pi/agent/                      # runtime; PI_CODING_AGENT_DIR may override
  AGENTS.md                      # runtime guidance, not repo maintenance rules
  settings.json                  # preserved preferences + selected package pins
  extensions/                    # gateway integration
  skills/                        # base gateway skills
  daily-skills/                  # optional curated workflow
  auth.json, sessions/, ...      # private existing state, never copied to source
~/.config/9router/env             # canonical server credential file
```

Repository root `AGENTS.md` remains maintenance guidance for editing this source checkout. It is not copied into runtime. Do not manually clone this repository into `~/.pi/agent` for new installs.

### Existing install migration and rollback

Legacy installs may already have this Git checkout in `~/.pi/agent`. Installer creates a separate source checkout, preserves legacy `.git`, auth, sessions, caches, and unknown files, and backs up changed managed files before replacement. Only exact old repository gateway override is cleared, with backup; custom `models.json` overrides remain and produce a review warning. `AGENTS.override.md` remains untouched and overrides managed guidance; review warning before starting Pi.

Backups use `<file>.backup.<timestamp>`. Restore specific files from their backups to roll back settings/guidance; use previous source commit for code rollback. Never remove auth/session/state directories or reset legacy runtime Git checkout. Back up source and uncommitted project work independently; Herdr persistence is not a backup.

Source checkout with local edits stops update instead of resetting it. Keep experiments in a separate development checkout. Changes to optional profile skill sources belong under `profiles/daily/skills`; do not copy `node_modules`.

## Herdr and Ovis startup

Installer never starts or restarts Herdr server. If absent, Ovis install reports startup pending. Start Herdr as the same non-root user with its tool PATH available:

```bash
export PATH="$HOME/.bun/bin:$HOME/.local/bin:$PATH"
# Load nvm in this shell if Pi is installed there.
herdr
```

Then use another terminal/pane:

```bash
herdr plugin action invoke devswha.ovis.start
curl -fsS http://127.0.0.1:7317/api/health
```

An action acknowledgement is not a health check. Expect JSON `ok:true` plus Herdr details. Do not use `herdr server stop` to fix Ovis. Inspect plugin logs instead. Bun must be on the environment PATH of the Herdr server, not merely a later client shell.

Persistent agent sessions should survive SSH disconnects; verify with your installed Herdr. Reboot startup is deliberately not installed as a privileged service here. Configure supported per-user service startup separately, with correct HOME/PATH and explicit authorization for linger/service changes. Verify reboot behavior before relying on unattended VM work.

## Private phone access — separate authorization

**Ovis can control terminals. Keep port 7317 off the public Internet. Network access must be explicitly approved and protected before enabling it.**

Recommended: Tailscale on VM and phone, HTTPS Serve to loopback, access restricted to intended devices/logins. With permission to change Tailscale Serve configuration:

```bash
tailscale serve --bg --https=443 http://127.0.0.1:7317
```

Inspect existing Serve configuration first; do not overwrite another service's route. Open the resulting HTTPS address on phone. Follow [Ovis phone setup and access policy](https://github.com/devswha/ovis/blob/v0.4.21/INSTALL.md#5-optional-phone-or-remote-access), including device pairing where required. Tokens belong only in private plugin config, never logs or source. Do not disable authentication to solve connection problems. Do not enable Ovis relay implicitly.

## Validation

```bash
bash -n install.sh scripts/install-ovis.sh
node --test tests/*.test.mjs
node --test profiles/daily/skills/security-audit/*.test.cjs
git diff --check
```

Tests use temporary directories and fake tool responses; they do not install tools, download dependencies, touch real Herdr, or expose terminals. Optional tmux check uses isolated socket:

```bash
tmux -L pi-config-check -f <(printf '%s\n' 'set -g default-terminal "screen-256color"'; cat home/tmux.conf) new-session -d -s validate
tmux -L pi-config-check kill-session -t validate
```

### VM acceptance checklist — not yet verified

1. Fresh non-root Linux install, base-only and daily+Ovis options; rerun without duplicate config or private-state loss.
2. Gateway reachable from VM; Pi starts with selected model inside Herdr.
3. Ovis health passes; phone connects over restricted private HTTPS.
4. Pi custom question/task dialogs and approvals render correctly; terminal fallback works.
5. Phone/SSH disconnect and reconnect preserve ongoing agent work.
6. Supported startup procedure survives reboot with correct user, HOME, PATH, and state.
7. Project backups and restore verified. Keep unresolved failures explicit.

## Source tracking

Track portable settings, source skills, templates, scripts, tests, and documentation. Never track auth, environment secrets, sessions, logs, caches, generated model catalogs, or installed package directories. Historical `models.json`, `models-store.json`, and Linux x64 `bin/` artifacts are retained for compatibility but are **not installed** into new runtime.
