// SPDX-License-Identifier: MIT
// One shared view choice updates the whole collection. Keep the README links
// available when JavaScript is disabled.
document.querySelectorAll('.frame-catalog').forEach(catalog => {
  const frames = [...catalog.querySelectorAll('tbody tr')].map(row => {
    const image = row.querySelector('img');
    return {
      image,
      preview: image.closest('a'),
      name: row.querySelector('td:nth-child(2) strong').textContent,
      views: [...row.querySelectorAll('td:last-child a')]
    };
  });
  const controls = document.createElement('fieldset');
  controls.className = 'catalog-view-controls';
  const legend = document.createElement('legend');
  legend.className = 'view-announcement';
  legend.textContent = 'View all frames';
  controls.append(legend);
  const live = document.createElement('span');
  live.className = 'view-announcement';
  live.setAttribute('aria-live', 'polite');
  const choices = document.createElement('div');
  choices.className = 'catalog-view-choices';
  frames[0].views.forEach((link, index) => {
    const label = document.createElement('label');
    const input = document.createElement('input');
    input.type = 'radio';
    input.name = 'catalog-view';
    input.value = link.textContent;
    input.checked = link.href === frames[0].preview.href;
    const text = document.createElement('span');
    text.textContent = link.textContent;
    label.append(input, text);
    choices.append(label);
    input.addEventListener('change', () => {
      if (!input.checked) return;
      frames.forEach(({image, preview, name, views}) => {
        const view = views[index];
        image.src = view.href;
        image.style.setProperty('--canvas', view.dataset.canvas);
        image.alt = `${name}, ${view.textContent.toLowerCase()} view`;
        preview.href = view.href;
        preview.setAttribute('aria-label', image.alt);
      });
      live.textContent = `All ${frames.length} frames: showing ${input.value.toLowerCase()} view`;
    });
  });
  controls.append(choices, live);
  catalog.before(controls);
  catalog.classList.add('has-shared-view');
});

// Play once when visible, then hold the final front view. Reduced-motion
// visitors keep the still poster; there are no animation buttons or controls.
const demo = document.querySelector('#insertion-demo');
if (demo) {
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  let visible = false;
  const syncPlayback = () => {
    if (visible && !reduced.matches && !demo.ended) demo.play().catch(() => {});
    else demo.pause();
  };
  reduced.addEventListener('change', syncPlayback);
  new IntersectionObserver(entries => {
    visible = entries[0].isIntersecting && entries[0].intersectionRatio >= .25;
    syncPlayback();
  }, {threshold: [0, .25]}).observe(demo);
}
