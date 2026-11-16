import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

test("authorization form is a window on an empty page", () => {
  const css = readFileSync(new URL("./styles.css", import.meta.url), "utf8");
  const auth = css.match(/\.auth\s*\{[^}]*\}/)[0];
  const card = css.match(/\.auth__card\s*\{[^}]*\}/)[0];
  assert.match(auth, /background:\s*var\(--bg\)/);
  assert.doesNotMatch(auth, /url\(/);
  assert.match(card, /border:\s*1px solid var\(--line\)/);
  assert.match(card, /background:\s*var\(--bg\)/);
  assert.match(card, /box-shadow:\s*none/);
  assert.doesNotMatch(card, /url\(/);
});
