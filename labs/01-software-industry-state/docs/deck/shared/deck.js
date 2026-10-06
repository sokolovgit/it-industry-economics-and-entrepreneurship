(() => {
  const slides = [...document.querySelectorAll('.slide')];
  const body = document.body;
  let i = 0;

  slides.forEach((s, n) => {
    const num = s.querySelector('.slide__num');
    if (num && !num.textContent.trim()) num.textContent = String(n + 1).padStart(2, '0');
  });

  // Fit the fixed 1280x720 slide into the viewport.
  const fit = () => {
    if (body.classList.contains('show-all')) return;
    const k = Math.min(innerWidth / 1280, innerHeight / 720) * 0.92;
    slides.forEach(s => (s.style.transform = `scale(${k})`));
  };

  const show = n => {
    i = Math.max(0, Math.min(slides.length - 1, n));
    slides.forEach((s, k) => s.classList.toggle('is-active', k === i));
    location.hash = i + 1;
  };

  addEventListener('keydown', e => {
    const k = e.key;
    if (k === 'ArrowRight' || k === 'ArrowDown' || k === ' ' || k === 'PageDown') { e.preventDefault(); show(i + 1); }
    else if (k === 'ArrowLeft' || k === 'ArrowUp' || k === 'PageUp') { e.preventDefault(); show(i - 1); }
    else if (k === 'Home') show(0);
    else if (k === 'End') show(slides.length - 1);
    else if (k === 'f') document.documentElement.requestFullscreen?.();
    else if (k === 'a') { body.classList.toggle('show-all'); fit(); }
  });

  addEventListener('resize', fit);

  if (location.search.includes('all')) body.classList.add('show-all');
  fit();
  show(parseInt(location.hash.slice(1), 10) - 1 || 0);
})();
