import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { countdownLeft, END_COUNTDOWN_SECONDS, endScreen } from "./endscreen.js";

test("the end of a video stays on the player", () => {
  assert.equal(endScreen({ ended: false, autoplay: true, hasNext: true }), "hidden");
  assert.equal(endScreen({ ended: true, autoplay: false, hasNext: true }), "replay");
  assert.equal(endScreen({ ended: true, autoplay: true, hasNext: false }), "replay");
  assert.equal(endScreen({ ended: true, autoplay: true, hasNext: true }), "countdown");
  assert.equal(END_COUNTDOWN_SECONDS, 8);
  assert.equal(countdownLeft(8, 0), 8);
  assert.equal(countdownLeft(8, 7.1), 1);
  assert.equal(countdownLeft(8, 8), 0);
});

test("player does not open the next video at the first ended event", () => {
  const player = readFileSync(new URL("./components/Player.jsx", import.meta.url), "utf8");
  const watch = readFileSync(new URL("./pages/WatchPage.jsx", import.meta.url), "utf8");
  assert.match(player, /endScreen\(/);
  assert.match(player, /Повторить/);
  assert.match(player, /Отмена/);
  assert.match(watch, /upNext=/);
  assert.doesNotMatch(player, /onEnded\(\) \{\s*setPlaying\(false\);\s*setChrome\(true\);\s*if \(autoplay\)/);
});
