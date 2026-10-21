# pi-server-agents

Versioned Pi agent setup for this server.

Tracked:
- `settings.json`
- `models.json`
- `models-store.json`
- `skills/`
- `home/AGENTS.md` cross-server home instructions
- `home/tmux.conf` managed tmux configuration
- `.gitignore`

Not tracked:
- `auth.json` secrets
- `sessions/` chat history
- package/cache dirs reproducible from settings

## Install on a new server

Requires Linux/macOS, `curl`, and `git`:

```bash
curl -fsSL https://raw.githubusercontent.com/caesariodito/pi-server-agents/main/install.sh | bash
```

Installer supports normal users and root. Root installation prints a warning and requires typing `ROOT` through `/dev/tty`; Pi then has unrestricted machine access, and files are installed under `/root`.

Installer prompts for one of two modes through `/dev/tty`:

1. **Install/update missing setup** keeps installed tools and fills missing setup.
2. **Reinstall all** reruns every managed tool installer without deleting user data.

Installer manages Node.js 24 through nvm, Pi 0.87.1, qmd, Herdr, this configuration, configured Pi packages, generic `home/AGENTS.md` at `~/AGENTS.md`, and tmux configuration when tmux is already installed. It does not install or upgrade tmux. Existing `~/.config/9router/env` remains unchanged. Existing non-repository agent directories and changed home files are timestamp-backed up.

Tmux settings live at `~/.config/tmux/pi-server-agents.conf`. Installer preserves existing `~/.tmux.conf` content and adds one `source-file` line, backing up changed config first. It chooses `tmux-256color` when terminfo exists, otherwise `screen-256color`; RGB and optional fzf session picker are capability-gated. Active tmux servers reload without killing sessions. Clipboard uses tmux/OSC 52 and still depends on client terminal and SSH path support.

Safer review-first form:

```bash
curl -fsSLo /tmp/install-pi.sh https://raw.githubusercontent.com/caesariodito/pi-server-agents/main/install.sh
less /tmp/install-pi.sh
bash /tmp/install-pi.sh
```

For unattended installation, choose `missing` or `reinstall` and provide environment variables without placing secrets directly in shell history:

```bash
export PI_SETUP_MODE=missing
export NINEROUTER_URL="http://localhost:20128"
read -rsp '9Router key: ' NINEROUTER_KEY; export NINEROUTER_KEY; echo
curl -fsSL https://raw.githubusercontent.com/caesariodito/pi-server-agents/main/install.sh | bash
unset NINEROUTER_KEY
```

To rerun every managed installer:

```bash
curl -fsSL https://raw.githubusercontent.com/caesariodito/pi-server-agents/main/install.sh | PI_SETUP_MODE=reinstall bash
```

## Validate installer changes

```bash
bash -n install.sh
tmux -L pi-config-check -f <(printf '%s\n' 'set -g default-terminal "screen-256color"'; cat home/tmux.conf) new-session -d -s validate
tmux -L pi-config-check kill-session -t validate
git diff --check
```

## Manual restore

If `~/.pi/agent` does not exist:
```bash
mkdir -p ~/.pi
git clone https://github.com/caesariodito/pi-server-agents ~/.pi/agent
```

If `~/.pi/agent` already exists, back it up first:
```bash
mkdir -p ~/.pi
mv ~/.pi/agent ~/.pi/agent.backup.$(date +%Y%m%d-%H%M%S)
git clone https://github.com/caesariodito/pi-server-agents ~/.pi/agent
```

If you need old auth secrets, copy them from backup:
```bash
ls -ld ~/.pi/agent.backup.*
cp ~/.pi/agent.backup.YYYYMMDD-HHMMSS/auth.json ~/.pi/agent/auth.json
```

## Environment example

Add secrets to your shell profile, not this repo:
```bash
# 9Router
export NINEROUTER_URL="http://localhost:20128"
export NINEROUTER_KEY="sk-..."

# Pi models.json currently uses baseUrl "http://localhost:20128/v1".
# Keep NINEROUTER_URL equivalent to that host/port on each server.

# Optional Pi process config
export PI_OFFLINE=0
export PI_SKIP_VERSION_CHECK=0
```

If 9Router auth is disabled, omit `NINEROUTER_KEY`.

Do not commit `auth.json`, `.env`, or `sessions/`.
