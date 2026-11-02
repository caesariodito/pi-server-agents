#!/usr/bin/env node
import assert from 'node:assert/strict';
import { mkdir, mkdtemp, writeFile, symlink, rm, access } from 'node:fs/promises';
import { resolve } from 'node:path';
import { request } from 'node:http';
import { startPreview, diagramAllowed } from './preview.mjs';

const scratch = resolve(import.meta.dirname, '../../../.scratch/review-preview');
await mkdir(scratch, { recursive: true });
const directory = await mkdtemp(resolve(scratch, 'test-'));
const root = resolve(directory, 'docs');
await mkdir(root);
let preview;
try {
  await writeFile(resolve(root, 'spec.md'), '# Hello\n\n**bold** [safe](https://example.invalid) [bad](javascript:alert%281%29)\n\n<script>alert(1)</script>\n\n![image](https://example.invalid/image.png)');
  await writeFile(resolve(root, 'implementation-plan.html'), '<!doctype html><a href="spec.md">Spec</a><script>/* trusted review */</script>');
  await writeFile(resolve(directory, 'outside.md'), 'outside');
  await symlink(resolve(directory, 'outside.md'), resolve(root, 'escape.md'));
  await writeFile(resolve(root, 'data.json'), '{}');
  await writeFile(resolve(root, 'large.md'), 'x'.repeat(2 * 1024 * 1024 + 1));
  preview = await startPreview(root);
  const get = (path, headers = {}, method = 'GET') => new Promise((ok, fail) => {
    const url = new URL(preview.url);
    const req = request({ hostname: url.hostname, port: url.port, path: url.pathname + path, method, headers }, res => {
      let body = ''; res.on('data', chunk => body += chunk); res.on('end', () => ok({ status: res.statusCode, body, headers: res.headers }));
    }); req.on('error', fail); req.end();
  });
  const rendered = await get('spec.md');
  assert.equal(rendered.status, 200);
  assert.match(rendered.body, /<h1 id="hello">Hello<\/h1>/);
  assert.match(rendered.body, /<strong>bold<\/strong>/);
  assert(!rendered.body.includes('<script>') && !rendered.body.includes('<img'));
  assert(!rendered.body.includes('href="javascript:'));
  assert.match(rendered.headers['content-security-policy'], /script-src 'none'/);
  await writeFile(resolve(root, 'spec.md'), '[entity](javascript&#58;alert%281%29) [encoded](%6aavascript:alert%281%29) [relative](other.md)\n\n| A | B |\n| - | - |\n| x | y |\n\n```js\nconst x = 1;\n```');
  const formatting = (await get('spec.md')).body;
  assert(!formatting.includes('href="javascript') && !formatting.includes('href="%6aavascript'));
  assert(formatting.includes('href="other.md"') && formatting.includes('<table>') && formatting.includes('<pre><code'));
  assert(diagramAllowed('flowchart TD\n A-->B'));
  for (const source of ['%%{init: {securityLevel: loose}}%%\nflowchart TD', '---\nconfig: {}\n---', 'flowchart TD\nclick A "https://evil.invalid"', 'x'.repeat(50001)]) assert(!diagramAllowed(source));
  await writeFile(resolve(root, 'diagrams.md'), '# Diagram reference\n\n## Entity relationships\n\n```mermaid\nflowchart TD\n A-->B\n```');
  const diagrams = await get('diagrams.md');
  assert(diagrams.body.includes('id="entity-relationships"') && diagrams.body.includes(' data-mermaid'));
  const engineAvailable = await access(resolve(import.meta.dirname, '../../technical-spec/node_modules/mermaid/dist/mermaid.esm.min.mjs')).then(() => true, () => false);
  assert.match(diagrams.headers['content-security-policy'], engineAvailable ? /nonce-.*strict-dynamic/ : /script-src 'none'/);
  if (!engineAvailable) assert(diagrams.body.includes('Mermaid engine unavailable'));
  assert(diagrams.body.includes('<figure class="figure" data-title="Entity relationships">'));
  await writeFile(resolve(root, 'outline.md'), '# Doc\n\n## Same\n\n### Child `code`\n\n## Same\n\n#### Deep');
  const outline = (await get('outline.md')).body;
  assert(outline.includes('<title>Doc · outline.md</title>'));
  assert(outline.includes('id="same"') && outline.includes('id="same-1"'), 'duplicate headings get unique slugs');
  assert(outline.includes('<a class="anchor" href="#same-1"'));
  const sidebar = outline.split('<main', 1)[0];
  assert(sidebar.includes('<li class="d3"><a href="#child-code">Child code</a></li>') && !sidebar.includes('href="#deep"'), 'contents list h2/h3 only');
  assert(sidebar.includes('>Implementation review</a>') && sidebar.includes('>Canonical spec</a>') && sidebar.includes('>Diagram reference</a>'));
  assert(!sidebar.includes('technical-spec.html'), 'missing review documents are not linked');
  assert((await get('spec.md')).body.includes('spec.md" aria-current="page">Canonical spec'));
  if (engineAvailable) {
    assert.match((await get('_mermaid/loader.mjs')).body, /mermaid\.esm\.min\.mjs/);
    assert.equal((await get('_mermaid/mermaid.esm.min.mjs')).status, 200);
  }
  assert.equal((await get('_mermaid/../../package.json')).status, 403);
  assert.equal((await get('_mermaid/package.json')).status, 403);
  await writeFile(resolve(root, 'blocked.md'), '```mermaid\n%%{init: {securityLevel: loose}}%%\nflowchart TD\n```');
  const blocked = await get('blocked.md');
  assert(blocked.body.includes('Diagram blocked:') && !blocked.body.includes(' data-mermaid'));
  assert.match(blocked.headers['content-security-policy'], /script-src 'none'/);
  await writeFile(resolve(root, 'spec.md'), '# Updated');
  assert.match((await get('spec.md')).body, /<h1 id="updated">Updated/);
  assert.equal((await get('implementation-plan.html')).status, 200);
  assert.equal((await get('spec.md', { Host: 'evil.invalid' })).status, 403);
  assert.equal((await get('spec.md', { Origin: 'https://evil.invalid' })).status, 403);
  for (const path of ['../outside.md', '%2e%2e/outside.md', 'escape.md', '%2Fetc/passwd']) assert.equal((await get(path)).status, 403, path);
  assert.equal((await get('missing.md')).status, 404);
  assert.equal((await get('data.json')).status, 415);
  assert.equal((await get('large.md')).status, 413);
  assert.equal((await get('spec.md', {}, 'POST')).status, 405);
  assert.equal((await get('spec.md', {}, 'HEAD')).body, '');
  console.log('Markdown preview checks: PASS');
} finally {
  if (preview) await new Promise(ok => preview.server.close(ok));
  await rm(directory, { recursive: true, force: true });
}
