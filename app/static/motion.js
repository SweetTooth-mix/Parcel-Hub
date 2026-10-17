// Progressive enhancement: content is visible even without animation support.
(() => {
  const preference = window.matchMedia("(prefers-reduced-motion: reduce)");
  const seen = new WeakSet();
  const pending = new Map();
  const running = new Set();
  let quiet = 0;
  const ease = "cubic-bezier(0.22, 1, 0.36, 1)";
  const sections = [
    ".page-head",
    ".stat",
    ".hero",
    ".panel",
    ".order-start",
    ".task-banner",
    ".section-head",
    ".info-note",
    ".help-step",
    ".about-card",
    ".notification",
    ".story-copy",
    ".auth-story > .scene",
    ".story-footer",
    ".auth-form-side > .eyebrow",
    ".auth-form-side > h2",
    ".auth-form-side > p",
    ".auth-form-side > form",
    ".auth-switch",
    ".demo-accounts",
    ".auth-form-side > .button",
    ".modal-body",
    ".kiosk-card > h2",
    ".kiosk-success",
  ].join(",");
  const titles =
    ".page-head h1, .story-copy h1, .hero-copy h2, .order-start h2, .auth-form-side > h2, .kiosk-card > h2";

  function animate(element, frames, options = {}) {
    if (preference.matches || quiet || !element.animate) return null;
    const animation = element.animate(frames, {
      duration: 520,
      easing: ease,
      fill: "backwards",
      ...options,
    });
    running.add(animation);
    // No forwards fill: after finishing/cancelling, normal styles take over.
    animation.finished.then(
      () => running.delete(animation),
      () => running.delete(animation),
    );
    return animation;
  }

  function textEntrance(title) {
    if (title.querySelector(".motion-word")) return;
    const walker = document.createTreeWalker(title, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    let index = 0;
    for (const node of nodes) {
      const fragment = document.createDocumentFragment();
      for (const part of node.textContent.split(/(\s+)/)) {
        if (!part) continue;
        if (/^\s+$/.test(part)) {
          fragment.append(document.createTextNode(part));
          continue;
        }
        const word = document.createElement("span");
        word.className = "motion-word";
        word.textContent = part;
        fragment.append(word);
      }
      node.replaceWith(fragment);
    }
    // Preserve the original text, emphasis and line breaks for assistive tech.
    for (const word of title.querySelectorAll(".motion-word")) {
      animate(
        word,
        [
          { opacity: 0, transform: "translateY(10px)" },
          { opacity: 1, transform: "translateY(0)" },
        ],
        { duration: 440, delay: Math.min(index++ * 35, 175) },
      );
    }
  }

  function enter(element, delay = 0) {
    if (!element.isConnected || preference.matches || quiet) return;
    // Keyboard users should never wait for a focused control to become visible.
    if (element.contains(document.activeElement)) return;
    const heading = element.matches(titles);
    if (!heading)
      animate(
        element,
        [
          { opacity: 0, transform: "translateY(16px)" },
          { opacity: 1, transform: "translateY(0)" },
        ],
        { delay },
      );
    for (const title of heading ? [element] : element.querySelectorAll(titles))
      textEntrance(title);
    for (const bar of element.querySelectorAll(".chart-bar")) {
      animate(
        bar,
        [{ transform: "scaleY(0.05)" }, { transform: "scaleY(1)" }],
        { duration: 650, delay },
      );
    }
  }

  const observer =
    typeof IntersectionObserver === "function"
      ? new IntersectionObserver(
          (entries) => {
            for (const entry of entries) {
              if (!entry.isIntersecting || !pending.has(entry.target)) continue;
              const delay = pending.get(entry.target) || 0;
              pending.delete(entry.target);
              observer.unobserve(entry.target);
              enter(entry.target, delay);
            }
          },
          { threshold: 0.06 },
        )
      : null;

  function reveal(root = document) {
    // Retire observers for cards removed by navigation/search/refresh.
    for (const element of pending.keys()) {
      if (!element.isConnected) {
        observer?.unobserve(element);
        pending.delete(element);
      }
    }
    const candidates = [...root.querySelectorAll(sections)].filter(
      (element) => !seen.has(element),
    );
    if (root.matches?.(sections) && !seen.has(root)) candidates.unshift(root);
    let index = 0;
    for (const element of candidates) {
      if (seen.has(element)) continue;
      seen.add(element);
      // Animate the containing card, not every nested section independently.
      if (
        candidates.some(
          (parent) => parent !== element && parent.contains(element),
        )
      )
        continue;
      if (preference.matches || quiet || !element.animate) continue;
      const delay = Math.min(index++ * 45, 180);
      if (observer) {
        pending.set(element, delay);
        observer.observe(element);
      } else enter(element, delay);
    }
  }

  function withoutEntrance(callback) {
    quiet++;
    try {
      return callback();
    } finally {
      quiet--;
    }
  }

  function busy(button) {
    if (!button) return () => {};
    const previous = button.getAttribute("aria-busy");
    button.setAttribute("aria-busy", "true");
    // Avoid flashing a spinner for instantaneous interactions.
    const timer = setTimeout(() => {
      if (button.isConnected) button.classList.add("is-loading");
    }, 160);
    return () => {
      clearTimeout(timer);
      button.classList.remove("is-loading");
      if (previous === null) button.removeAttribute("aria-busy");
      else button.setAttribute("aria-busy", previous);
    };
  }

  document.addEventListener("click", (event) => {
    const control = event.target.closest?.("button, a.button");
    if (!control || control.disabled || preference.matches || !control.animate)
      return;
    const rect = control.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    control.classList.add("has-ripple");
    const ripple = document.createElement("span");
    ripple.className = "click-ripple";
    ripple.setAttribute("aria-hidden", "true");
    const size = Math.max(rect.width, rect.height) * 2;
    const x = event.detail ? event.clientX - rect.left : rect.width / 2;
    const y = event.detail ? event.clientY - rect.top : rect.height / 2;
    ripple.style.width = ripple.style.height = `${size}px`;
    ripple.style.left = `${x - size / 2}px`;
    ripple.style.top = `${y - size / 2}px`;
    control.append(ripple);
    const animation = animate(
      ripple,
      [
        { transform: "scale(0)", opacity: 0.18 },
        { transform: "scale(1)", opacity: 0 },
      ],
      { duration: 460, easing: "ease-out" },
    );
    if (animation)
      animation.finished.then(
        () => ripple.remove(),
        () => ripple.remove(),
      );
    else ripple.remove();
  });

  document.addEventListener("focusin", (event) => {
    for (const animation of running) {
      const target = animation.effect?.target;
      if (target?.contains(event.target)) animation.cancel();
    }
  });

  preference.addEventListener("change", () => {
    if (!preference.matches) return;
    observer?.disconnect();
    pending.clear();
    for (const animation of running) animation.cancel();
    running.clear();
  });
  window.addEventListener("beforeunload", () => {
    observer?.disconnect();
    pending.clear();
    for (const animation of running) animation.cancel();
  });
  window.ParcelHubMotion = { reveal, withoutEntrance, busy };
})();
