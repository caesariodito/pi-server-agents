# AGENTS.md — server baseline

## Server context

- Linux server managed through SSH.
- Determine current host, user, home, and Tailscale address before changes:
  ```bash
  hostname
  id
  printf 'HOME=%s\n' "$HOME"
  tailscale ip -4
  ```
- Docker Engine and Docker Compose are expected.
- Dockge manages `$HOME/stacks` when installed.
- Read `$HOME/stacks/README.md` before Docker deployment changes.

## Mandatory Docker layout

Every Docker Compose deployment must live under:

```text
$HOME/stacks/<stack>/docker-compose.yaml
```

Never deploy a Compose project directly under `$HOME`, `/tmp`, or a repository workspace. Keep one stack per directory. Keep stack-specific docs, scripts, persistent bind mounts, and `.env` beside its Compose file.

## Secrets and state

- Never print, commit, copy into documentation, or expose `.env` values, passwords, tokens, private keys, databases, sessions, or backups.
- Use `.env.example` or secret-file `.example` files with placeholders. Real secret files must be mode `600` and ignored by version control.
- Inspect environment variable names only unless a secret value is explicitly needed for an operation.
- Back up stateful services before upgrades or migrations. Test restore instructions.
- Never run `docker compose down -v`, delete stack data, prune volumes, or overwrite a database without explicit approval and a verified backup.

## Network and exposure policy

- Discover the server Tailscale IPv4 with `tailscale ip -4`; never assume an address from another server.
- Private services bind host ports to the server Tailscale IP, not `0.0.0.0`.
- Public web services use the central `$HOME/stacks/ingress` stack.
- Central ingress uses one Cloudflare Tunnel and Caddy on external Docker network `web`.
- Do not add per-app `cloudflared` containers.
- Public app containers join external network `web`; do not publish app ports to the host unless explicitly required.
- Add explicit hostname routes to `$HOME/stacks/ingress/Caddyfile`. Do not use Caddy catch-all proxy routes.
- Verify local DNS zone, tunnel routes, and access policy in stack documentation before changes.
- Review client compatibility before putting Cloudflare Access in front of an API or native-client service.

## New deployment procedure

Before creating or changing a deployment, inspect live state and read stack docs:

```bash
cat "$HOME/stacks/README.md"
docker compose ls -a
docker ps -a
ss -lnt
docker network ls
```

### 1. Create stack directory

```bash
mkdir -p "$HOME/stacks/<app>"
cd "$HOME/stacks/<app>"
```

Create at minimum:

```text
docker-compose.yaml
.env.example
.gitignore
README.md
```

Create real `.env` only when needed, set mode `600`, and never place secrets in Compose or documentation:

```bash
cp .env.example .env
chmod 600 .env
```

### 2. Choose one exposure model

Private/Tailscale service:

```yaml
services:
  app:
    ports:
      - "TAILSCALE_IPV4:PORT:CONTAINER_PORT"
```

Replace `TAILSCALE_IPV4` with output from `tailscale ip -4`.

Public web service through central ingress:

```yaml
services:
  app:
    # No ports entry.
    networks:
      - web

networks:
  web:
    external: true
    name: web
```

For cross-stack Caddy DNS, give service a unique service name or stable `container_name`. Check existing names first:

```bash
docker ps -a --format '{{.Names}}'
```

Never add another `cloudflared` container. Use existing central tunnel.

### 3. Add public Caddy route

For public apps, add an explicit route to `$HOME/stacks/ingress/Caddyfile`:

```caddy
http://app.example.com {
    reverse_proxy app-container-name:CONTAINER_PORT
}
```

Use documented local hostname and domain. Do not add a duplicate tunnel route or DNS record when an existing wildcard covers the hostname. Do not add a Caddy wildcard proxy.

Validate before reload:

```bash
cd "$HOME/stacks/ingress"
docker compose exec caddy caddy validate --config /etc/caddy/Caddyfile
docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile
```

### 4. Validate and deploy app

```bash
cd "$HOME/stacks/<app>"
docker compose config
docker compose pull
docker compose up -d
docker compose ps
docker compose logs --tail=100
```

### 5. Verify

Public app:

```bash
curl -I https://app.example.com
```

Also test login, persistence across `docker compose restart`, health status, backup, and restore instructions. After every successful public deployment, update the current-stack and public-service inventory in `$HOME/stacks/README.md`.

Record hostname, stack path, upstream service/port, access policy, and purpose. Remove or mark entries retired when services are removed. Never record credentials or secret values. Source of routing truth remains `$HOME/stacks/ingress/Caddyfile`; compare inventory against Caddy before changes and fix documentation drift in the same change.

### 6. Stateful app requirements

Before considering deployment complete, document in stack `README.md`:

- Public or private URL and port
- Required environment variables without secret values
- Persistent data locations
- Backup command and included data
- Restore procedure
- Update procedure

Run a backup before upgrades or migrations. Never run `docker compose down -v`, delete stack data, prune volumes, or overwrite databases without explicit approval and a verified backup.

Prefer minimal changes. Preserve existing Tailscale-bound stacks unless migration is requested. Pin infrastructure and security-sensitive image versions; review upstream release notes before changing pins.
