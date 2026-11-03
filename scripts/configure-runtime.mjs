#!/usr/bin/env node
import { cpSync, existsSync, lstatSync, mkdirSync, readFileSync, readdirSync, renameSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { createHash } from 'node:crypto';

const [sourceArg, agentArg, dailyFlag] = process.argv.slice(2);
if (!sourceArg || !agentArg || !['0', '1'].includes(dailyFlag)) throw new Error('Usage: configure-runtime.mjs SOURCE AGENT_DIR DAILY(0|1)');
const source = resolve(sourceArg), agent = resolve(agentArg);
if (source === agent) throw new Error('Source and runtime directories must differ');
mkdirSync(agent, { recursive: true, mode: 0o700 });
function rejectSymlinkParents(path) {
  for (let current = path; current === agent || current.startsWith(agent + '/'); current = dirname(current)) {
    if (existsSync(current) && lstatSync(current).isSymbolicLink()) throw new Error(`Refusing managed symlink: ${current}`);
  }
}
rejectSymlinkParents(agent);
const stamp = `${new Date().toISOString().replace(/[:.]/g, '-')}-${process.pid}`;
const settingsPath = join(agent, 'settings.json');
const settings = existsSync(settingsPath) ? JSON.parse(readFileSync(settingsPath, 'utf8')) : JSON.parse(readFileSync(join(source, 'settings.json'), 'utf8'));
if (!settings || typeof settings !== 'object' || Array.isArray(settings)) throw new Error('Settings must be a JSON object');
for (const key of ['packages', 'skills']) if (settings[key] !== undefined && !Array.isArray(settings[key])) throw new Error(`settings.${key} must be an array`);
const modelsPath = join(agent, 'models.json');
const models = existsSync(modelsPath) ? JSON.parse(readFileSync(modelsPath, 'utf8')) : undefined;
if (models !== undefined && (!models || typeof models !== 'object' || Array.isArray(models))) throw new Error('models.json must be a JSON object');
const marker = join(agent, '.daily-workflow');
const daily = dailyFlag === '1' || existsSync(marker);
const runtime = readFileSync(join(source, 'runtime/AGENTS.md'), 'utf8');
const dailyGuidance = daily ? '\n' + readFileSync(join(source, 'profiles/daily/AGENTS.md'), 'utf8') : '';
const shared = JSON.parse(readFileSync(join(source, 'profiles/shared-skills.json'), 'utf8'));
if (!/^git:github\.com\/caesariodito\/skills@[a-f0-9]{40}$/.test(shared.source) || !['base', 'daily'].every(key => Array.isArray(shared[key]) && shared[key].every(name => /^[a-z0-9-]+$/.test(name)))) throw new Error('Invalid shared skill pin or selection');

function save(path, data) {
  rejectSymlinkParents(path);
  if (existsSync(path) && readFileSync(path).equals(Buffer.from(data))) return;
  mkdirSync(dirname(path), { recursive: true });
  if (existsSync(path)) cpSync(path, `${path}.backup.${stamp}`, { errorOnExist: true, force: false });
  const temp = `${path}.tmp.${process.pid}`;
  writeFileSync(temp, data, { mode: 0o600, flag: 'wx' });
  renameSync(temp, path);
}
function copyTree(from, to) {
  // ponytail: small curated source trees only; add manifest-based removal if managed files are retired.
  for (const entry of readdirSync(from, { withFileTypes: true })) {
    const src = join(from, entry.name), dst = join(to, entry.name);
    if (entry.isDirectory()) copyTree(src, dst);
    else if (entry.isFile()) {
      const data = readFileSync(src);
      save(dst, data);
    }
    else throw new Error(`Unsupported source entry: ${src}`);
  }
}
const pins = daily ? JSON.parse(readFileSync(join(source, 'profiles/daily/packages.json'), 'utf8')) : [];
const identity = spec => {
  const value = typeof spec === 'string' ? spec : spec?.source;
  if (typeof value !== 'string') throw new Error('Invalid package declaration');
  return value.replace(/@[^/@]+$/, '').replace(/^git:github\.com\//, 'https://github.com/').replace(/\.git$/, '').replace(/\/$/, '');
};
const managed = [...pins, shared.source];
const selected = [...shared.base, ...(daily ? shared.daily : [])];
settings.packages = [...(settings.packages ?? []).filter(spec => !managed.some(pin => identity(pin) === identity(spec))), ...pins, { source: shared.source, skills: selected.map(name => `${name}/SKILL.md`), extensions: [], prompts: [], themes: [] }];
// Preserve legacy files for rollback, but stop loading the old managed snapshot.
if (settings.skills) settings.skills = settings.skills.filter(path => ![join(agent, 'daily-skills'), '~/.pi/agent/daily-skills'].includes(path));
const legacyGateway = [];
for (const [name, hash] of Object.entries(shared.legacyGatewayHashes)) {
  if (!/^9router(?:-web-fetch|-web-search)?$/.test(name) || !/^[a-f0-9]{64}$/.test(hash)) throw new Error('Invalid legacy skill manifest');
  const old = join(agent, 'skills', name);
  if (!existsSync(old)) continue;
  rejectSymlinkParents(join(old, 'SKILL.md'));
  if (readdirSync(old).length !== 1 || createHash('sha256').update(readFileSync(join(old, 'SKILL.md'))).digest('hex') !== hash) throw new Error(`Local gateway skill differs from former managed source; preserve and merge before migration: ${old}`);
  legacyGateway.push([name, old]);
}
// Read/validate settings before replacing any managed runtime file.
save(settingsPath, JSON.stringify(settings, null, 2) + '\n');
save(join(agent, 'AGENTS.md'), runtime + dailyGuidance);
// An old override wins over AGENTS.md; leave it intact and report instead of silently ignoring policy.
if (existsSync(join(agent, 'AGENTS.override.md'))) console.warn('WARNING: existing AGENTS.override.md overrides managed guidance; review it before starting Pi.');
if (models) {
  // Repair prior empty migrations or migrate exact legacy config; preserve unrelated user overrides.
  const legacy = models.providers?.['9router'];
  if (Object.keys(models).length === 0 || (legacy?.baseUrl === 'http://100.70.192.32:20128/v1' && Object.keys(models.providers).length === 1 && Object.keys(legacy).every(k => ['baseUrl', 'apiKey'].includes(k)))) {
    save(modelsPath, '{"providers":{}}\n');
  } else if (legacy) console.warn('WARNING: existing models.json overrides 9Router extension; review endpoint/auth settings before starting Pi.');
}
// Retire only former installer-owned gateway directories, preserving contents for rollback.
for (const [name, old] of legacyGateway) {
  const retired = join(agent, 'retired-skills', `${name}.backup.${stamp}`);
  rejectSymlinkParents(retired);
  mkdirSync(dirname(retired), { recursive: true });
  renameSync(old, retired);
}
copyTree(join(source, 'extensions'), join(agent, 'extensions'));
copyTree(join(source, 'skills'), join(agent, 'skills'));
if (daily) save(marker, 'enabled\n');
console.log(`Runtime configured: ${agent}; daily workflow: ${daily ? 'enabled' : 'unchanged/off'}`);
