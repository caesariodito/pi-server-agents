#!/usr/bin/env bash
set -Eeuo pipefail

readonly PI_VERSION="0.87.1"
readonly NODE_VERSION="24"
readonly NVM_INSTALLER_VERSION="v0.40.3"
readonly REPO_URL="https://github.com/caesariodito/pi-server-agents"
readonly AGENT_DIR="${PI_CODING_AGENT_DIR:-$HOME/.pi/agent}"
readonly ROUTER_ENV="$HOME/.config/9router/env"

log() { printf '\n==> %s\n' "$*"; }
die() { printf 'Error: %s\n' "$*" >&2; exit 1; }

[[ ${EUID:-$(id -u)} -ne 0 ]] || die "Run as a normal user, not root."
command -v curl >/dev/null || die "curl is required."
command -v git >/dev/null || die "git is required."

install_nvm() {
  local installer
  installer="$(mktemp)"
  trap 'rm -f "$installer"' RETURN
  curl -fsSL "https://raw.githubusercontent.com/nvm-sh/nvm/$NVM_INSTALLER_VERSION/install.sh" -o "$installer"
  PROFILE=/dev/null bash "$installer"
}

export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
if [[ ! -s "$NVM_DIR/nvm.sh" ]]; then
  log "Installing nvm $NVM_INSTALLER_VERSION"
  install_nvm
fi
# shellcheck source=/dev/null
. "$NVM_DIR/nvm.sh"

log "Installing Node.js $NODE_VERSION"
nvm install "$NODE_VERSION"
nvm alias default "$NODE_VERSION" >/dev/null
nvm use "$NODE_VERSION" >/dev/null

log "Installing Pi $PI_VERSION"
npm install -g --ignore-scripts "@earendil-works/pi-coding-agent@$PI_VERSION"

log "Installing qmd"
npm install -g @tobilu/qmd

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
printf '\nSetup complete. Run: cd /path/to/project && pi\n'
