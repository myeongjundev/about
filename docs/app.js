(() => {
  const root = document.documentElement;
  const progress = document.querySelector('.scroll-progress span');
  const themeButton = document.querySelector('.theme-toggle');
  const themeLabel = document.querySelector('.theme-label');
  const profileCard = document.querySelector('.side');
  const craftButtons = [...document.querySelectorAll('[data-craft]')];
  const craftCaption = document.querySelector('.craft-caption');
  const craftOutput = document.querySelector('.craft-output');
  const navLinks = [...document.querySelectorAll('.entrances a')];
  const sections = navLinks
    .map((link) => document.querySelector(link.getAttribute('href')))
    .filter(Boolean);

  const savedTheme = localStorage.getItem('portfolio-theme');
  const preferredDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

  function setTheme(theme) {
    root.dataset.theme = theme;
    const isDark = theme === 'dark';
    if (themeButton) themeButton.setAttribute('aria-pressed', String(isDark));
    if (themeLabel) themeLabel.textContent = isDark ? 'Light mode' : 'Dark mode';
    document.querySelector('meta[name="theme-color"]')?.setAttribute(
      'content',
      isDark ? '#0b1020' : '#f4f6fb'
    );
  }

  setTheme(savedTheme || (preferredDark ? 'dark' : 'light'));
  themeButton?.addEventListener('click', () => {
    const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    localStorage.setItem('portfolio-theme', next);
  });

  function selectCraft(button) {
    craftButtons.forEach((item) => item.setAttribute('aria-pressed', String(item === button)));
    if (craftCaption) craftCaption.textContent = button.dataset.copy || '';
    if (craftOutput) craftOutput.value = `${button.dataset.index} / ${button.textContent.trim().replace(/^\d+/, '')}`;
  }

  craftButtons.forEach((button, index) => {
    button.addEventListener('click', () => selectCraft(button));
    button.addEventListener('keydown', (event) => {
      if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
      event.preventDefault();
      let nextIndex = index;
      if (event.key === 'ArrowLeft') nextIndex = (index - 1 + craftButtons.length) % craftButtons.length;
      if (event.key === 'ArrowRight') nextIndex = (index + 1) % craftButtons.length;
      if (event.key === 'Home') nextIndex = 0;
      if (event.key === 'End') nextIndex = craftButtons.length - 1;
      craftButtons[nextIndex].focus();
      selectCraft(craftButtons[nextIndex]);
    });
  });

  if (profileCard && window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
    let pointerFrame = 0;
    let profileRect = null;
    profileCard.addEventListener('pointerenter', () => {
      profileRect = profileCard.getBoundingClientRect();
    });
    profileCard.addEventListener('pointermove', (event) => {
      if (!profileRect) profileRect = profileCard.getBoundingClientRect();
      const pointerX = event.clientX - profileRect.left;
      const pointerY = event.clientY - profileRect.top;
      cancelAnimationFrame(pointerFrame);
      pointerFrame = requestAnimationFrame(() => {
        profileCard.style.setProperty('--pointer-x', `${pointerX}px`);
        profileCard.style.setProperty('--pointer-y', `${pointerY}px`);
        profileCard.classList.add('is-pointer-active');
      });
    });
    profileCard.addEventListener('pointerleave', () => {
      cancelAnimationFrame(pointerFrame);
      profileRect = null;
      profileCard.classList.remove('is-pointer-active');
    });
    window.addEventListener('scroll', () => { profileRect = null; }, { passive: true });
  }

  let scrollable = 0;

  function updateProgress() {
    const value = scrollable > 0 ? window.scrollY / scrollable : 0;
    if (progress) progress.style.transform = `scaleX(${Math.min(1, Math.max(0, value))})`;
  }

  function measureProgress() {
    scrollable = document.documentElement.scrollHeight - window.innerHeight;
    updateProgress();
  }

  const revealObserver = new IntersectionObserver(
    (entries) => entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        revealObserver.unobserve(entry.target);
      }
    }),
    { rootMargin: '0px 0px -8% 0px', threshold: 0.08 }
  );
  document.querySelectorAll('.reveal').forEach((item) => revealObserver.observe(item));

  const sectionObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        navLinks.forEach((link) => {
          const active = link.getAttribute('href') === `#${entry.target.id}`;
          link.classList.toggle('is-active', active);
          if (active) link.setAttribute('aria-current', 'location');
          else link.removeAttribute('aria-current');
        });
      });
    },
    { rootMargin: '-20% 0px -65% 0px' }
  );
  sections.forEach((section) => sectionObserver.observe(section));

  window.addEventListener('scroll', updateProgress, { passive: true });
  window.addEventListener('resize', measureProgress, { passive: true });
  document.querySelectorAll('.work-case').forEach((item) => {
    item.addEventListener('toggle', () => requestAnimationFrame(measureProgress));
  });
  requestAnimationFrame(() => {
    measureProgress();
    document.body.classList.add('is-ready');
  });
})();
