import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { progressPhase } from "./progress.js";

test("the header runs a red bar while a page opens", () => {
  assert.equal(progressPhase(true), "run");
  assert.equal(progressPhase(false), "idle");
  const css = readFileSync(new URL("./styles.css", import.meta.url), "utf8");
  const bar = css.match(/\.top-progress\s*\{[^}]*\}/)[0];
  assert.match(bar, /background:\s*#ff0000/);
  assert.match(bar, /height:\s*3px/);
  assert.match(css, /@keyframes top-progress/);
});
