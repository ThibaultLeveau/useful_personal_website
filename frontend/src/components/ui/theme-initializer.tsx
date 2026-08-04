const themeInitializer = `(() => {
  try {
    const preference = localStorage.getItem("upw-theme") || "system";
    const resolved = preference === "system"
      ? (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")
      : preference;
    document.documentElement.dataset.theme = resolved;
    document.documentElement.dataset.themePreference = preference;
    document.documentElement.style.colorScheme = resolved;
  } catch {
    document.documentElement.dataset.theme = "light";
    document.documentElement.dataset.themePreference = "system";
    document.documentElement.style.colorScheme = "light";
  }
})();`;

export function ThemeInitializer() {
  return <script id="theme-initializer" dangerouslySetInnerHTML={{ __html: themeInitializer }} />;
}
