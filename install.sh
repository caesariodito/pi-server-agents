#!/usr/bin/env bash
# curl -fsSL https://raw.githubusercontent.com/caesariodito/pi-server-agents/main/install.sh | bash
set -Eeuo pipefail

readonly PI_VERSION="0.87.1"
readonly NODE_VERSION="24"
readonly NVM_INSTALLER_VERSION="v0.40.3"
readonly REPO_URL="https://github.com/caesariodito/pi-server-agents"
readonly HERDR_INSTALLER_URL="https://herdr.dev/install.sh"
readonly AGENT_DIR="${PI_CODING_AGENT_DIR:-$HOME/.pi/agent}"
readonly ROUTER_ENV="$HOME/.config/9router/env"
readonly TMUX_CONFIG="$HOME/.config/tmux/pi-server-agents.conf"

log() { printf '\n==> %s\n' "$*"; }
die() { printf 'Error: %s\n' "$*" >&2; exit 1; }

choose_setup_mode() {
  local tty=/dev/tty choice
  case "${PI_SETUP_MODE:-}" in
    missing|reinstall) SETUP_MODE="$PI_SETUP_MODE"; return ;;
    "") ;;
    *) die "PI_SETUP_MODE must be 'missing' or 'reinstall'." ;;
  esac

  if [[ ! -r "$tty" || ! -w "$tty" ]]; then
    SETUP_MODE=missing
    return
  fi

  printf '%s\n' \
    'Choose setup mode:' \
    '  1) Install/update missing setup (recommended)' \
    '  2) Reinstall all managed tools and configuration' \
    '  3) Cancel' > "$tty"
  read -r -p 'Selection [1]: ' choice < "$tty"
  case "${choice:-1}" in
    1) SETUP_MODE=missing ;;
    2) SETUP_MODE=reinstall ;;
    3) die "Setup cancelled." ;;
    *) die "Invalid setup mode." ;;
  esac
}

confirm_root_install() {
  local tty=/dev/tty answer
  [[ ${EUID:-$(id -u)} -eq 0 ]] || return 0
  [[ -r "$tty" && -w "$tty" ]] || die "Root installation requires an interactive terminal."
  printf '%s\n' \
    'WARNING: Pi will run with unrestricted machine access.' \
    'Configuration and Node.js will be installed under /root.' > "$tty"
  read -r -p "Type ROOT to continue: " answer < "$tty"
  [[ "$answer" == "ROOT" ]] || die "Root installation cancelled."
}

confirm_root_install
choose_setup_mode
readonly SETUP_MODE
printf 'Setup mode: %s\n' "$SETUP_MODE"
command -v curl >/dev/null || die "curl is required."
command -v git >/dev/null || die "git is required."

install_nvm() {
  local installer
  installer="$(mktemp)"
  curl -fsSL "https://raw.githubusercontent.com/nvm-sh/nvm/$NVM_INSTALLER_VERSION/install.sh" -o "$installer"
  PROFILE=/dev/null bash "$installer"
  rm -f "$installer"
}

ensure_nvm_profile() {
  local profile="$HOME/.profile"
  touch "$profile"
  grep -Fq 'export NVM_DIR="$HOME/.nvm"' "$profile" || cat >> "$profile" <<'EOF'

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
EOF
}

export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
if [[ "$SETUP_MODE" == reinstall || ! -s "$NVM_DIR/nvm.sh" ]]; then
  log "Installing nvm $NVM_INSTALLER_VERSION"
  install_nvm
else
  log "Keeping existing nvm"
fi
ensure_nvm_profile
# shellcheck source=/dev/null
. "$NVM_DIR/nvm.sh"

if [[ "$SETUP_MODE" == reinstall || "$(nvm version "$NODE_VERSION")" == N/A ]]; then
  log "Installing Node.js $NODE_VERSION"
  nvm install "$NODE_VERSION"
else
  log "Keeping existing Node.js $NODE_VERSION"
fi
nvm alias default "$NODE_VERSION" >/dev/null
nvm use "$NODE_VERSION" >/dev/null

