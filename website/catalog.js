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

// A single play-through, then hold the finished frame. Reduced-motion visitors
// see the still poster until they choose to play. The control also supports pause.
const demo = document.querySelector('#insertion-demo');
const motionButton = document.querySelector('.motion-control');
if (demo && motionButton) {
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  let complete = false;
  let started = false;
  demo.controls = false;
  motionButton.hidden = false;
  const play = () => {
    started = true;
    if (complete) { demo.currentTime = 0; complete = false; }
    demo.play().then(() => { motionButton.textContent = 'Pause animation'; })
      .catch(() => { motionButton.textContent = 'Play animation'; });
  };
  demo.addEventListener('pause', () => {
    motionButton.textContent = complete ? 'Replay animation' : 'Play animation';
  });
  demo.addEventListener('timeupdate', () => {
    if (demo.currentTime >= 5.7) {
      complete = true;
      demo.pause();
      motionButton.textContent = 'Replay animation';
    }
  });
  motionButton.addEventListener('click', () => {
    if (demo.paused) play(); else demo.pause();
  });
  reduced.addEventListener('change', event => { if (event.matches) demo.pause(); });
  new IntersectionObserver(entries => {
    if (entries[0].isIntersecting) {
      if (!started && !reduced.matches) play();
    } else if (!demo.paused) demo.pause();
  }, {threshold: .25}).observe(demo);
}
