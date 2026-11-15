import assert from "node:assert/strict";
import test from "node:test";

import { formatAgo, formatCompact, formatSubscribers, formatVideoCount, formatViews } from "./format.js";

const now = Date.parse("2026-11-15T15:00:00Z");

test("formatViews groups thousands and keeps the Russian plural", () => {
  assert.equal(formatViews(9747).replace(/\s/g, " "), "9 747 просмотров");
  assert.equal(formatViews(1), "1 просмотр");
  assert.equal(formatViews(2), "2 просмотра");
});

test("formatCompact uses YouTube-style units", () => {
  assert.equal(formatCompact(490), "490");
  assert.equal(formatCompact(1500), "1,5 тыс.");
  assert.equal(formatCompact(624000), "624 тыс.");
  assert.equal(formatCompact(8500000), "8,5 млн");
});

test("formatSubscribers abbreviates large counts", () => {
  assert.equal(formatSubscribers(1), "1 подписчик");
  assert.equal(formatSubscribers(297000), "297 тыс. подписчиков");
});

test("formatVideoCount matches the channel header line", () => {
  assert.equal(formatVideoCount(1), "1 видео");
  assert.equal(formatVideoCount(12), "12 видео");
  assert.equal(formatVideoCount(1500), "1,5 тыс. видео");
});

test("formatAgo matches the watch-page wording", () => {
  assert.equal(formatAgo("2026-11-15T14:59:30Z", now), "только что");
  assert.equal(formatAgo("2026-11-15T14:30:00Z", now), "30 мин. назад");
  assert.equal(formatAgo("2026-11-15T13:00:00Z", now), "2 ч назад");
  assert.equal(formatAgo("2026-11-03T15:00:00Z", now), "12 дн. назад");
  assert.equal(formatAgo("2024-11-15T15:00:00Z", now), "2 г. назад");
});
