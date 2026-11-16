import assert from "node:assert/strict";
import test from "node:test";

import {
  DEFAULT_SETTINGS,
  SETTINGS_NAV,
  breakDue,
  headerChrome,
  normalizeSettings,
  readSettings,
  resolveTheme,
  roleLabel,
  subscriptionNotices,
  themeLabel,
  voiceQueryPath,
  writeSettings,
} from "./settings.js";

test("theme follows the device until the account menu picks light or dark", () => {
  assert.equal(resolveTheme("device", false), "light");
  assert.equal(resolveTheme("device", true), "dark");
  assert.equal(resolveTheme("dark", false), "dark");
  assert.equal(resolveTheme("light", true), "light");
  assert.equal(resolveTheme("other", true), "light");
});

test("theme labels match the YouTube account menu", () => {
  assert.equal(themeLabel("device"), "как на устройстве");
  assert.equal(themeLabel("light"), "светлая тема");
  assert.equal(themeLabel("dark"), "тёмная тема");
});

test("settings stay in this browser and drop unknown values", () => {
  const storage = memoryStorage();
  assert.deepEqual(readSettings(storage), DEFAULT_SETTINGS);
  writeSettings(storage, {
    theme: "dark",
    restricted: true,
    autoplayNext: true,
    playbackRate: 1.5,
    breakMinutes: 30,
    notifySubscriptions: false,
    saveViews: false,
    extra: 1,
  });
  assert.deepEqual(readSettings(storage), {
    theme: "dark",
    restricted: true,
    autoplayNext: true,
    playbackRate: 1.5,
    breakMinutes: 30,
    notifySubscriptions: false,
    saveViews: false,
  });
  storage.setItem("cpy-settings", "{");
  assert.deepEqual(readSettings(storage), DEFAULT_SETTINGS);
  assert.deepEqual(normalizeSettings({ theme: "blue", restricted: "yes", playbackRate: 9, breakMinutes: 7 }), {
    theme: "device",
    restricted: true,
    autoplayNext: false,
    playbackRate: 1,
    breakMinutes: 0,
    notifySubscriptions: true,
    saveViews: true,
  });
});

test("break reminder and subscription notices follow the settings", () => {
  assert.equal(breakDue(0, 3600), false);
  assert.equal(breakDue(15, 14 * 60), false);
  assert.equal(breakDue(15, 15 * 60), true);
  assert.equal(roleLabel("admin"), "Администратор");
  assert.equal(roleLabel("moderator"), "Модератор");
  assert.equal(roleLabel("user"), "Пользователь");
  const feed = [
    { id: "1", title: "Утро", channel_name: "author-one" },
    { id: "2", title: "Сосед", channel_name: "author-two" },
  ];
  assert.deepEqual(subscriptionNotices(feed, ["author-one"], true), [feed[0]]);
  assert.deepEqual(subscriptionNotices(feed, ["author-one"], false), []);
});

test("settings page lists the same sections as YouTube", () => {
  assert.deepEqual(
    SETTINGS_NAV.map((item) => item.label),
    [
      "Аккаунт",
      "Тайм-менеджмент",
      "Уведомления",
      "Воспроизведение",
      "Конфиденциальность",
      "Связанные приложения",
      "Расчеты и платежи",
      "Расширенные настройки",
    ],
  );
  assert.equal(SETTINGS_NAV[0].to, "/account");
  assert.equal(SETTINGS_NAV[3].to, "/account/playback");
});

test("narrow header keeps a search button until the field is open", () => {
  assert.deepEqual(headerChrome({ narrow: false, searchOpen: false }), {
    showSearchForm: true,
    showSearchButton: false,
  });
  assert.deepEqual(headerChrome({ narrow: true, searchOpen: false }), {
    showSearchForm: false,
    showSearchButton: true,
  });
  assert.deepEqual(headerChrome({ narrow: true, searchOpen: true }), {
    showSearchForm: true,
    showSearchButton: false,
  });
});

test("voice search opens the results for the spoken query", () => {
  assert.equal(voiceQueryPath("  утро на канале "), "/search?q=%D1%83%D1%82%D1%80%D0%BE%20%D0%BD%D0%B0%20%D0%BA%D0%B0%D0%BD%D0%B0%D0%BB%D0%B5");
  assert.equal(voiceQueryPath("   "), null);
});

function memoryStorage() {
  const data = new Map();
  return {
    getItem(key) {
      return data.has(key) ? data.get(key) : null;
    },
    setItem(key, value) {
      data.set(key, String(value));
    },
  };
}