if [[ "$SETUP_MODE" == reinstall ]] || ! command -v pi >/dev/null; then
  log "Installing Pi $PI_VERSION"
  npm install -g --ignore-scripts "@earendil-works/pi-coding-agent@$PI_VERSION"
else
  log "Keeping existing Pi"
fi

if [[ "$SETUP_MODE" == reinstall ]] || ! command -v qmd >/dev/null; then
  log "Installing qmd"
  npm install -g @tobilu/qmd
else
  log "Keeping existing qmd"
fi

export PATH="$HOME/.local/bin:$PATH"
if [[ "$SETUP_MODE" == reinstall ]] || ! command -v herdr >/dev/null; then
  log "Installing Herdr"
  herdr_installer="$(mktemp)"
  curl -fsSL "$HERDR_INSTALLER_URL" -o "$herdr_installer"
  HERDR_INSTALL_DIR="$HOME/.local/bin" sh "$herdr_installer"
  rm -f "$herdr_installer"
else
  log "Keeping existing Herdr"
fi
grep -Fq 'export PATH="$HOME/.local/bin:$PATH"' "$HOME/.profile" || cat >> "$HOME/.profile" <<'EOF'

export PATH="$HOME/.local/bin:$PATH"
EOF

log "Installing Pi configuration"
mkdir -p "$(dirname "$AGENT_DIR")"
if [[ -d "$AGENT_DIR/.git" ]]; then
  origin="$(git -C "$AGENT_DIR" remote get-url origin 2>/dev/null || true)"
  if [[ "$origin" == "$REPO_URL" || "$origin" == "$REPO_URL.git" ]]; then
    git -C "$AGENT_DIR" pull --ff-only
  else
    backup="$AGENT_DIR.backup.$(date +%Y%m%d-%H%M%S)"
    mv "$AGENT_DIR" "$backup"
    printf 'Existing agent directory backed up to %s\n' "$backup"
    git clone "$REPO_URL" "$AGENT_DIR"
  fi
elif [[ -e "$AGENT_DIR" ]]; then
  backup="$AGENT_DIR.backup.$(date +%Y%m%d-%H%M%S)"
  mv "$AGENT_DIR" "$backup"
  printf 'Existing agent directory backed up to %s\n' "$backup"
  git clone "$REPO_URL" "$AGENT_DIR"
else
  git clone "$REPO_URL" "$AGENT_DIR"
fi

install_home_agents() {
  local source="$AGENT_DIR/home/AGENTS.md" target="$HOME/AGENTS.md" backup
  [[ -f "$source" ]] || die "Missing home AGENTS.md template: $source"
  if [[ -e "$target" ]] && ! cmp -s "$source" "$target"; then
    backup="$target.backup.$(date +%Y%m%d-%H%M%S)"
    cp -a "$target" "$backup"
    printf 'Existing home AGENTS.md backed up to %s\n' "$backup"
  fi
  cmp -s "$source" "$target" 2>/dev/null || install -m 644 "$source" "$target"
}

log "Installing home AGENTS.md"
install_home_agents

