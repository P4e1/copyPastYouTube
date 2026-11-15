import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { readSettings, resolveTheme, writeSettings } from "./settings";

const SettingsContext = createContext(null);
const DARK = "(prefers-color-scheme: dark)";

export function SettingsProvider({ children }) {
  const [settings, setSettings] = useState(() => readSettings(localStorage));
  const [prefersDark, setPrefersDark] = useState(() => window.matchMedia(DARK).matches);

  useEffect(() => {
    const query = window.matchMedia(DARK);
    const onChange = (event) => setPrefersDark(event.matches);
    query.addEventListener("change", onChange);
    return () => query.removeEventListener("change", onChange);
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = resolveTheme(settings.theme, prefersDark);
  }, [settings.theme, prefersDark]);

  const value = useMemo(
    () => ({
      settings,
      updateSettings(patch) {
        setSettings((current) => writeSettings(localStorage, { ...current, ...patch }));
      },
    }),
    [settings],
  );

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
}

export function useSettings() {
  const value = useContext(SettingsContext);
  if (value === null) {
    throw new Error("Настройки не подключены");
  }
  return value;
}
