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

  const nativeScrollProgress = CSS.supports('animation-timeline: scroll()');

  if (progress && !nativeScrollProgress) {
    let scrollable = 0;
    const updateProgress = () => {
      const value = scrollable > 0 ? window.scrollY / scrollable : 0;
      progress.style.transform = `scaleX(${Math.min(1, Math.max(0, value))})`;
    };
    const measureProgress = () => {
      scrollable = document.documentElement.scrollHeight - window.innerHeight;
      updateProgress();
    };
    window.addEventListener('scroll', updateProgress, { passive: true });
    window.addEventListener('resize', measureProgress, { passive: true });
    document.querySelectorAll('.work-case').forEach((item) => {
      item.addEventListener('toggle', () => requestAnimationFrame(measureProgress));
    });
    requestAnimationFrame(measureProgress);
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

  const navs = [...document.querySelectorAll('.entrances')].filter((nav) =>
    nav.querySelector('.entrance-indicator')
  );
  navs.forEach((nav) => nav.classList.add('has-indicator'));

  function moveIndicator(nav) {
    const indicator = nav.querySelector('.entrance-indicator');
    const active = nav.querySelector('a.is-active');
    if (!active) {
      indicator.style.opacity = '0';
      return;
    }
    const item = active.parentElement;
    indicator.style.width = `${item.offsetWidth}px`;
    indicator.style.height = `${item.offsetHeight}px`;
    indicator.style.transform = `translate(${item.offsetLeft}px, ${item.offsetTop}px)`;
    indicator.style.opacity = '1';
  }

  function moveIndicators() {
    navs.forEach(moveIndicator);
  }

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
      moveIndicators();
    },
    { rootMargin: '-20% 0px -65% 0px' }
  );
  sections.forEach((section) => sectionObserver.observe(section));

  navLinks.forEach((link) => {
    link.addEventListener('click', () => {
      const target = link.getAttribute('href');
      navLinks.forEach((other) => {
        const active = other.getAttribute('href') === target;
        other.classList.toggle('is-active', active);
        if (active) other.setAttribute('aria-current', 'location');
        else other.removeAttribute('aria-current');
      });
      moveIndicators();
    });
  });

  // 관찰자가 처음 반응하기 전에도 표시가 보이도록, 주소의 앵커나 첫 항목을 켜 둔다.
  if (navLinks.length && !navLinks.some((link) => link.classList.contains('is-active'))) {
    const fromHash = navLinks.find((link) => link.getAttribute('href') === window.location.hash);
    const target = (fromHash || navLinks[0]).getAttribute('href');
    navLinks.forEach((link) => link.classList.toggle('is-active', link.getAttribute('href') === target));
  }

  // 글꼴 적용이나 폭 변화로 목록 크기가 달라지면 표시도 다시 맞춘다.
  let resizeFrame = 0;
  window.addEventListener('resize', () => {
    cancelAnimationFrame(resizeFrame);
    resizeFrame = requestAnimationFrame(moveIndicators);
  });
  if ('ResizeObserver' in window) {
    const listObserver = new ResizeObserver(() => moveIndicators());
    navs.forEach((nav) => listObserver.observe(nav.querySelector('ol')));
  }
  moveIndicators();

  requestAnimationFrame(() => document.body.classList.add('is-ready'));
})();
