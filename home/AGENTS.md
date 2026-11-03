# Personal server host policy

- Linux server accessed through SSH; discover hostname, user, HOME, and current network addresses before changes. Read existing host/stack documentation; do not assume another machine's topology.
- This template selects `$HOME/stacks/<stack>/docker-compose.yaml` for personal Compose deployments. Read `$HOME/stacks/README.md` first. Existing host-specific guidance is preserved by installer.
- Load installed `server-operations` skill before deployment/debugging. It owns procedures; host docs own actual domains, networks, ingress, access policy, backups, and service inventory.
- Never print or commit secrets, private state, sessions, or backups. Keep secret files ignored and mode 600. Back up stateful data before upgrades/migrations and verify restore instructions.
- Destructive changes, volume deletion, database overwrite, deployment/restart, and network/auth changes require explicit approval. Never expose Docker socket or unrestricted write API.
- Preserve existing private Tailscale-bound services. If host docs select central Cloudflare Tunnel/Caddy ingress, reuse it; no per-app tunnel or catch-all proxy. Do not create missing infrastructure from template assumptions.
- If central Homepage read-only Docker discovery is configured, user-facing services need appropriate homepage.* labels; infrastructure-only containers stay unlabeled. Verify intended discovery without exposing unrestricted Docker access.
- Update owning stack docs after authorized changes; no credentials in inventories. Installing agent setup does not authorize managing host services.
