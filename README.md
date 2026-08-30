# pi-server-agents

Versioned Pi agent setup for this server.

Tracked:
- `settings.json`
- `models.json`
- `models-store.json`
- `skills/`
- `.gitignore`

Not tracked:
- `auth.json` secrets
- `sessions/` chat history
- package/cache dirs reproducible from settings

## Restore on new server

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

# Optional Pi process config
export PI_OFFLINE=0
export PI_SKIP_VERSION_CHECK=0
```

If 9Router auth is disabled, omit `NINEROUTER_KEY`.

Do not commit `auth.json`, `.env`, or `sessions/`.
