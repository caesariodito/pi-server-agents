// Served as _mermaid/loader.mjs beside the pinned Mermaid bundle. Source stays readable when rendering fails.
import mermaid from './mermaid.esm.min.mjs';

const scheme = matchMedia('(prefers-color-scheme: dark)');
const figures = [...document.querySelectorAll('.figure')].filter(figure => figure.querySelector('[data-mermaid]'));
const MIN_SCALE = 0.7; // Below this, Mermaid text drops under ~10px; scroll instead.
let pass = 0;

function themeVariables() {
  const css = getComputedStyle(document.documentElement);
  const v = name => css.getPropertyValue(name).trim();
  return {
    darkMode: scheme.matches, background: v('--panel'), fontFamily: v('--sans'), fontSize: '14px',
    primaryColor: v('--raised'), primaryTextColor: v('--ink'), primaryBorderColor: v('--line-strong'),
    secondaryColor: v('--side'), tertiaryColor: v('--panel'), lineColor: v('--muted'), textColor: v('--ink'),
    mainBkg: v('--raised'), nodeBorder: v('--line-strong'), clusterBkg: v('--side'), clusterBorder: v('--line-strong'),
    edgeLabelBackground: v('--panel'), titleColor: v('--ink'),
    actorBkg: v('--raised'), actorBorder: v('--line-strong'), actorTextColor: v('--ink'), actorLineColor: v('--faint'),
    signalColor: v('--muted'), signalTextColor: v('--ink'), labelBoxBkgColor: v('--side'), labelBoxBorderColor: v('--line-strong'),
    labelTextColor: v('--ink'), loopTextColor: v('--muted'), noteBkgColor: v('--side'), noteBorderColor: v('--line-strong'), noteTextColor: v('--ink'),
    activationBkgColor: v('--side'), activationBorderColor: v('--line-strong'), sequenceNumberColor: v('--paper'),
    attributeBackgroundColorOdd: v('--raised'), attributeBackgroundColorEven: v('--panel'),
  };
}

// Natural size, never upscaled; shrink to fit only down to MIN_SCALE, then scroll horizontally.
function fit(svg) {
  const width = svg.viewBox.baseVal?.width || svg.getBoundingClientRect().width;
  svg.removeAttribute('style');
  svg.removeAttribute('height');
  svg.setAttribute('width', Math.ceil(width));
  svg.style.maxWidth = '100%';
  svg.style.minWidth = `${Math.ceil(width * MIN_SCALE)}px`;
  return width;
}

function viewer() {
  let dialog = document.querySelector('dialog.viewer');
  if (dialog) return dialog;
  dialog = document.createElement('dialog');
  dialog.className = 'viewer';
  dialog.innerHTML = '<header><span></span><button type="button" value="close">Close</button></header><div class="diagram" tabindex="0"></div>';
  dialog.querySelector('button').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
  dialog.addEventListener('close', () => {
    const { svg, home } = dialog;
    if (svg && home) { home.append(svg); home.style.minHeight = ''; svg.style.maxWidth = '100%'; dialog.svg = dialog.home = null; dialog.opener?.focus(); }
  });
  document.body.append(dialog);
  return dialog;
}

function openViewer(figure, opener) {
  const dialog = viewer();
  const home = figure.querySelector('.diagram');
  const svg = home.querySelector('svg');
  dialog.querySelector('header span').textContent = figure.dataset.title || 'Diagram';
  Object.assign(dialog, { svg, home, opener });
  home.style.minHeight = `${home.offsetHeight}px`; // Hold layout so the page does not jump.
  svg.style.maxWidth = 'none';
  dialog.querySelector('.diagram').append(svg);
  dialog.showModal();
}

async function renderAll() {
  const run = ++pass;
  mermaid.initialize({
    startOnLoad: false, securityLevel: 'strict', theme: 'base', themeVariables: themeVariables(),
    htmlLabels: false, flowchart: { htmlLabels: false, wrappingWidth: 220 }, suppressErrorRendering: true,
  });
  for (const [index, figure] of figures.entries()) {
    const source = figure.querySelector('[data-mermaid]').textContent;
    try {
      const { svg } = await mermaid.render(`diagram-${index}-${run}`, source);
      if (run !== pass) return;
      let view = figure.querySelector(':scope > .diagram');
      if (!view) {
        view = document.createElement('div');
        view.className = 'diagram';
        view.tabIndex = 0;
        view.setAttribute('role', 'img');
        view.setAttribute('aria-label', `${figure.dataset.title || 'Diagram'}. Source available below.`);
        figure.prepend(view);
      }
      view.innerHTML = svg;
      const width = fit(view.querySelector('svg'));
      figure.querySelector('details').open = false;
      figure.classList.add('rendered');
      figure.querySelector('.figure-bar')?.remove();
      const bar = document.createElement('div');
      bar.className = 'figure-bar';
      const clipped = width * MIN_SCALE > view.clientWidth;
      bar.innerHTML = `<span class="hint">${clipped ? 'Wide diagram — scroll sideways or open full size.' : ''}</span><button type="button">Full size</button>`;
      bar.querySelector('button').addEventListener('click', event => openViewer(figure, event.currentTarget));
      view.after(bar);
    } catch {
      if (figure.querySelector('.alert')) continue;
      const error = document.createElement('p');
      error.className = 'alert';
      error.setAttribute('role', 'alert');
      error.textContent = 'Diagram could not render. Read source below.';
      figure.prepend(error);
    }
  }
}

await renderAll();
// Re-theme when the system scheme flips; close the viewer first so the moved SVG returns home.
scheme.addEventListener('change', () => { document.querySelector('dialog.viewer[open]')?.close(); renderAll(); });
