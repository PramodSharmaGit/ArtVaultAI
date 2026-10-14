// Close the profile menu on outside click or Escape.
(() => {
  const menu = document.querySelector('.profile');
  if (!menu) return;
  document.addEventListener('click', (e) => { if (!menu.contains(e.target)) menu.open = false; });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && menu.open) { menu.open = false; menu.querySelector('summary').focus(); }
  });
})();
