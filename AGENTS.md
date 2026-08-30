# AGENTS.md

Repo purpose: version Pi agent setup for `pi-server-agents`.

## Track

Keep small, useful config in git:
- `settings.json`
- `models.json`
- `models-store.json`
- `skills/`
- package/resource manifests when added
- docs: `README.md`, `AGENTS.md`

## Do not track

Never commit secrets or private runtime data:
- `auth.json`
- `.env`, `.env.*`
- `sessions/`
- logs/cache/temp dirs
- installed package clones/caches (`npm/`, `git/`) unless explicitly requested

## Change rules

- Prefer settings/package refs over vendored installed packages.
- Keep diffs minimal.
- Use existing Pi package/install mechanisms when possible.
- After changing tracked setup, use Conventional Commits and run:
  ```bash
  git status --short --ignored
  git add <changed-files>
  git commit -m '<type>(<scope>): <short message>'
  git push
  ```
- Common commit types: `feat`, `fix`, `docs`, `chore`, `refactor`.
- Before committing, verify ignored secrets remain ignored:
  ```bash
  git status --short --ignored
  ```

## Restore

See `README.md` for clone/backup/env setup.
