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

Restore:
```bash
git clone <repo-url> ~/.pi/agent
```

If Pi is already configured, back up existing `~/.pi/agent` first.
