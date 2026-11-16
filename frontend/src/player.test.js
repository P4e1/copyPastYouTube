import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import {
  PLAYBACK_RATES,
  bufferedFraction,
  formatPlayerClock,
  formatPlayerTimeLabel,
  playerView,
  rateLabel,
  seekToRatio,
} from "./player.js";

test("player clock matches the YouTube control, without fractional seconds", () => {
  assert.equal(formatPlayerClock(0), "0:00");
  assert.equal(formatPlayerClock(5), "0:05");
  assert.equal(formatPlayerClock(65.9), "1:05");
  assert.equal(formatPlayerClock(2410), "40:10");
  assert.equal(formatPlayerClock(3981), "1:06:21");
});

test("player time button speaks the current time and the full length", () => {
  assert.equal(
    formatPlayerTimeLabel(2410, 3981),
    "40 мин. 10 сек. (общая длительность 1 ч. 6 мин. 21 сек.)",
  );
  assert.equal(formatPlayerTimeLabel(5, 0), "5 сек. (общая длительность 0 сек.)");
});

test("seek stays inside the video", () => {
  assert.equal(seekToRatio(0.5, 100), 50);
  assert.equal(seekToRatio(-1, 100), 0);
  assert.equal(seekToRatio(2, 100), 100);
  assert.equal(seekToRatio(0.25, 0), 0);
});

test("buffer fill is the end of the range under the playhead", () => {
  assert.equal(bufferedFraction([[0, 30]], 10, 100), 0.3);
  assert.equal(bufferedFraction([], 0, 100), 0);
  assert.equal(bufferedFraction([[0, 10]], 0, 0), 0);
});

test("settings list uses YouTube speeds and calls 1x ordinary", () => {
  assert.deepEqual(PLAYBACK_RATES, [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2]);
  assert.equal(rateLabel(1), "Обычная");
  assert.equal(rateLabel(1.25), "1,25");
});

test("wide screen fills the window and the ordinary screen keeps the side column", () => {
  assert.deepEqual(playerView(false), {
    frame: "half",
    watchClass: "watch",
    guide: "kept",
  });
  assert.deepEqual(playerView(true), {
    frame: "full",
    watchClass: "watch watch--theater",
    guide: "closed",
  });
});

test("full-window stage stretches across the watch column", () => {
  const css = readFileSync(new URL("./styles.css", import.meta.url), "utf8");
  const blocks = css.match(/\.watch\.watch--theater\s*\{[^}]*\}/g) || [];
  assert.ok(blocks.some((block) => /align-items:\s*stretch/.test(block)));
  assert.match(
    css,
    /\.watch\.watch--theater \.watch__left,\s*\.watch\.watch--theater \.watch__main\s*\{[^}]*width:\s*100%/,
  );
});

test("fullscreen fills the window when the browser blocks the fullscreen api", () => {
  const source = readFileSync(new URL("./components/Player.jsx", import.meta.url), "utf8");
  assert.match(source, /yt-player--window/);
  assert.match(source, /requestFullscreen\?\.\(\)[\s\S]*?\.catch\(/);
});

test("player reads settings before the speed state that uses them", () => {
  const source = readFileSync(new URL("./components/Player.jsx", import.meta.url), "utf8");
  const settingsAt = source.indexOf("useSettings()");
  const rateAt = source.indexOf("useState(settings.playbackRate)");
  assert.ok(settingsAt !== -1 && rateAt !== -1);
  assert.ok(settingsAt < rateAt);
});
