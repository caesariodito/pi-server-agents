#!/usr/bin/env bash
# curl -fsSL https://raw.githubusercontent.com/caesariodito/pi-server-agents/main/install.sh | bash
set -Eeuo pipefail

readonly PI_VERSION="1.4.0"
readonly OVIS_VERSION="v0.4.21"
readonly NODE_VERSION="24"
readonly NVM_INSTALLER_VERSION="v0.40.3"
readonly REPO_URL="https://github.com/caesariodito/pi-server-agents"
readonly HERDR_INSTALLER_URL="https://herdr.dev/install.sh"
readonly AGENT_DIR="${PI_CODING_AGENT_DIR:-$HOME/.pi/agent}"
readonly SOURCE_DIR="$HOME/.local/share/pi-server-agents"
readonly ROUTER_ENV="$HOME/.config/9router/env"
export PI_CODING_AGENT_DIR="$AGENT_DIR"
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

  if ! ( : <> "$tty" ) 2>/dev/null; then
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
  ( : <> "$tty" ) 2>/dev/null || die "Root installation requires an interactive terminal."
  printf '%s\n' \
    'WARNING: Pi will run with unrestricted machine access.' \
    'Configuration and Node.js will be installed under /root.' > "$tty"
  read -r -p "Type ROOT to continue: " answer < "$tty"
  [[ "$answer" == "ROOT" ]] || die "Root installation cancelled."
}

choose_feature() {
  local name="$1" prompt="$2" value="${!1:-}" answer
  case "$value" in
    0|1) ;;
    '')
      value=0
      if ( : <> /dev/tty ) 2>/dev/null; then
        read -r -p "$prompt [y/N] " answer < /dev/tty
        case "$answer" in y|Y|yes|YES) value=1 ;; esac
      fi ;;
    *) die "$name must be 0 or 1." ;;
  esac
  printf -v "$name" '%s' "$value"
}

# Validate flags before even root confirmation or tool installation.
for flag in PI_SETUP_DAILY_WORKFLOW PI_SETUP_OVIS PI_SETUP_QMD; do
  case "${!flag:-}" in ''|0|1) ;; *) die "$flag must be 0 or 1." ;; esac
done
case "${PI_SETUP_MODE:-}" in ''|missing|reinstall) ;; *) die "PI_SETUP_MODE must be 'missing' or 'reinstall'." ;; esac
confirm_root_install
choose_setup_mode
choose_feature PI_SETUP_DAILY_WORKFLOW 'Install daily coding workflow?'
choose_feature PI_SETUP_OVIS 'Install Ovis for mobile access (includes missing Bun and apt unzip; no network exposure)?'
choose_feature PI_SETUP_QMD 'Install optional qmd search tool?'
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

version_at_least() {
  node -e 'const parse=s=>{const m=s.match(/(?:^|\s|v)(\d+)\.(\d+)\.(\d+)(?:\s|$)/);if(!m)process.exit(2);return m.slice(1).map(Number)};const a=parse(process.argv[1]),b=parse(process.argv[2]);for(let i=0;i<3;i++){if(a[i]>b[i])process.exit(0);if(a[i]<b[i])process.exit(1)}' "$1" "$2"
}

if [[ "$SETUP_MODE" == reinstall ]] || ! command -v pi >/dev/null; then
  log "Installing Pi $PI_VERSION"
  npm install -g --ignore-scripts "@earendil-works/pi-coding-agent@$PI_VERSION"
else
  version_at_least "$(pi --version)" "$PI_VERSION" || die "Existing Pi must be >= $PI_VERSION. Upgrade explicitly or choose reinstall."
  log "Keeping existing compatible Pi"
fi

if [[ "$PI_SETUP_QMD" == 1 ]] && { [[ "$SETUP_MODE" == reinstall ]] || ! command -v qmd >/dev/null; }; then
  log "Installing qmd"
  npm install -g @tobilu/qmd
else
  log "Leaving optional qmd unchanged"
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

log "Updating installer source (separate from Pi runtime)"
[[ "$SOURCE_DIR" != "$AGENT_DIR" ]] || die "Source and runtime directories must differ."
mkdir -p "$(dirname "$SOURCE_DIR")"
if [[ -d "$SOURCE_DIR/.git" ]]; then
  origin="$(git -C "$SOURCE_DIR" remote get-url origin)"
  [[ "$origin" == "$REPO_URL" || "$origin" == "$REPO_URL.git" ]] || die "Unexpected source repository: $SOURCE_DIR"
  [[ -z "$(git -C "$SOURCE_DIR" status --porcelain)" ]] || die "Source checkout has local changes; preserve them before updating: $SOURCE_DIR"
  git -C "$SOURCE_DIR" pull --ff-only
elif [[ -e "$SOURCE_DIR" ]]; then
  die "Source path already exists without expected Git repository: $SOURCE_DIR"
else
  git clone "$REPO_URL" "$SOURCE_DIR"
fi

log "Installing managed runtime files; preserving credentials and sessions"
node "$SOURCE_DIR/scripts/configure-runtime.mjs" "$SOURCE_DIR" "$AGENT_DIR" "$PI_SETUP_DAILY_WORKFLOW"

install_home_agents() {
  local source="$SOURCE_DIR/home/AGENTS.md" target="$HOME/AGENTS.md" backup
  [[ -f "$source" ]] || die "Missing home AGENTS.md template: $source"
  if [[ -e "$target" ]] && ! cmp -s "$source" "$target"; then
    printf 'Keeping existing host-specific home guidance: %s\n' "$target"
    return
  fi
  cmp -s "$source" "$target" 2>/dev/null || install -m 644 "$source" "$target"
}

log "Installing home AGENTS.md"
install_home_agents

install_tmux_config() {
  local source="$SOURCE_DIR/home/tmux.conf" target="$HOME/.tmux.conf" backup terminal popup=false validate_socket validation_output
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
    ( : <> "$tty" ) 2>/dev/null || die "No terminal available. Export NINEROUTER_URL before running installer."
    read -r -p "9Router URL [http://localhost:20128]: " url < "$tty"
    url="${url:-http://localhost:20128}"
  fi
  url="${url%/}"

  if [[ -z "$key" ]] && ( : <> "$tty" ) 2>/dev/null; then
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

if [[ "$PI_SETUP_OVIS" == 1 ]]; then
  bash "$SOURCE_DIR/scripts/install-ovis.sh" "$OVIS_VERSION"
fi

log "Verifying installation"
printf 'Node.js: %s\n' "$(node --version)"
printf 'Pi:      %s\n' "$(pi --version)"
printf 'qmd:     %s\n' "$(qmd --version 2>/dev/null || printf 'not installed (optional)')"
printf 'Herdr:   %s\n' "$(herdr --version)"
printf '\nSetup complete. Run: cd /path/to/project && pi\n'
