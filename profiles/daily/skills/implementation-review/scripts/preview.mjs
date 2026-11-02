#!/usr/bin/env node
// Local review directory only; trusted generated HTML, untrusted Markdown.
import { createServer } from 'node:http';
import { readFile, realpath, stat } from 'node:fs/promises';
import { homedir } from 'node:os';
import { extname, isAbsolute, relative, resolve, sep } from 'node:path';
import { pathToFileURL } from 'node:url';
import { randomBytes } from 'node:crypto';
import { createRequire } from 'node:module';

const MAX_BYTES = 2 * 1024 * 1024;
const MERMAID_DIST = resolve(import.meta.dirname, '../../technical-spec/node_modules/mermaid/dist');
const ASSETS = resolve(import.meta.dirname, '../assets');
// Review set documents, listed under sidebar Links when present in served root.
const REFERENCES = [
  ['implementation-plan.html', 'Implementation review'], ['technical-spec.html', 'Technical specification'],
  ['spec.md', 'Canonical spec'], ['diagrams.md', 'Diagram reference'],
];
let PREVIEW_CSS = '';
export function diagramAllowed(source) {
  return source.length <= 50000 && !/%%\s*\{|^\s*---|^\s*(click|link)\s/im.test(source);
}
const escape = value => String(value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

async function markdownEngine() {
  const install = resolve(homedir(), '.pi/agent/install');
  let engine;
  try {
    const version = (await readFile(resolve(install, 'current-version'), 'utf8')).trim();
    if (!/^[\w.-]+$/.test(version)) throw new Error('Invalid managed Pi version');
    engine = resolve(install, 'releases', version, 'node_modules/marked/lib/marked.esm.js');
    await stat(engine);
  } catch {
    const require = createRequire(resolve(process.execPath, '../../lib/node_modules/@earendil-works/pi-coding-agent/package.json'));
    engine = require.resolve('marked');
  }
  const { Marked } = await import(pathToFileURL(engine).href);
  // Parsing is synchronous, so per-document outline state is safe between requests.
  let outline, slugs, section;
  const marked = new Marked({ renderer: {
    heading({ tokens, depth, text }) {
      const base = text.toLowerCase().replace(/[^a-z0-9 -]/g, '').trim().replace(/\s+/g, '-') || 'section';
      const count = slugs.get(base) ?? 0;
      slugs.set(base, count + 1);
      const id = count ? `${base}-${count}` : base;
      const label = this.parser.parseInline(tokens);
      const plain = label.replace(/<[^>]*>/g, '');
      outline.push({ id, depth, label: plain });
      if (depth > 1) section = plain;
      const anchor = depth > 1 ? `<a class="anchor" href="#${escape(id)}" aria-label="Link to this section">#</a>` : '';
      return `<h${depth} id="${escape(id)}">${label}${anchor}</h${depth}>`;
    },
    code(token) {
      if (token.lang?.trim() !== 'mermaid') return false;
      const allowed = diagramAllowed(token.text);
      return `<figure class="figure" data-title="${section ?? ''}">${allowed ? '' : '<p class="alert" role="alert">Diagram blocked: configuration directives, click actions, or excessive size. Read source below.</p>'}<details open><summary>Mermaid source</summary><pre${allowed ? ' data-mermaid' : ''}>${escape(token.text)}</pre></details></figure>`;
    },
    html({ text }) { return escape(text); },
    image({ text }) { return escape(text); },
    link({ href, tokens }) {
      const label = this.parser.parseInline(tokens);
      // Reject entity/percent-obfuscated schemes, protocol-relative URLs and controls.
      if (/[\s\u0000-\u001f\u007f\\]/.test(href) || href.startsWith('//') || /&(?:#|\w+;)/.test(href)) return label;
      const decoded = (() => { try { return decodeURIComponent(href); } catch { return ''; } })();
      if (!decoded || (decoded.includes(':') && !/^(https?:|mailto:)/i.test(decoded))) return label;
      return `<a href="${escape(href)}" rel="noreferrer noopener">${label}</a>`;
    },
  }});
  return source => {
    outline = []; slugs = new Map(); section = undefined;
    const html = marked.parse(source);
    return { html, outline };
  };
}

async function sidebar(root, prefix, name, outline) {
  const references = [];
  for (const [file, label] of REFERENCES) {
    try { if ((await stat(resolve(root, file))).isFile()) references.push([file, label]); } catch {}
  }
  const links = references.map(([file, label]) => `<li><a href="${prefix}${file}"${file === name ? ' aria-current="page"' : ''}>${label}</a></li>`).join('');
  const toc = outline.filter(item => item.depth === 2 || item.depth === 3)
    .map(item => `<li class="d${item.depth}"><a href="#${escape(item.id)}">${item.label}</a></li>`).join('');
  const blocks = (links ? `<nav class="side-block" aria-label="Review documents"><span class="side-label">Links</span><ul class="side-links">${links}</ul></nav>` : '')
    + (toc ? `<nav class="side-block" aria-label="Contents"><span class="side-label">Contents</span><ol class="toc">${toc}</ol></nav>` : '');
  return blocks ? `<aside class="sidebar"><details><summary>Contents and links</summary><div>${blocks}</div></details></aside>` : '';
}

function page({ title, name, side, rendered, script }) {
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${title}</title><style>${PREVIEW_CSS}</style></head>`
    + `<body><a class="skip" href="#document">Skip to document</a><div class="shell${side ? '' : ' solo'}">${side}<main class="content" id="document">`
    + `<div class="masthead"><span class="file">${escape(name)}</span><span>Markdown preview</span><span class="note">Read-only · rendered from source on each load</span></div>`
    + `<article class="prose">${rendered}</article></main></div>${script}</body></html>`;
}

export async function startPreview(directory, port = 0) {
  const root = await realpath(directory);
  if (!(await stat(root)).isDirectory()) throw new Error('Select a review directory');
  const markdown = await markdownEngine();
  PREVIEW_CSS = await readFile(resolve(ASSETS, 'preview.css'), 'utf8');
  const loader = await readFile(resolve(ASSETS, 'preview-diagrams.mjs'), 'utf8');
  const prefix = `/${randomBytes(24).toString('hex')}/`;
  let origin;
  const server = createServer(async (request, response) => {
    const send = (status, body, type = 'text/plain; charset=utf-8') => {
      response.writeHead(status, { 'Content-Type': type, 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer' });
      response.end(request.method === 'HEAD' ? '' : body);
    };
    if (request.headers.host !== new URL(origin).host || (request.headers.origin && request.headers.origin !== origin)) return send(403, 'Forbidden');
    if (!['GET', 'HEAD'].includes(request.method)) return send(405, 'Method not allowed');
    try {
      // Inspect raw path before URL normalization to reject traversal, including encoded forms.
      const raw = request.url.split('?')[0];
      if (!raw.startsWith(prefix)) return send(404, 'Not found');
      const name = decodeURIComponent(raw.slice(prefix.length)) || 'implementation-plan.html';
      if (name.startsWith('_mermaid/')) {
        const asset = name.slice('_mermaid/'.length);
        if (!/^[a-zA-Z0-9_./-]+\.m?js$/.test(asset) || asset.split('/').some(p => p.startsWith('.'))) return send(403, 'Forbidden');
        if (asset === 'loader.mjs') return send(200, loader, 'text/javascript; charset=utf-8');
        const file = await realpath(resolve(MERMAID_DIST, asset));
        const rel = relative(await realpath(MERMAID_DIST), file);
        if (rel.startsWith('..') || isAbsolute(rel)) return send(403, 'Forbidden');
        return send(200, await readFile(file, 'utf8'), 'text/javascript; charset=utf-8');
      }
      if (name.includes('\0') || name.includes('\\') || name.split('/').some(part => part.startsWith('.')) || isAbsolute(name)) return send(403, 'Forbidden');
      const file = await realpath(resolve(root, name));
      const rel = relative(root, file);
      if (rel.startsWith(`..${sep}`) || rel === '..' || isAbsolute(rel)) return send(403, 'Forbidden');
      const extension = extname(file).toLowerCase();
      if (!['.md', '.html'].includes(extension)) return send(415, 'Only Markdown and generated review HTML are served');
      const info = await stat(file);
      if (!info.isFile()) return send(404, 'Not found');
      if (info.size > MAX_BYTES) return send(413, 'Document exceeds 2 MiB');
      const source = await readFile(file, 'utf8');
      if (Buffer.byteLength(source) > MAX_BYTES) return send(413, 'Document exceeds 2 MiB');
      // ponytail: static HTML is trusted renderer output; do not use this as an arbitrary HTML upload server.
      const { html: rendered, outline } = extension === '.md' ? markdown(source) : { html: '', outline: [] };
      const diagrams = rendered.includes(' data-mermaid');
      let engineAvailable = false;
      if (diagrams) { try { await stat(resolve(MERMAID_DIST, 'mermaid.esm.min.mjs')); engineAvailable = true; } catch {} }
      const nonce = randomBytes(24).toString('base64');
      response.setHeader('Content-Security-Policy', `default-src 'none'; style-src 'unsafe-inline'; script-src ${extension === '.html' ? "'unsafe-inline'" : diagrams && engineAvailable ? `'nonce-${nonce}' 'strict-dynamic'` : "'none'"}; base-uri 'none'; form-action 'none'; frame-ancestors 'none'`);
      const diagramScript = diagrams ? engineAvailable ? `<script type="module" nonce="${nonce}" src="${prefix}_mermaid/loader.mjs"></script>` : '<p class="alert" role="alert">Mermaid engine unavailable. Run npm ci --ignore-scripts in technical-spec skill directory. Source remains readable.</p>' : '';
      let body = source;
      if (extension === '.md') {
        const heading = outline.find(item => item.depth === 1)?.label;
        const title = heading ? `${heading} · ${escape(name)}` : escape(name);
        body = page({ title, name, side: await sidebar(root, prefix, name, outline), rendered, script: diagramScript });
      }
      send(200, body, 'text/html; charset=utf-8');
    } catch (error) {
      send(error.code === 'ENOENT' || error.code === 'ENOTDIR' ? 404 : error instanceof URIError ? 400 : 500, 'Document unavailable');
    }
  });
  await new Promise((ok, fail) => { server.once('error', fail); server.listen(port, '127.0.0.1', ok); });
  origin = `http://127.0.0.1:${server.address().port}`;
  return { server, url: origin + prefix };
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  try {
    if (process.argv.length !== 3) throw new Error('Usage: node preview.mjs /absolute/path/to/non-sensitive-review-directory');
    const { url } = await startPreview(process.argv[2]);
    console.log(`Review preview: ${url}\nMarkdown renders on refresh. No HTML copy written. Ctrl+C stops server.\nServe only a dedicated non-sensitive review directory. Export browser answers before changing origin.`);
  } catch (error) { console.error(`preview: ${error.message}`); process.exitCode = 1; }
}
