// Runs before the stylesheet so the saved theme applies on the first paint.
(() => {
  const storageKey = "parcelhub-theme";
  const system = window.matchMedia("(prefers-color-scheme: dark)");
  const normalize = (value) =>
    ["light", "dark"].includes(value) ? value : "system";
  const readPreference = () => {
    try {
      return normalize(localStorage.getItem(storageKey));
    } catch {
      return "system";
    }
  };
  let preference = readPreference();

  function apply() {
    const theme =
      preference === "system"
        ? system.matches
          ? "dark"
          : "light"
        : preference;
    document.documentElement.dataset.theme = theme;
    document
      .querySelector('meta[name="theme-color"]')
      ?.setAttribute("content", theme === "dark" ? "#0c1727" : "#f3f5f8");
    window.dispatchEvent(new Event("parcelhub:theme-change"));
  }

  window.ParcelHubTheme = {
    get preference() {
      return preference;
    },
    get current() {
      return document.documentElement.dataset.theme;
    },
    set(value) {
      preference = normalize(value);
      try {
        if (preference === "system") localStorage.removeItem(storageKey);
        else localStorage.setItem(storageKey, preference);
      } catch {
        // The toggle still works for this page when storage is unavailable.
      }
      apply();
    },
  };
  system.addEventListener("change", () => {
    if (preference === "system") apply();
  });
  window.addEventListener("storage", (event) => {
    if (event.key === storageKey || event.key === null) {
      preference = readPreference();
      apply();
    }
  });
  apply();
})();
