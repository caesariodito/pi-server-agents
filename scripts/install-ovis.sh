#!/usr/bin/env bash
set -Eeuo pipefail
version="${1:?Ovis release ref required}"
fail() { printf 'Ovis: %s\n' "$*" >&2; exit 1; }
minimum() {
  node -e 'const p=s=>{const m=s.match(/(?:^|\s|v)(\d+)\.(\d+)\.(\d+)(?:\s|$)/);if(!m)process.exit(2);return m.slice(1).map(Number)};const a=p(process.argv[1]),b=p(process.argv[2]);for(let i=0;i<3;i++){if(a[i]>b[i])process.exit(0);if(a[i]<b[i])process.exit(1)}' "$1" "$2"
}
minimum "$(herdr --version)" 0.9.0 || fail 'Herdr >=0.9.0 required; upgrade explicitly. Existing server was not restarted.'
export PATH="$HOME/.bun/bin:$HOME/.local/bin:$PATH"
if ! command -v bun >/dev/null; then
  installer="$(mktemp)"
  trap 'rm -f "$installer"' EXIT
  curl -fsSL https://bun.sh/install -o "$installer"
  bash "$installer" 'bun-v1.4.0'
fi
minimum "$(bun --version)" 1.4.0 || fail 'Bun >=1.4.0 required; upgrade explicitly.'
# Configure loopback before plugin install: plugin startup may run immediately.
config="$(herdr plugin config-dir devswha.ovis)"
[[ "$config" == /* ]] || fail 'Expected absolute plugin config directory.'
node --input-type=module - "$config" <<'JS'
import { existsSync, readFileSync, mkdirSync, appendFileSync, lstatSync } from 'node:fs';
import { join } from 'node:path';
const dir=process.argv[2];
mkdirSync(dir,{recursive:true,mode:0o700});
for(const key of ['HOST','HERDR_WEB_HOST'])if(process.env[key] && process.env[key]!=='127.0.0.1')throw new Error('Ambient Ovis host is not loopback');
for(const key of ['PORT','HERDR_WEB_PORT'])if(process.env[key] && process.env[key]!=='7317')throw new Error('Ambient Ovis port requires manual review');
for(const name of ['env','.env']){
  const file=join(dir,name);
  if(!existsSync(file))continue;
  if(lstatSync(file).isSymbolicLink())throw new Error('Refusing symlinked Ovis config');
  const text=readFileSync(file,'utf8');
  for(const line of text.split('\n')){
    if(!line.trim()||line.trim().startsWith('#'))continue;
    const match=line.match(/^\s*(?:export\s+)?([A-Z_][A-Z0-9_]*)\s*=\s*(.*?)\s*$/);
    if(!match)throw new Error('Review unsupported Ovis config syntax before installation');
    const value=match[2].replace(/^(['"])(.*)\1$/,'$2');
    if(['HOST','HERDR_WEB_HOST'].includes(match[1])&&value!=='127.0.0.1')throw new Error('Existing Ovis listener not loopback; refusing network exposure');
    if(['PORT','HERDR_WEB_PORT'].includes(match[1])&&value!=='7317')throw new Error('Existing custom Ovis port; configure manually');
    if(match[1].includes('RELAY')&&!['','0','false'].includes(value))throw new Error('Existing relay configuration; configure manually');
  }
}
const file=join(dir,'env');
if(!existsSync(file))appendFileSync(file,'HOST=127.0.0.1\nPORT=7317\n',{mode:0o600});
JS
# Existing installation is user-owned: do not replace its checkout or auto-update.
plugins="$(herdr plugin list --json)"
installed="$(printf '%s' "$plugins" | node --input-type=module -e 'let s="";for await(const c of process.stdin)s+=c;const d=JSON.parse(s);if(!Array.isArray(d.result?.plugins))throw Error("Invalid plugin list");console.log(d.result.plugins.some(p=>p.plugin_id==="devswha.ovis")?"yes":"no")')"
if [[ "$installed" == no ]]; then
  herdr plugin install --ref "$version" --yes devswha/ovis
fi
if ! herdr status server >/dev/null 2>&1; then
  printf 'Ovis installed. Startup pending: start Herdr with Bun and Pi on PATH, then invoke devswha.ovis.start. No network access configured.\n'
  exit 0
fi
herdr plugin action invoke devswha.ovis.start
for ((attempt=0; attempt<20; attempt++)); do
  if curl -fsS --max-time 2 http://127.0.0.1:7317/api/health | node -e 'let s="";for await(const c of process.stdin)s+=c;const d=JSON.parse(s);process.exit(d.ok===true&&d.herdr?0:1)' --input-type=module 2>/dev/null; then
    printf 'Ovis healthy at http://127.0.0.1:7317. Phone access NOT configured; follow README private-access instructions.\n'
    exit 0
  fi
  sleep 1
done
fail 'Start queued but health check failed. Check plugin logs; Herdr server was not restarted.'
