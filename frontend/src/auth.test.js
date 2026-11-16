import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

test("authorization page sits on an empty background", () => {
  const css = readFileSync(new URL("./styles.css", import.meta.url), "utf8");
  const auth = css.match(/\.auth\s*\{[^}]*\}/)[0];
  const card = css.match(/\.auth__card\s*\{[^}]*\}/)[0];
  assert.match(auth, /background:\s*var\(--bg\)/);
  assert.doesNotMatch(auth, /url\(/);
  assert.match(card, /background:\s*transparent/);
  assert.match(card, /box-shadow:\s*none/);
  assert.match(card, /border:\s*0/);
});
