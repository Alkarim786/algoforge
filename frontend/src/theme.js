import { useEffect, useState } from "react";

const QUERY = "(prefers-color-scheme: dark)";
const STORAGE_KEY = "algoforge-theme";
const EVENT = "algoforge-theme-change";

/** "light", "dark", or "system" (follow the operating system). */
export function getThemeChoice() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored === "light" || stored === "dark" ? stored : "system";
  } catch {
    return "system";
  }
}

function isDark(choice = getThemeChoice()) {
  return choice === "dark" || (choice === "system" && window.matchMedia(QUERY).matches);
}

/** Puts the effective theme on <html data-theme>, which the stylesheet keys off. index.html does the same before
 * the first paint, so there's no flash of the wrong theme. */
export function applyTheme() {
  const dark = isDark();
  document.documentElement.dataset.theme = dark ? "dark" : "light";
  document.documentElement.style.colorScheme = dark ? "dark" : "light";
}

export function setThemeChoice(choice) {
  try {
    if (choice === "system") localStorage.removeItem(STORAGE_KEY);
    else localStorage.setItem(STORAGE_KEY, choice);
  } catch {
    // Storage can be blocked; the choice then lasts until the page reloads.
  }
  applyTheme();
  window.dispatchEvent(new Event(EVENT));
}

/** The chosen theme and whether the page is currently dark. Re-renders on a change from any component, or when the
 * operating system switches while the choice is "system". */
export function useTheme() {
  const [state, setState] = useState(() => ({ choice: getThemeChoice(), dark: isDark() }));
  useEffect(() => {
    const media = window.matchMedia(QUERY);
    const update = () => {
      applyTheme();
      setState({ choice: getThemeChoice(), dark: isDark() });
    };
    media.addEventListener("change", update);
    window.addEventListener(EVENT, update);
    return () => {
      media.removeEventListener("change", update);
      window.removeEventListener(EVENT, update);
    };
  }, []);
  return state;
}

/** Whether the page is dark, for components that theme themselves (Monaco, Mermaid). */
export function usePrefersDark() {
  return useTheme().dark;
}
