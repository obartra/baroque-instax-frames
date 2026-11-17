// SPDX-License-Identifier: MIT
// Enhance the README's view links. Without JavaScript they open the same images.
document.querySelectorAll('.frame-catalog tbody tr').forEach(row => {
  const image = row.querySelector('img');
  const preview = image.closest('a');
  const name = row.querySelector('td:nth-child(2) strong').textContent;
  const views = [...row.querySelectorAll('td:last-child a')];
  const live = document.createElement('span');
  live.className = 'view-announcement';
  live.setAttribute('aria-live', 'polite');
  row.querySelector('td:last-child').append(live);
  views.forEach(link => {
    link.setAttribute('aria-label', `${name}: ${link.textContent} view`);
    if (link.href === preview.href) link.setAttribute('aria-current', 'true');
    link.addEventListener('click', event => {
      if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      image.src = link.href;
      image.style.setProperty('--canvas', link.dataset.canvas);
      image.alt = `${name}, ${link.textContent.toLowerCase()} view`;
      preview.href = link.href;
      views.forEach(other => other.removeAttribute('aria-current'));
      link.setAttribute('aria-current', 'true');
      live.textContent = `${name}: showing ${link.textContent.toLowerCase()} view`;
    });
  });
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
