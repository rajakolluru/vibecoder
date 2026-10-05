(() => {
  document.documentElement.classList.remove('no-js');

  const chips = document.querySelectorAll('[data-filter]');
  const items = document.querySelectorAll('.archive-list .gotcha');
  const empty = document.querySelector('.archive-empty');
  chips.forEach((chip) => chip.addEventListener('click', () => {
    const f = chip.dataset.filter;
    chips.forEach((c) => c.setAttribute('aria-pressed', String(c === chip)));
    let shown = 0;
    items.forEach((it) => {
      const ok = f === 'all' || it.dataset.audience === f;
      it.hidden = !ok;
      if (ok) shown++;
    });
    if (empty) empty.hidden = shown !== 0;
  }));

  document.querySelectorAll('button.copy').forEach((b) => b.addEventListener('click', async () => {
    const url = b.dataset.url;
    try {
      await navigator.clipboard.writeText(url);
      b.textContent = 'Copied';
    } catch {
      window.prompt('Copy this link', url);
    }
    setTimeout(() => { b.textContent = 'Copy link'; }, 1600);
  }));
})();
