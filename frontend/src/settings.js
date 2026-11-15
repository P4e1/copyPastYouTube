export const SETTINGS_KEY = "cpy-settings";

export const DEFAULT_SETTINGS = {
  theme: "device",
  restricted: false,
  autoplayNext: false,
};

export const THEME_OPTIONS = [
  { id: "device", label: "Как на устройстве" },
  { id: "light", label: "Светлая тема" },
  { id: "dark", label: "Тёмная тема" },
];

export const SETTINGS_NAV = [
  { id: "account", label: "Аккаунт", to: "/account" },
  { id: "time", label: "Тайм-менеджмент", to: "/account/time" },
  { id: "notifications", label: "Уведомления", to: "/account/notifications" },
  { id: "playback", label: "Воспроизведение", to: "/account/playback" },
  { id: "privacy", label: "Конфиденциальность", to: "/account/privacy" },
  { id: "apps", label: "Связанные приложения", to: "/account/apps" },
  { id: "billing", label: "Расчеты и платежи", to: "/account/billing" },
  { id: "advanced", label: "Расширенные настройки", to: "/account/advanced" },
];

export const SHORTCUTS = [
  ["k или пробел", "пауза и воспроизведение"],
  ["m", "звук"],
  ["f", "полный экран"],
  ["t", "широкий экран"],
  ["← / →", "перемотка на 5 секунд"],
  ["↑ / ↓", "громкость"],
];

export function resolveTheme(theme, prefersDark) {
  if (theme === "dark") {
    return "dark";
  }
  if (theme === "light") {
    return "light";
  }
  if (theme === "device") {
    return prefersDark ? "dark" : "light";
  }
  return "light";
}

export function themeLabel(theme) {
  const found = THEME_OPTIONS.find((item) => item.id === theme);
  return (found || THEME_OPTIONS[0]).label.toLowerCase();
}

export function normalizeSettings(raw) {
  const source = raw && typeof raw === "object" ? raw : {};
  const theme = THEME_OPTIONS.some((item) => item.id === source.theme) ? source.theme : "device";
  return {
    theme,
    restricted: Boolean(source.restricted),
    autoplayNext: Boolean(source.autoplayNext),
  };
}

export function readSettings(storage) {
  try {
    return normalizeSettings(JSON.parse(storage.getItem(SETTINGS_KEY) || "null"));
  } catch {
    return { ...DEFAULT_SETTINGS };
  }
}

export function writeSettings(storage, next) {
  const value = normalizeSettings(next);
  storage.setItem(SETTINGS_KEY, JSON.stringify(value));
  return value;
}

export function headerChrome({ narrow, searchOpen }) {
  return {
    showSearchForm: !narrow || searchOpen,
    showSearchButton: narrow && !searchOpen,
  };
}

export function voiceQueryPath(transcript) {
  const query = String(transcript || "").trim();
  if (!query) {
    return null;
  }
  return `/search?q=${encodeURIComponent(query)}`;
}