install_tmux_config() {
  local source="$AGENT_DIR/home/tmux.conf" target="$HOME/.tmux.conf" backup terminal popup=false validate_socket validation_output
  [[ -f "$source" ]] || die "Missing tmux template: $source"
  if ! command -v tmux >/dev/null; then
    printf 'tmux not installed; skipping tmux configuration.\n'
    return
  fi

  mkdir -p "$(dirname "$TMUX_CONFIG")"
  if infocmp tmux-256color >/dev/null 2>&1; then
    terminal=tmux-256color
  else
    terminal=screen-256color
  fi
  {
    printf 'set -g default-terminal "%s"\n' "$terminal"
    if [[ "$terminal" == tmux-256color ]] && infocmp xterm-256color >/dev/null 2>&1; then
      printf 'set -as terminal-features ",xterm-256color:RGB"\n'
    fi
    cat "$source"
    if command -v fzf >/dev/null && tmux list-commands 2>/dev/null | grep -q '^display-popup '; then
      printf '%s\n' 'bind s display-popup -E -w 70% -h 60% "session=\$(tmux list-sessions -F '\''#{session_name}'\'' | fzf --reverse); [ -n \"\$session\" ] && tmux switch-client -t \"\$session\""'
      popup=true
    fi
  } > "$TMUX_CONFIG.tmp"
  if [[ -e "$TMUX_CONFIG" ]] && ! cmp -s "$TMUX_CONFIG.tmp" "$TMUX_CONFIG"; then
    backup="$TMUX_CONFIG.backup.$(date +%Y%m%d-%H%M%S)"
    cp -a "$TMUX_CONFIG" "$backup"
    printf 'Existing managed tmux config backed up to %s\n' "$backup"
  fi
  mv "$TMUX_CONFIG.tmp" "$TMUX_CONFIG"
  chmod 644 "$TMUX_CONFIG"

  if [[ ! -e "$target" ]]; then
    printf 'source-file "%s"\n' "$TMUX_CONFIG" > "$target"
  elif ! grep -Fqx "source-file \"$TMUX_CONFIG\"" "$target"; then
    backup="$target.backup.$(date +%Y%m%d-%H%M%S)"
    cp -a "$target" "$backup"
    printf '\nsource-file "%s"\n' "$TMUX_CONFIG" >> "$target"
    printf 'Existing tmux config backed up to %s\n' "$backup"
  fi

  validate_socket="pi-setup-validate-$$"
  validation_output="$(mktemp)"
  if ! tmux -L "$validate_socket" -f "$target" new-session -d -s validate 2> "$validation_output" || [[ -s "$validation_output" ]]; then
    tmux -L "$validate_socket" kill-session -t validate >/dev/null 2>&1 || true
    printf 'tmux validation failed:\n' >&2
    cat "$validation_output" >&2
    rm -f "$validation_output"
    return 1
  fi
  rm -f "$validation_output"
  tmux -L "$validate_socket" kill-session -t validate
  if tmux list-sessions >/dev/null 2>&1; then
    tmux source-file "$target"
  fi
  printf 'tmux config installed: %s (%s, fzf picker: %s)\n' "$TMUX_CONFIG" "$terminal" "$popup"
}

log "Configuring tmux"
install_tmux_config

configure_router() {
  local tty=/dev/tty url key

  if [[ -f "$ROUTER_ENV" ]]; then
    chmod 600 "$ROUTER_ENV"
    printf 'Keeping existing %s\n' "$ROUTER_ENV"
    return
  fi

  url="${NINEROUTER_URL:-}"
  key="${NINEROUTER_KEY:-}"
  if [[ -z "$url" ]]; then
    [[ -r "$tty" && -w "$tty" ]] || die "No terminal available. Export NINEROUTER_URL before running installer."
    read -r -p "9Router URL [http://localhost:20128]: " url < "$tty"
    url="${url:-http://localhost:20128}"
  fi
  url="${url%/}"

  if [[ -z "$key" && -r "$tty" && -w "$tty" ]]; then
    read -r -s -p "9Router key (leave empty when auth is disabled): " key < "$tty"
    printf '\n' > "$tty"
  fi

  mkdir -p "$(dirname "$ROUTER_ENV")"
  umask 077
  {
    printf 'export NINEROUTER_URL=%q\n' "$url"
    [[ -z "$key" ]] || printf 'export NINEROUTER_KEY=%q\n' "$key"
  } > "$ROUTER_ENV"
  chmod 600 "$ROUTER_ENV"
}

log "Configuring 9Router"
configure_router

log "Installing configured Pi packages"
pi update --extensions

log "Verifying installation"
printf 'Node.js: %s\n' "$(node --version)"
printf 'Pi:      %s\n' "$(pi --version)"
printf 'qmd:     %s\n' "$(qmd --version 2>/dev/null || printf 'installed')"
printf 'Herdr:   %s\n' "$(herdr --version)"
printf '\nSetup complete. Run: cd /path/to/project && pi\n'
