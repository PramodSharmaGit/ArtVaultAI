(() => {
  const video = document.querySelector('.hero-video');
  const button = document.querySelector('.hero-video-toggle');
  if (!video || !button) return;
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const connection = navigator.connection;
  let visible = true;
  let pausedByUser = false;
  const allowed = () => !reducedMotion.matches && !connection?.saveData && !['slow-2g', '2g'].includes(connection?.effectiveType);
  const play = () => {
    if (!video.src || !allowed() || !visible || document.hidden || pausedByUser) return;
    video.play().catch(() => { button.hidden = true; });
  };
  video.addEventListener('playing', () => {
    video.classList.add('is-playing');
    button.hidden = false;
    button.classList.remove('is-paused');
    button.setAttribute('aria-label', 'Pause video');
    button.title = 'Pause video';
  });
  video.addEventListener('error', () => {
    video.classList.remove('is-playing');
    button.hidden = true;
  });
  // Fade to the opening still before restarting, hiding the cut between scenes.
  video.addEventListener('timeupdate', () => {
    if (video.duration - video.currentTime < .7) video.classList.remove('is-playing');
  });
  video.addEventListener('ended', () => { video.currentTime = 0; play(); });
  button.addEventListener('click', () => {
    pausedByUser = !pausedByUser;
    if (pausedByUser) {
      video.pause();
      button.classList.add('is-paused');
      button.setAttribute('aria-label', 'Play video');
      button.title = 'Play video';
    } else play();
  });
  const preferenceChanged = () => {
    if (!allowed()) {
      video.pause();
      video.removeAttribute('src');
      video.load();
      video.classList.remove('is-playing');
      button.hidden = true;
    } else start();
  };
  const start = () => {
    if (!allowed()) return;
    if (!video.src) { video.src = video.dataset.src; video.load(); }
    play();
  };
  reducedMotion.addEventListener('change', preferenceChanged);
  connection?.addEventListener('change', preferenceChanged);
  document.addEventListener('visibilitychange', () => { if (document.hidden) video.pause(); else play(); });
  new IntersectionObserver(([entry]) => {
    visible = entry.isIntersecting;
    if (!visible) video.pause(); else play();
  }).observe(video);
  // No video URL is assigned until the page has loaded and the browser has idle time.
  const schedule = () => {
    if ('requestIdleCallback' in window) window.requestIdleCallback(start, { timeout: 2500 });
    else window.setTimeout(start, 500);
  };
  if (document.readyState === 'complete') schedule();
  else window.addEventListener('load', schedule, { once: true });
})();
