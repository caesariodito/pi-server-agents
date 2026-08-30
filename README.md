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

Do not commit `auth.json` or `sessions/`.
